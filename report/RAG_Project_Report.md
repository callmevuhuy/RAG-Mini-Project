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
   - Loại bỏ hoàn toàn câu nhắc nhở demo gây phiền toái trên toàn bộ ứng dụng (frontend storefront, modal đặt hàng, placeholder và phản hồi chatbot).
   - Xử lý câu hỏi giảm giá / chiết khấu (Issue 11): Tính toán chính xác tổng tiền đơn hàng và phản hồi rõ ràng chính sách niêm yết, loại bỏ hoàn toàn việc lặp lại danh sách giá thừa.
   - Chuẩn hóa tìm kiếm sản phẩm tiếng Việt (Issue 12): Tích hợp bộ chuẩn hóa Unicode và lọc không dấu/có dấu giúp tìm kiếm chính xác các từ khóa *"áo thun"*, *"áo"*, *"bình"*, *"cà phê"* trên thanh tìm kiếm storefront.
   - Nhận diện cách gọi đời thường và loại trừ an toàn (Issue 13, Issue 14): Cho phép khách gọi *"áo trắng size M"*, *"áo màu xanh"* mà không cần gõ từ *"thun"*, đồng thời chủ động loại trừ các loại trang phục ngoài danh mục (*"áo khoác"*, *"áo sơ mi"*, *"áo len"*...).
   - Tự động chốt biến thể duy nhất & giải quyết vòng lặp xác nhận (Issue 15): Nếu thuộc tính khách chọn chỉ tương ứng với duy nhất 1 biến thể (ví dụ Bình giữ nhiệt màu đen duy nhất chỉ có dung tích 750ml), bot lập tức chốt biến thể thay vì hỏi lặp lại; đồng thời hỗ trợ các từ khóa đồng thuận (*"yes"*, *"ok"*, *"đúng rồi"*...).
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
| **Chatbot Unit & Integration Tests** (`tests/test_chatbot.py`) | 23 | 23 | **100.0%** |
| **RAG Evaluation Suite** (`eval/run_rag_evaluation.py`) | 21 | 21 | **100.0%** (Route/Status) |
| **RAG Unit & Security Tests** (`tests/test_rag.py`) | 29 | 29 | **100.0%** |
| **Inherited E-commerce Suite** (`eval/run_evaluation.py --provider fake`) | 14 | 14 | **100.0%** |
| **Frontend Production Build** (`npm run build`) | — | — | **SUCCESS** |

### Chi tiết các chỉ số RAG:
- **Hit@3**: 100.0%
- **Recall@5**: 97.92% (Dev: 95.24%, Test: 100%)
- **MRR**: 0.9688 (Dev: 0.9286, Test: 1.0)
- **Citation Metadata Resolution**: 100.0%
- **Expected answer fact match / cited evidence lexical support**: 96.43% / 96.43%.
- **Safe Abstention & Access Denied**: 100.0%
- **Holdout regression V13 (20 cases)**: Hit@3, Recall@5, citation resolution, fact match, lexical support, routing và safety đạt 100% sau hai regression fixes. V13 đã được dùng khi tuning; không phải blind holdout.
- Fact/evidence metrics là so khớp chuỗi, không phải entailment review. Test split ban đầu đã được tham vấn qua MC-03; chưa có human claim review hoặc blind evaluation độc lập.

---

## 4. Nhật Ký Điều Tra & Xử Lý Sự Cố Chatbot (Issue Log & Resolution Ledger)

Dưới đây là chi tiết toàn bộ các issues phát hiện trong quá trình kiểm thử thực tế người dùng và giải pháp kỹ thuật đã triển khai để giải quyết dứt điểm:

| Mã Issue | Tình huống người dùng & Hiện tượng lỗi ban đầu | Nguyên nhân gốc rễ (Root Cause) | Giải pháp kỹ thuật đã xử lý | Ca kiểm thử bảo vệ |
|---|---|---|---|---|
| **Issue 2** | Khách hỏi: *"Còn bao nhiêu cái áo thun trắng size M trong kho vậy"* ➔ Bị handoff sang nhân viên hỗ trợ. | Router regex thiếu nhận diện mẫu câu hỏi số lượng tồn kho tự nhiên `còn bao nhiêu ... trong kho`. | Bổ sung `r"\bcon\s+bao\s+nhieu\b"`, `r"\btrong\s+kho\b"` vào `ORDER_READ_PATTERNS` và xử lý nhánh `check_stock`. | `test_natural_stock_query` |
| **Issue 3** | Khách hỏi sự hiện diện chung: *"Shop có áo thun không"*, *"Shop có bình giữ nhiệt không"* ➔ Không nhận diện được sản phẩm hoặc chuyển handoff. | Thiếu mẫu câu hỏi tổng quát dạng `shop có / shop còn / bên mình có`. | Bổ sung pattern `r"\b(?:shop\|ben\s+minh)\s+(?:co\|con)\b"` và trích xuất danh mục đối chiếu SQLite. | `test_natural_product_availability_and_stock_queries` |
| **Issue 4** | Khách hỏi danh mục loại: *"Shop còn những loại cà phê nào"* ➔ Phản hồi chưa đầy đủ thông tin từng loại. | Chưa có nhánh chuyên biệt tổng hợp danh sách phân loại (variants) của một sản phẩm khi hỏi `những loại / các loại`. | Thêm nhận diện `is_asking_all_types`, duyệt qua toàn bộ variants và trả về chi tiết tên, giá, số lượng tồn kho từng loại. | `test_natural_product_availability_and_stock_queries` |
| **Issue 5** | Khách tìm kiếm tư vấn chung: *"Tôi đang tìm cà phê"*, *"Đang tìm bình"* ➔ Không nhận diện được intent tư vấn. | Router và chat engine chỉ xử lý câu mua hoặc hỏi giá/tồn kho cụ thể. | Thêm nhánh `is_discovery`, giới thiệu tổng quan công năng sản phẩm cùng khoảng giá niêm yết (từ min đến max). | `test_natural_product_availability_and_stock_queries` |
| **Issue 6** | Khách hỏi sản phẩm không kinh doanh: *"Shop có áo khoác không"* ➔ Phản hồi lỗi hoặc nhầm lẫn sang sản phẩm khác. | Đối chiếu catalog rỗng (`candidates == []`) chưa có thông điệp hướng dẫn rõ ràng. | Báo lịch sự shop chưa có sản phẩm này và liệt kê đầy đủ các danh mục sản phẩm hiện có để khách tham khảo. | `test_natural_product_availability_and_stock_queries` |
| **Issue 7** | Khách chọn tổ hợp thuộc tính không tồn tại: *"Bình giữ nhiệt Xanh bạc hà 750ml"* ➔ Bot im lặng hoặc lỗi matching. | Xanh bạc hà chỉ có ở 500ml, còn 750ml chỉ có Đen và Kem (thuộc tính xung đột chéo). | Phân tích tập con `matching_sub`, chỉ rõ tổ hợp không tồn tại và gợi ý từng phân loại thực tế còn hàng. | `test_natural_product_availability_and_stock_queries` |
| **Issue 8** | Nhầm lẫn địa chỉ tiếng Anh (*"Demo Street"*) hoặc tên người thành tên sản phẩm cần mua. | Bộ trích xuất contact thông thường chỉ nhận diện đường phố tiếng Việt có tiền tố `"đường"`, `"phố"`. | Cải tiến `extract_contact_info` nhận diện các từ khóa đường phố quốc tế/không nhãn và tách riêng residual text trước khi tra cứu Catalog. | `test_order_guidance_no_demo_notice_and_street_address_extraction` |
| **Issue 9** | Câu nhắc nhở: *"Chỉ dùng thông tin giả cho demo nhé."* xuất hiện khi hướng dẫn khách đặt hàng gây phiền hà. | Dư thừa chuỗi hướng dẫn demo trong câu trả lời chatbot. | Loại bỏ triệt để cảnh báo demo khỏi prompt và toàn bộ phản hồi của `chat_engine.py` cũng như storefront. | `test_order_guidance_no_demo_notice_and_street_address_extraction` |
| **Issue 10** | Khách chọn biến thể đã hết hàng (*"áo thun hồng size S"* - tồn kho = 0) ➔ Bot vẫn hỏi tên/sđt/địa chỉ rồi mới báo lỗi. | Kiểm tra tồn kho bị đặt sau bước thu thập thông tin người nhận. | Đưa kiểm tra tồn kho lên ngay sau khi xác định được variant; nếu `available <= 0` lập tức thông báo hết hàng và gợi ý các phân loại còn hàng. | `test_out_of_stock_variant_selection` |
| **Issue 11** | Khách hỏi giảm giá: *"Tôi muốn mua 3 áo thun trắng size M thì có giảm giá không"* ➔ Bot lặp lại chuỗi giá 2 lần (`199,000₫, 199,000₫`). | Nhánh `check_price` ghép nối chuỗi giá đơn và chuỗi giá tổng bị trùng lặp. | Tái cấu trúc nhánh chiết khấu: tính chính xác tổng giá trị đơn hàng (3 × 199.000₫ = 597.000₫) và khẳng định chính sách bán đúng giá niêm yết rõ ràng. | `test_discount_inquiry_for_order` |
| **Issue 12** | Tìm kiếm sản phẩm storefront không ra kết quả khi gõ tiếng Việt có dấu hoặc gõ tắt (*"áo"*, *"bình"*, *"cà phê"*). | Backend SQLite so khớp `LIKE '%q%'` phân biệt dấu (accent-sensitive). | Bổ sung hàm chuẩn hóa Unicode NFD `engine_norm()` cho endpoint `/api/v1/products?q=...` lọc không phân biệt hoa thường và dấu tiếng Việt. | `test_vietnamese_accent_insensitive_product_search` |
| **Issue 13** | Khách gọi đời thường: *"Tôi muốn mua 2 cái áo trắng size M"* ➔ Báo không tìm thấy sản phẩm; Turn 2 khách nhắn lại bị handoff. | Từ khóa bắt buộc chữ `"thun"`; câu chat chỉ có `"áo"` nên `candidates == []`; Turn 2 không có pending order nên router handoff. | Cho phép từ `"áo"` kết hợp thuộc tính màu/size nhận diện `Áo thun basic cotton` (có danh sách loại trừ an toàn); bảo toàn pending state. | `test_issue13_colloquial_apparel_order_and_multi_turn` |
| **Issue 14** | Khách hỏi: *"Shop còn áo màu xanh không?"* ➔ Bot báo shop chưa có sản phẩm này. | Từ khóa không khớp do thiếu từ `"thun"` trong câu hỏi màu sắc. | Nhận diện `"áo"` + màu xanh để match `Áo thun basic cotton` và báo chính xác tồn kho của biến thể `Xanh, M` (còn 12 sản phẩm). | `test_issue14_colloquial_apparel_stock_query` |
| **Issue 15** | Khách đặt: *"3 cái bình giữ nhiệt màu đen"*, bot hỏi: *"Bạn muốn chọn: Đen, 750ml?"*, khách đáp: *"Yes, 3 cái bình màu đen"* ➔ Lặp lại câu hỏi vô tận. | Màu Đen của bình giữ nhiệt chỉ có duy nhất dung tích 750ml nhưng hàm yêu cầu đủ 2 thuộc tính mới chốt; thiếu nhận diện từ khóa đồng thuận. | Tự động chốt biến thể duy nhất khi thuộc tính nhận diện là độc nhất; bổ sung nhận diện từ khóa đồng thuận (`yes`, `ok`, `đúng rồi`...) để kích hoạt biến thể. | `test_issue15_unique_variant_no_clarification_loop` |

---

## 5. Rủi Ro và Giới Hạn Còn Lại

1. **Shared Token Demo**: Chưa kết nối hệ thống SSO/IAM doanh nghiệp thực thụ; token demo chỉ phục vụ môi trường cục bộ.
2. **Lexical Vectorizer**: Hiện dùng hashed n-gram TF vectors thay vì semantic neural embedding model, nên khả năng hiểu các câu diễn đạt quá xa lạ ngoài từ điển còn hạn chế.
3. **Distributed Locking**: Chuyển đổi index active dùng filesystem cục bộ, chưa hỗ trợ đồng bộ đa máy chủ (cluster/multi-host).

---

*Tài liệu tham chiếu liên quan:*
- [Kế hoạch và Báo cáo TODO Chatbot](../todo/CHATBOT_UPGRADE_TODO.md)
- [Báo cáo Baseline P0](../artifacts/p0_baseline_report.md)
- [Báo cáo Đánh giá Chi tiết](../artifacts/evaluation_report.md)
- [Kiến trúc RAG](../given/RAG_Architecture.md)
