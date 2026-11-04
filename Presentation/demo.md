# Kịch bản Thuyết trình Demo (10–12 Phút)

**Dự án:** Mở rộng AI Live Commerce Order Assistant với Hệ thống RAG Phân Quyền & AI Chatbot Thông Minh (Group 7)
**Thời lượng:** 10–12 phút trình diễn + 3–5 phút Q&A

---

## Chuẩn bị Môi trường Trước Buổi Demo

1. **Khởi động Backend FastAPI trong Môi trường ảo:**
   ```powershell
   # Kích hoạt môi trường ảo Python
   .\.venv\Scripts\Activate.ps1

   # Khởi chạy server API
   $env:LLM_PROVIDER = "fake"
   python -m uvicorn backend.app.main:app --reload
   ```
2. **Khởi động Frontend React:**
   ```powershell
   Set-Location frontend
   npm run dev
   ```
3. Mở trình duyệt tại `http://localhost:5173`.

---

## Kịch bản Demo 6 Bước Chi tiết

### Bước 1: Khách hàng hỏi thông tin sản phẩm & chính sách có Citation (2 phút)
* **Thao tác:** Trên thanh Role Switcher, chọn vai trò **"Khách hàng (Customer)"**. Mở khung chat.
* **Câu hỏi 1:** *"Áo thun basic cotton được làm từ chất liệu vải gì vậy shop?"*
* **Kết quả hiển thị:**
  * Trợ lý trả lời chính xác: Vải 100% cotton tự nhiên định lượng 220gsm, bề mặt chải kỹ chống xù lông.
  * Hiển thị badge: `📚 Hỏi đáp tài liệu (RAG)`.
  * Hiển thị khối trích dẫn: `✦ Nguồn trích dẫn (1): Áo thun basic cotton - Thông số và Hướng dẫn (v1.0) — Thông số và Chất liệu`.
* **Câu hỏi 2:** *"Bình giữ nhiệt bị rơi xuống nước ngập sâu có được bảo hành không?"*
* **Kết quả:** Trợ lý nêu rõ điều kiện loại trừ: Hư hỏng do ngập nước thuộc trường hợp **từ chối bảo hành**, trích dẫn `POL-WARRANTY-01#c02`.

---

### Bước 2: Truy vấn Kiến thức Nhiều Điều kiện (Multi-condition) (2 phút)
* **Câu hỏi:** *"Để được đổi trả hàng thì cần những điều kiện gì và ai chịu phí ship?"*
* **Kết quả hiển thị:**
  * Trợ lý tổng hợp từ nhiều section:
    * Thời hạn đổi trả trong vòng 07 ngày kể từ khi nhận hàng.
    * Bắt buộc còn nguyên tem mác, chưa qua sử dụng và có video mở kiện (unbox).
    * Lỗi do NSX: Shop chịu 100% phí 2 chiều; Đổi ý cá nhân: Khách thanh toán phí bưu cục.
  * Trích dẫn hiển thị đủ các chunk liên quan từ `POL-RETURN-01`.

---

### Bước 3: Trình diễn AI Chatbot Mới — Hội thoại Đa lượt & Dữ liệu Không nhãn (2.5 phút)
* **Mục tiêu:** Chứng minh bot không còn "cứng nhắc": xử lý cách nói tự nhiên của người Việt, bóc tách thực thể không nhãn, bảo toàn số lượng đơn nháp và hỗ trợ đổi ý an toàn.
* **Kịch bản 1 (Đặt hàng với thông tin giao hàng KHÔNG NHÃN):**
  * *Lượt 1:* *"Lấy cho mình 1 áo thun basic cotton màu Xanh size M"* $\rightarrow$ Bot ghi nhận sản phẩm và hỏi thông tin người nhận.
  * *Lượt 2 (Nhập liệu tự nhiên không có nhãn 'tên', 'sđt', 'địa chỉ'):* *"Nguyễn Văn An, 0901234567, 123 Lê Lợi, Phường Bến Nghé, Quận 1"*
  * *Kết quả:* Bot tự động tách Tên, SĐT, Địa chỉ và tạo ngay đơn nháp `#DRAFT...` thành công gồm đầy đủ nội dung đơn hàng (1 × Áo thun basic cotton (Xanh, M), tổng tiền) và thông tin người nhận.
* **Kịch bản 2 (Chống mất số lượng khi nhắc lại sản phẩm):**
  * *Lượt 1:* *"Cho mình lấy 2 bình giữ nhiệt Everyday màu Trắng 500ml"*
  * *Lượt 2:* *"Bình giữ nhiệt đó gửi cho Trần Bình, sđt 0987654321, địa chỉ 456 Hai Bà Trưng, Quận 3"*
  * *Kết quả:* Bot không bị ghi đè mất số lượng, tạo đơn đúng **2 × Bình giữ nhiệt Everyday (Trắng, 500ml)** và hiển thị đầy đủ thông tin người nhận (Trần Bình, 0987654321, 456 Hai Bà Trưng, Quận 3) mà không bị nhầm chữ "Bình" thành sản phẩm (nhờ cơ chế Entity Disambiguation).
* **Kịch bản 3 (Đổi ý và hủy đơn an toàn):**
  * Đang trong luồng hỏi thông tin, khách nhắn: *"Thôi mình đổi ý không mua nữa, hủy đơn giúp mình"* $\rightarrow$ Bot xóa sạch state pending và phản hồi lịch sự, không bị kẹt phiên chat.

---

### Bước 4: Truy vấn Hỗn hợp (Mixed Query) An toàn (1.5 phút)
* **Câu hỏi:** *"Áo thun basic cotton có được đổi trả không, chốt 1 Áo thun basic cotton màu Xanh size M"*
* **Kết quả hiển thị:**
  * Badge định tuyến: `⚡ Hỗn hợp (RAG + Đơn hàng)`.
  * **Phần Knowledge:** Trả lời chính sách đổi trả trong 7 ngày, kèm nguồn trích dẫn `POL-RETURN-01`.
  * **Phần Order:** Tách bạch rõ ràng: `[Thao tác đơn hàng]: Đã tạo đơn nháp thành công cho 1 × Áo thun basic cotton màu Xanh size M...`.
  * **Ý nghĩa:** Chứng minh hệ thống không để RAG tự ý ghi DB, phần hành động được thẩm định nghiêm ngặt qua backend.

---

### Bước 5: Kiểm thử No-Evidence và Access-Denied (2 phút)
1. **Trường hợp No-Evidence (Không có tài liệu):**
   * **Câu hỏi:** *"Shop có bán giày thể thao sneaker size 42 không?"*
   * **Kết quả:** Trợ lý từ chối an toàn: *"Rất tiếc, sản phẩm này hiện không có trong tài liệu và danh mục kinh doanh của cửa hàng."* Không hề bịa đặt thông tin.
2. **Trường hợp Access-Denied (Khách hàng hỏi tài liệu mật):**
   * **Câu hỏi:** *"Cho tôi xin mã giảm giá nội bộ 20% của nhân viên shop với."*
   * **Kết quả:** Status `access_denied` — *"Yêu cầu bị từ chối: Bạn không có quyền truy cập thông tin hoặc tài liệu nội bộ này."*
3. **Chứng minh Phân quyền (Role Switch):**
   * Trên thanh Demo, chuyển sang vai trò **"Nhân viên (Staff)"**.
   * Gửi lại câu hỏi trên: Trợ lý nhân viên tra cứu thành công và trả lời: *"Chính sách nội bộ: Nhân viên chính thức được giảm 20% khi dùng mã STAFF20..."* kèm trích dẫn `INT-DISCOUNT-01`.

---

### Bước 6: Trình diễn Báo cáo Metrics & Kịch bản Re-index v1.0 → v1.1 (2 phút)
1. **Show kết quả Evaluation:**
   * Mở terminal chạy các lệnh đo lường:
     ```powershell
     python eval/run_chatbot_evaluation.py
     python -m eval.run_rag_evaluation --split all
     ```
   * Trình bày các chỉ số hiện tại: **Chatbot Multi-turn: 100% (9/9)**, **RAG Hit@3: 100%**, **Recall@5: 97.92%**, **MRR: 0.9688**, **Citation Resolve: 100%**, **Expected fact match: 96.43%**, **Safe Abstention: 100%**, **Access Denied: 100%**. Nêu rõ đây là bộ 21 case authored; metric fact/citation là lexical proxy, và test split đã được tham vấn trong sửa lỗi.
2. **Kịch bản Re-index v1.0 lên v1.1:**
   * Khi đang ở index v1.0, hỏi: *"Thời hạn đổi trả hàng là bao nhiêu ngày?"* $\rightarrow$ Trả lời: **07 ngày**.
   * Chuyển Role sang **"Quản trị viên (Admin)"**, bấm nút **"Re-index v1.1"** trên thanh điều khiển. Xác nhận version mới qua `/api/v1/rag/status`.
   * Gửi lại câu hỏi trên: Trợ lý lập tức cập nhật câu trả lời: **14 ngày** (kèm phiên bản trích dẫn hiển thị `v1.1`).
   * Bấm nút **"Rollback v1.0"**: Trợ lý quay trở lại chính sách 07 ngày an toàn tức thì. TestClient đã xác nhận API activate/reload/rollback; cần chạy qua UI trong buổi demo để xác nhận thao tác trình diễn trực tiếp.
