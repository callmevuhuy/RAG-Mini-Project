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


if __name__ == "__main__":
    unittest.main()
