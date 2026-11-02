# Báo cáo Dự án RAG — AI Live Commerce Order Assistant

**Cập nhật:** 02/11/2026
**Phạm vi:** Tiếp quản, hoàn thiện RAG có phân quyền và nâng cấp toàn diện AI Chatbot Engine (P0, P1, P2).

---

## 1. Tóm tắt Tổng quan

Dự án nối RAG vào trợ lý thương mại điện tử hiện có và giải quyết dứt điểm sự "cứng nhắc" của AI Chatbot.
- **RAG Engine**: Phân quyền 3 cấp (`public`, `staff`, `admin`), trích xuất citations từ 12 tài liệu (31 chunks) và hỗ trợ hot rollback index giữa các phiên bản v1.0 và v1.1.
- **AI Chatbot Engine (`chat_engine.py`)**: Tách module độc lập, chuẩn hóa tiếng Việt, hỗ trợ bóc tách thực thể người nhận hoàn toàn không nhãn, số lượng tự nhiên (*"2c"*, *"2 cái"*...), bảo toàn đơn hàng nháp đa lượt không bị mất số lượng và xử lý lệnh hủy/đổi ý tức thì.
- **Bảo toàn dữ liệu nghiệp vụ**: Database SQLite tiếp tục là nguồn duy nhất xác thực SKU, giá và tồn kho. Mọi câu trả lời của AI/RAG đều không được tự động ghi dữ liệu nghiệp vụ.

---

## 2. Các Nâng Cấp Nổi Bật Đã Triển Khai

1. **AI Chatbot Thông minh & Linh hoạt (P0, P1, P2)**:
   - Xóa bỏ sự phụ thuộc vào nhãn tiền tố: Khách nhắn tự nhiên *"An, 0901234567, 123 Lê Lợi Q1"* hoặc *"Demo Street"*, bot tự động bóc tách đúng Tên, SĐT và Địa chỉ.
   - Loại bỏ hoàn toàn câu nhắc nhở gây khó chịu *"Chỉ dùng thông tin giả cho demo nhé."* khi hướng dẫn tạo đơn hàng.
   - Cơ chế Disambiguation: Loại bỏ thông tin liên hệ khỏi câu chat trước khi đối chiếu Catalog SQLite, chống nhầm lẫn tên người hoặc tên đường phố thành sản phẩm.
   - Nhận diện tồn kho, tìm kiếm sản phẩm và phân loại tự nhiên: Xử lý mượt mà các mẫu câu *"Shop có áo thun xanh không"*, *"Shop còn những loại cà phê nào"*, *"Tôi đang tìm cà phê"*.
   - Xử lý thông minh khi sản phẩm hoặc phân loại không tồn tại: Thông báo lịch thiệp sản phẩm chưa có (*"Shop có áo khoác không"*), hoặc phân tích cụ thể khi thuộc tính xung đột (*"Bình Xanh bạc hà 750ml"*).
   - Kiểm tra tồn kho tức thì khi chọn phân loại: Nếu biến thể đã hết hàng (*"áo thun hồng size S"*), bot báo hết hàng ngay và gợi ý các phân loại còn hàng thay vì yêu cầu điền thông tin nhận hàng vô ích.
   - Sửa triệt để lỗi mất trạng thái đa lượt: Khách nhắc lại sản phẩm ở turn sau nhưng không nói lại số lượng thì số lượng vẫn được bảo toàn nguyên vẹn.
   - Thêm tính năng hủy đơn nháp đang chờ (`cancel_pending`) khi khách đổi ý.
2. **Bảo mật & Phân quyền RAG**:
   - Chặn giả mạo header `X-User-Role`: Chỉ chấp nhận vai trò Staff/Admin khi có `DEMO_STAFF_TOKEN`/`DEMO_ADMIN_TOKEN` khớp cấu hình backend.
   - Customer tuyệt đối không truy xuất tài liệu nội bộ trong mọi bước (retrieval, generation, citations).
   - Ingestion từ chối metadata phân quyền thiếu; loader kiểm tra mã hash SHA-256 chống hư hỏng bundle vô ý.
3. **Cơ chế Hot Rollback**:
   - Thay đổi phiên bản index tức thì thông qua con trỏ active nguyên tử `artifacts/active_index.json` mà không cần khởi động lại server.

---

## 3. Kết Quả Đo Lường & Đánh Giá Thực Tế

Toàn bộ các bộ kiểm thử được chạy độc lập trên database SQLite tạm thời:

| Bộ kiểm thử | Số ca chạy | Kết quả đạt | Tỷ lệ thành công |
| :--- | :---: | :---: | :---: |
| **Chatbot Multi-turn Evaluation** (`eval/run_chatbot_evaluation.py`) | 9 | 9 | **100.0%** |
| **Chatbot Unit & Integration Tests** (`tests/test_chatbot.py`) | 12 | 12 | **100.0%** |
| **RAG Evaluation Suite** (`eval/run_rag_evaluation.py`) | 20 | 20 | **100.0%** (Route/Status) |
| **RAG Unit & Security Tests** (`tests/test_rag.py`) | 10 | 10 | **100.0%** |
| **Inherited E-commerce Suite** (`eval/run_evaluation.py --provider fake`) | 14 | 14 | **100.0%** |
| **Frontend Production Build** (`npm run build`) | — | — | **SUCCESS** |

### Chi tiết các chỉ số RAG:
- **Hit@3**: 100.0%
- **Recall@5**: 93.89% (Dev: 86.9%, Test: 100%)
- **MRR**: 0.9000 (Dev: 0.7857, Test: 1.0)
- **Citation Metadata Resolution**: 100.0%
- **Safe Abstention & Access Denied**: 100.0%
- **Claim Support Proxy**: 70.0% (đối sánh chuỗi từ khóa expected)

---

## 4. Rủi Ro và Giới Hạn Còn Lại

1. **Shared Token Demo**: Chưa kết nối hệ thống SSO/IAM doanh nghiệp thực thụ; token demo chỉ phục vụ môi trường cục bộ.
2. **Lexical Vectorizer**: Hiện dùng hashed n-gram TF vectors thay vì semantic neural embedding model, nên khả năng hiểu các câu diễn đạt quá xa lạ ngoài từ điển còn hạn chế.
3. **Distributed Locking**: Chuyển đổi index active dùng filesystem cục bộ, chưa hỗ trợ đồng bộ đa máy chủ (cluster/multi-host).

---

*Tài liệu tham chiếu liên quan:*
- [Kế hoạch và Báo cáo TODO Chatbot](../todo/CHATBOT_UPGRADE_TODO.md)
- [Báo cáo Baseline P0](../artifacts/p0_baseline_report.md)
- [Báo cáo Đánh giá Chi tiết](../artifacts/evaluation_report.md)
- [Kiến trúc RAG](../given/RAG_Architecture.md)
