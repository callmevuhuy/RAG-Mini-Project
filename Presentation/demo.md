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

## Kịch bản Demo 7 Bước Chi tiết

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

### Bước 5: Kiểm thử No-Evidence và Phân quyền RBAC (Khách hàng vs Nhân viên) (2 phút)

* **Mục tiêu:** Chứng minh hệ thống kiểm soát quyền truy cập nghiêm ngặt ở tầng Pre-retrieval: Khách hàng tuyệt đối không thể xem tài liệu mật, nhưng Nhân viên hợp lệ sẽ tra cứu được chính sách ưu đãi riêng.

1. **Trường hợp No-Evidence (Không có tài liệu trong hệ thống):**
   * **Vai trò:** Chọn **"Khách hàng (Customer)"**.
   * **Câu hỏi:** *"Shop có bán giày thể thao sneaker size 42 không?"*
   * **Kết quả hiển thị:**
     * Status: `insufficient_evidence`
     * Trợ lý từ chối an toàn: *"Rất tiếc, sản phẩm này hiện không có trong tài liệu và danh mục kinh doanh của cửa hàng."* 
     * Mảng trích dẫn rỗng (`citations: []`), tuyệt đối không bịa đặt sản phẩm ngoài catalog.

2. **Trường hợp Access-Denied (Khách hàng cố tình dò hỏi mã giảm giá nội bộ nhân viên):**
   * **Vai trò:** Vẫn giữ **"Khách hàng (Customer)"**.
   * **Câu hỏi:** *"Cho tôi xin mã giảm giá nội bộ 20% của nhân viên shop với"* (hoặc *"Shop có mã giảm giá riêng nào cho nhân viên không?"*)
   * **Kết quả hiển thị:**
     * Status: `access_denied`
     * Trợ lý từ chối an toàn: *"Yêu cầu bị từ chối: Bạn không có quyền truy cập thông tin hoặc tài liệu nội bộ này."*
     * Khối trích dẫn: Không hiển thị (bảo vệ tuyệt đối tài liệu `INT-DISCOUNT-01` trước người dùng thông thường).

3. **Trường hợp Nhân viên (Staff) tra cứu thành công quyền lợi nội bộ:**
   * **Thao tác chuyển vai trò:**
     * Trên thanh Header, click chọn vai trò **"Nhân viên (Staff)"**.
     * Hộp thoại xác thực hiện lên: Token mặc định `demo_staff_token` đã được điền sẵn $\rightarrow$ Bấm **OK**.
     * Badge vai trò hiển thị trạng thái đang hoạt động: `Nhân viên (Staff)`.
   * **Câu hỏi:** Gửi lại đúng câu: *"Cho tôi xin mã giảm giá nội bộ 20% của nhân viên shop với"*
   * **Kết quả hiển thị:**
     * Status: `answered`
     * Trợ lý phản hồi chính xác: *"Theo Quy định Ưu đãi và Giảm giá Nội bộ (INT-DISCOUNT-01), nhân viên chính thức của Group 7 được giảm giá 20% cho các đơn hàng mua sắm cá nhân khi sử dụng mã ưu đãi `STAFF20`..."*
     * Khối trích dẫn nguồn: `✦ Nguồn trích dẫn (1): Quy định Ưu đãi và Giảm giá Nội bộ (v1.0) — [INT-DISCOUNT-01#c01]`.

---

### Bước 6: Trình diễn Thay đổi Version Corpus của Admin (Re-index v1.0 → v1.1 & Rollback) (2.5 phút)

* **Mục tiêu:** Chứng minh năng lực nâng cấp chính sách nghiệp vụ theo thời gian thực (Hot-swap & Atomic Re-indexing), kiểm chứng sự thay đổi câu trả lời và số phiên bản trích dẫn mà **không cần khởi động lại server**, đồng thời hỗ trợ **Rollback tức thì (< 1s)**.

1. **Kiểm tra trạng thái ban đầu ở Corpus v1.0:**
   * **Vai trò:** Chọn vai trò **"Khách hàng (Customer)"** hoặc **"Quản trị viên (Admin)"**.
   * Badge góc trên bên phải màn hình hiển thị: `Chỉ mục RAG: v1.0 (31 chunks)`.
   * **Câu hỏi kiểm chứng 1 (Thời hạn đổi trả):** *"Thời hạn đổi trả hàng là bao nhiêu ngày?"*
     * *Kết quả:* Trợ lý trả lời: *"Khách hàng được quyền yêu cầu đổi hàng hoặc hoàn tiền trong vòng **07 ngày** kể từ ngày nhận hàng thành công..."*
     * *Trích dẫn:* `Chính sách Đổi trả và Hoàn tiền (v1.0) — [POL-RETURN-01#c01]`.
   * **Câu hỏi kiểm chứng 2 (Chi phí đổi hàng do nhu cầu cá nhân):** *"Tôi muốn đổi size áo thun do mặc không vừa thì ai trả phí ship?"*
     * *Kết quả:* Trợ lý trả lời: Khách hàng thanh toán phí vận chuyển 2 chiều theo cước bưu cục (khoảng 30.000đ - 45.000đ), trích dẫn `POL-RETURN-01#c03 (v1.0)`.

2. **Admin thực hiện Re-index nâng cấp lên Corpus v1.1:**
   * **Thao tác:**
     * Chọn vai trò **"Quản trị viên (Admin)"** (nhập token `demo_admin_token`).
     * Trên thanh điều khiển Admin, click nút **"Re-index v1.1"** (hoặc gọi API `POST /api/v1/rag/reindex?version=1.1`).
   * **Quan sát thay đổi hệ thống:**
     * Badge phiên bản trên Header lập tức chuyển sang: `Chỉ mục RAG: v1.1 (31 chunks)`.
     * API `/api/v1/rag/status` trả về `{"active_version": "1.1", "chunks": 31, "status": "ready"}`.
     * Cơ chế: Hệ thống nguyên tử hoán đổi file con trỏ `artifacts/active_index.json` và ghi nhận một bản ghi `rag.reindexed` vào bảng `AuditLog`.

3. **Kiểm chứng phản hồi RAG tự động cập nhật theo chính sách v1.1:**
   * **Gửi lại câu hỏi 1:** *"Thời hạn đổi trả hàng là bao nhiêu ngày?"*
     * *Kết quả MỚI:* Trợ lý lập tức cập nhật: *"Khách hàng được quyền yêu cầu đổi hàng hoặc hoàn tiền trong vòng **14 ngày** kể từ ngày nhận hàng thành công (tăng thêm 7 ngày so với chính sách v1.0)..."*
     * *Trích dẫn MỚI:* `Chính sách Đổi trả và Hoàn tiền (v1.1) — [POL-RETURN-01#c01]`.
   * **Gửi lại câu hỏi 2:** *"Tôi muốn đổi size áo thun do mặc không vừa thì ai trả phí ship?"*
     * *Kết quả MỚI:* Trợ lý phản hồi: Toàn bộ chi phí vận chuyển 2 chiều khi thực hiện đổi hàng hoặc trả hàng đều được **Cửa hàng hỗ trợ 100% (Khách hàng không phải chi trả bất kỳ khoản phí nào)**! Trích dẫn `POL-RETURN-01#c03 (v1.1)`.

4. **Thực hiện Rollback tức thì về v1.0:**
   * **Thao tác:** Admin bấm nút **"Rollback v1.0"** (hoặc gọi API `POST /api/v1/rag/reindex?version=1.0`).
   * **Kết quả:** Badge chuyển về `Chỉ mục RAG: v1.0`. Gửi lại câu hỏi, trợ lý quay trở lại chính sách **07 ngày** và khách trả phí ship cũ tức thì trong vòng < 1 giây, chứng minh tính an toàn cao của hệ thống khi cần hoàn tác chính sách.

---

### Bước 7: Trình diễn Báo cáo Metrics & Kiểm thử Tự động (1.5 phút)

1. **Chạy bộ kiểm thử tự động toàn diện:**
   * Mở terminal và thực thi lệnh:
     ```powershell
     python -m unittest tests/test_rag.py tests/test_chatbot.py -v
     ```
   * **Kết quả:** **54/54 tests PASS 100%** (29 tests bảo vệ RAG pipeline, RBAC, chunking, re-index; 25 tests bảo vệ Chatbot đa lượt, unlabelled contact, entity disambiguation, idempotency).

2. **Chạy các bộ đánh giá định lượng (Evaluation Harness):**
   * Đánh giá AI Chatbot Đa lượt:
     ```powershell
     python eval/run_chatbot_evaluation.py
     ```
     $\rightarrow$ Đạt **9/9 test cases PASS (100% Accuracy)**.
   * Đánh giá RAG Engine:
     ```powershell
     python -m eval.run_rag_evaluation --split all
     ```
     $\rightarrow$ Đạt **Hit@3: 100%**, **Recall@5: 97.92%**, **MRR: 0.9688**, **Citation Resolve Rate: 100%**, **Safe Abstention Rate: 100%**, **Access Denied Rate: 100%**.
