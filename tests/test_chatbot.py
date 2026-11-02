"""Unit and integration tests for the enhanced AI Chatbot (P1 & P2).

Tests cover:
1. Unlabeled contact extraction (name, phone, address).
2. Natural Vietnamese quantity parsing ('2c', '2 cái', 'chốt 2'...).
3. Intent recognition and slot filling.
4. Multi-turn pending state preservation (no quantity loss, no variant loss).
5. Cancellation / pivot during pending order.
6. Single-turn unlabeled complete orders.
"""
from __future__ import annotations

import os
import tempfile
import unittest
from pathlib import Path
from uuid import uuid4

# Set up isolated SQLite database before importing app
TMP_DB = Path(tempfile.gettempdir()) / f"chatbot-test-{uuid4().hex}.db"
os.environ["DATABASE_URL"] = f"sqlite:///{TMP_DB.as_posix()}"
os.environ["LLM_PROVIDER"] = "fake"

from fastapi.testclient import TestClient

from backend.app.chat_engine import (
    extract_contact_info,
    extract_quantity,
    extract_cancellation,
    normalize_text,
)
from backend.app.seed import initialize_database
from backend.app import main
from backend.app.db import engine


class TestChatbotExtraction(unittest.TestCase):
    """Kiểm tra các hàm bóc tách thực thể và chuẩn hóa tiếng Việt."""

    def test_unlabeled_contact_extraction(self):
        text = "Nguyễn Văn An, 0901234567, 123 Lê Lợi, Phường Bến Nghé, Quận 1"
        info = extract_contact_info(text)
        self.assertEqual(info.phone, "0901234567")
        self.assertEqual(info.name, "Nguyễn Văn An")
        self.assertIn("123 Lê Lợi", info.address or "")
        self.assertIn("Quận 1", info.address or "")

    def test_labeled_contact_extraction(self):
        text = "Tên người nhận là Lê Hoàng Minh, sđt 0987654321, địa chỉ giao hàng 456 Hai Bà Trưng, Quận 3"
        info = extract_contact_info(text)
        self.assertEqual(info.phone, "0987654321")
        self.assertEqual(info.name, "Lê Hoàng Minh")
        self.assertEqual(info.address, "456 Hai Bà Trưng, Quận 3")

    def test_natural_quantity_parsing(self):
        self.assertEqual(extract_quantity("Lấy 2c áo thun"), 2)
        self.assertEqual(extract_quantity("Cho mình 3 cái bình nước"), 3)
        self.assertEqual(extract_quantity("Chốt 1 Áo thun basic"), 1)
        self.assertEqual(extract_quantity("Mua 5 áo size L"), 5)
        self.assertEqual(extract_quantity("2", is_awaiting_qty=True), 2)
        self.assertIsNone(extract_quantity("Tôi muốn mua áo thun"))

    def test_cancellation_intent(self):
        self.assertTrue(extract_cancellation("Thôi mình không mua nữa, hủy giúp mình"))
        self.assertTrue(extract_cancellation("Hủy đơn này giúp tôi"))
        self.assertTrue(extract_cancellation("Thôi hủy"))
        self.assertFalse(extract_cancellation("Tôi muốn đặt hàng"))


class TestChatbotIntegration(unittest.TestCase):
    """Kiểm tra tích hợp luồng chat đa lượt và an toàn dữ liệu."""

    @classmethod
    def setUpClass(cls):
        initialize_database()
        cls.client = TestClient(main.app)
        cls.origin = "http://127.0.0.1:5173"

    @classmethod
    def tearDownClass(cls):
        try:
            engine.dispose()
            TMP_DB.unlink(missing_ok=True)
        except Exception:
            pass

    def setUp(self):
        self.client.cookies.clear()
        res = self.client.post("/api/v1/session", headers={"Origin": self.origin})
        self.assertEqual(res.status_code, 200)

    def test_multi_turn_unlabeled_contact_flow(self):
        """Khách chốt hàng ở turn 1, gửi thông tin không nhãn ở turn 2 -> phải tạo đơn thành công."""
        # Turn 1
        res1 = self.client.post("/api/v1/chat/messages", headers={"Origin": self.origin}, json={
            "message": "Chốt 1 Áo thun basic cotton màu Xanh size M",
            "client_message_id": uuid4().hex
        })
        self.assertEqual(res1.status_code, 200)
        self.assertEqual(res1.json()["route"], "needs_information")
        self.assertIn("tên người nhận", res1.json()["message"])

        # Turn 2: Thông tin nhận hàng không nhãn
        res2 = self.client.post("/api/v1/chat/messages", headers={"Origin": self.origin}, json={
            "message": "Nguyễn Văn An, 0901234567, 123 Lê Lợi, Phường Bến Nghé, Quận 1",
            "client_message_id": uuid4().hex
        })
        self.assertEqual(res2.status_code, 200)
        self.assertEqual(res2.json()["route"], "pending_confirmation")
        self.assertTrue(res2.json().get("order_id"))
        self.assertIn("Đã tạo đơn nháp", res2.json()["message"])

    def test_multi_turn_quantity_preservation_on_product_repeat(self):
        """Khách nhắc lại sản phẩm ở turn 2 nhưng không nói lại số lượng -> số lượng không bị mất."""
        # Turn 1
        res1 = self.client.post("/api/v1/chat/messages", headers={"Origin": self.origin}, json={
            "message": "Cho mình lấy 2 bình giữ nhiệt Everyday màu Trắng 500ml",
            "client_message_id": uuid4().hex
        })
        self.assertEqual(res1.status_code, 200)
        self.assertEqual(res1.json()["route"], "needs_information")

        # Turn 2: Nhắc lại 'bình giữ nhiệt' nhưng không nói lại số lượng
        res2 = self.client.post("/api/v1/chat/messages", headers={"Origin": self.origin}, json={
            "message": "Bình giữ nhiệt đó gửi cho Trần Bình, sđt 0987654321, địa chỉ 456 Hai Bà Trưng, Quận 3",
            "client_message_id": uuid4().hex
        })
        self.assertEqual(res2.status_code, 200)
        self.assertEqual(res2.json()["route"], "pending_confirmation")
        # Kiểm tra số lượng trong thông báo là 2
        self.assertIn("2 × Bình giữ nhiệt Everyday", res2.json()["message"])

    def test_multi_turn_cancellation(self):
        """Khách đổi ý hủy đơn pending -> hệ thống xóa state và xác nhận an toàn."""
        # Turn 1
        res1 = self.client.post("/api/v1/chat/messages", headers={"Origin": self.origin}, json={
            "message": "Chốt 1 Áo thun basic cotton màu Trắng size M",
            "client_message_id": uuid4().hex
        })
        self.assertEqual(res1.status_code, 200)
        self.assertEqual(res1.json()["route"], "needs_information")

        # Turn 2: Hủy
        res2 = self.client.post("/api/v1/chat/messages", headers={"Origin": self.origin}, json={
            "message": "Thôi mình đổi ý không mua nữa, hủy đơn giúp mình",
            "client_message_id": uuid4().hex
        })
        self.assertEqual(res2.status_code, 200)
        self.assertEqual(res2.json()["route"], "answer")
        self.assertIn("Đã hủy yêu cầu đặt hàng", res2.json()["message"])

    def test_single_turn_unlabeled_complete_order(self):
        """Một câu duy nhất chứa đầy đủ sản phẩm, số lượng và thông tin liên lạc không nhãn."""
        res = self.client.post("/api/v1/chat/messages", headers={"Origin": self.origin}, json={
            "message": "Chốt 1 Áo thun basic cotton màu Xanh size M, Nguyễn Văn An, 0901234567, 123 Lê Lợi Quận 1",
            "client_message_id": uuid4().hex
        })
        self.assertEqual(res.status_code, 200)
        self.assertEqual(res.json()["route"], "pending_confirmation")
        self.assertTrue(res.json().get("order_id"))

    def test_natural_stock_query(self):
        """Khách hỏi tồn kho theo cách nói tự nhiên: 'Còn bao nhiêu cái áo thun trắng size M trong kho vậy'."""
        res = self.client.post("/api/v1/chat/messages", headers={"Origin": self.origin}, json={
            "message": "Còn bao nhiêu cái áo thun trắng size M trong kho vậy",
            "client_message_id": uuid4().hex
        })
        self.assertEqual(res.status_code, 200)
        self.assertEqual(res.json()["route"], "answer")
        self.assertIn("còn 18", res.json()["message"])
        self.assertIn("Áo thun basic cotton", res.json()["message"])


    def test_natural_product_availability_and_stock_queries(self):
        """Kiểm tra các câu hỏi tồn kho và sự hiện diện của sản phẩm theo cách nói tự nhiên (Issue 2..7)."""
        # Issue 2: Shop có áo thun xanh không
        r2 = self.client.post("/api/v1/chat/messages", headers={"Origin": self.origin}, json={
            "message": "Shop có áo thun xanh không", "client_message_id": uuid4().hex
        })
        self.assertEqual(r2.status_code, 200)
        self.assertEqual(r2.json()["route"], "answer")
        self.assertIn("còn 12", r2.json()["message"])

        # Issue 3: Shop còn áo thun size M không
        r3 = self.client.post("/api/v1/chat/messages", headers={"Origin": self.origin}, json={
            "message": "Shop còn áo thun size M không", "client_message_id": uuid4().hex
        })
        self.assertEqual(r3.status_code, 200)
        self.assertEqual(r3.json()["route"], "answer")
        self.assertIn("Trắng, M: còn 18", r3.json()["message"])
        self.assertIn("Xanh, M: còn 12", r3.json()["message"])

        # Issue 4: Shop có áo khoác không (sản phẩm không có trong catalog)
        r4 = self.client.post("/api/v1/chat/messages", headers={"Origin": self.origin}, json={
            "message": "Shop có áo khoác không", "client_message_id": uuid4().hex
        })
        self.assertEqual(r4.status_code, 200)
        self.assertEqual(r4.json()["route"], "answer")
        self.assertIn("chưa có sản phẩm này", r4.json()["message"])

        # Issue 5: Shop có bình Xanh bạc hà 750ml không (thuộc tính xung đột / không tồn tại)
        r5 = self.client.post("/api/v1/chat/messages", headers={"Origin": self.origin}, json={
            "message": "Shop có bình Xanh bạc hà 750ml không", "client_message_id": uuid4().hex
        })
        self.assertEqual(r5.status_code, 200)
        self.assertEqual(r5.json()["route"], "answer")
        self.assertIn("không có phân loại", r5.json()["message"])

        # Issue 6: Shop còn những loại cà phê nào thế
        r6 = self.client.post("/api/v1/chat/messages", headers={"Origin": self.origin}, json={
            "message": "Shop còn những loại cà phê nào thế", "client_message_id": uuid4().hex
        })
        self.assertEqual(r6.status_code, 200)
        self.assertEqual(r6.json()["route"], "answer")
        self.assertIn("250g, Hạt", r6.json()["message"])
        self.assertIn("Xay phin", r6.json()["message"])

        # Issue 7: Tôi đang tìm cà phê
        r7 = self.client.post("/api/v1/chat/messages", headers={"Origin": self.origin}, json={
            "message": "Tôi đang tìm cà phê", "client_message_id": uuid4().hex
        })
        self.assertEqual(r7.status_code, 200)
        self.assertEqual(r7.json()["route"], "answer")
        self.assertIn("Cà phê rang xay Đà Lạt", r7.json()["message"])

    def test_out_of_stock_variant_selection(self):
        """Khách chọn phân loại đã hết hàng (Hồng, S) -> báo out_of_stock và gợi ý phân loại còn hàng (Issue 10)."""
        res = self.client.post("/api/v1/chat/messages", headers={"Origin": self.origin}, json={
            "message": "tôi muốn mua áo thun hồng size S", "client_message_id": uuid4().hex
        })
        self.assertEqual(res.status_code, 200)
        self.assertEqual(res.json()["route"], "out_of_stock")
        self.assertIn("hiện đã hết hàng", res.json()["message"])
        self.assertIn("Trắng, M: còn 18", res.json()["message"])

    def test_order_guidance_no_demo_notice_and_street_address_extraction(self):
        """Bỏ câu 'Chỉ dùng thông tin giả cho demo nhé.' và nhận diện đúng địa chỉ 'Demo Street' (Issue 9)."""
        # Turn 1
        r1 = self.client.post("/api/v1/chat/messages", headers={"Origin": self.origin}, json={
            "message": "tôi muốn mua 250g cà phê hạt", "client_message_id": uuid4().hex
        })
        self.assertEqual(r1.status_code, 200)
        self.assertEqual(r1.json()["route"], "needs_information")
        # Tuyệt đối không chứa câu nhắc thông tin giả
        self.assertNotIn("Chỉ dùng thông tin giả cho demo nhé", r1.json()["message"])

        # Turn 2: gửi '250g cà phê hạt, Nguyễn Văn A, 0888581566, Demo Street'
        r2 = self.client.post("/api/v1/chat/messages", headers={"Origin": self.origin}, json={
            "message": "250g cà phê hạt, Nguyễn Văn A, 0888581566, Demo Street", "client_message_id": uuid4().hex
        })
        self.assertEqual(r2.status_code, 200)
        self.assertEqual(r2.json()["route"], "needs_information")
        # Đã nhận diện tên, sđt và địa chỉ 'Demo Street', chỉ còn thiếu số lượng
        self.assertNotIn("địa chỉ", r2.json()["message"])
        self.assertIn("số lượng", r2.json()["message"])
        self.assertNotIn("Chỉ dùng thông tin giả cho demo nhé", r2.json()["message"])

    def test_discount_inquiry_for_order(self):
        """Khách hỏi giảm giá khi mua 3 áo thun trắng size M -> trả lời rõ ràng không lặp giá (Issue 11)."""
        res = self.client.post("/api/v1/chat/messages", headers={"Origin": self.origin}, json={
            "message": "Tôi muốn mua 3 áo thun trắng, size M thì có giảm giá không",
            "client_message_id": uuid4().hex
        })
        self.assertEqual(res.status_code, 200)
        self.assertEqual(res.json()["route"], "answer")
        msg = res.json()["message"]
        self.assertIn("199,000₫/chiếc", msg)
        self.assertIn("597,000₫", msg)
        self.assertIn("giảm giá", msg)
        # Tuyệt đối không lặp lại chuỗi giá thừa
        self.assertNotIn("199,000₫, 199,000₫", msg)

    def test_vietnamese_accent_insensitive_product_search(self):
        """Tìm kiếm catalog API chuẩn hóa tiếng Việt, không phân biệt hoa thường hay có/không dấu (Issue 12)."""
        # Tìm 'áo thun'
        r1 = self.client.get("/api/v1/products?q=áo thun", headers={"Origin": self.origin})
        self.assertEqual(r1.status_code, 200)
        names1 = [p["name"] for p in r1.json()]
        self.assertIn("Áo thun basic cotton", names1)

        # Tìm 'áo'
        r2 = self.client.get("/api/v1/products?q=áo", headers={"Origin": self.origin})
        self.assertEqual(r2.status_code, 200)
        names2 = [p["name"] for p in r2.json()]
        self.assertIn("Áo thun basic cotton", names2)

        # Tìm 'bình'
        r3 = self.client.get("/api/v1/products?q=bình", headers={"Origin": self.origin})
        self.assertEqual(r3.status_code, 200)
        names3 = [p["name"] for p in r3.json()]
        self.assertIn("Bình giữ nhiệt Everyday", names3)

        # Tìm 'cà phê'
        r4 = self.client.get("/api/v1/products?q=cà phê", headers={"Origin": self.origin})
        self.assertEqual(r4.status_code, 200)
        names4 = [p["name"] for p in r4.json()]
        self.assertIn("Cà phê rang xay Đà Lạt", names4)

if __name__ == "__main__":
    unittest.main()
