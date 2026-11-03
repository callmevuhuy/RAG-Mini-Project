# Kịch bản Thuyết trình (Speaker Notes): RAG Extension — AI Live Commerce Order Assistant

**Dự án:** Trợ lý Thương mại Hội thoại Thông minh với Hệ thống RAG Phân Quyền & AI Chatbot Đa Lượt  
**Nhóm thực hiện:** Group 7  
**Thời lượng dự kiến:** 10–12 phút thuyết trình + 3–5 phút Q&A bảo vệ đồ án  
**Thông điệp cốt lõi:**  
> *"RAG tra cứu tri thức chính sách và catalog có nguồn trích dẫn kiểm chứng được; Database SQLite và Backend API độc quyền quyết định đơn hàng, giá bán và tồn kho khả dụng."*

---

## Slide 1: Giới thiệu Dự án (Thời lượng: ~45 giây)

* **Lời mở đầu:**  
  "Kính chào quý thầy cô và các bạn. Hôm nay, đại diện cho Group 7, em xin phép trình bày dự án: **AI Live Commerce Order Assistant mở rộng với Hệ thống RAG Phân Quyền và AI Chatbot Đa Lượt**.  
  Đây là bước phát triển tiếp nối trực tiếp từ mini-project môn *LLM & Prompt Engineering*. Nếu như ở môn trước, nhóm đã xây dựng thành công luồng nhận diện ý định đặt hàng và tạo đơn nháp từ câu chat, thì ở môn RAG này, nhóm đã giải quyết trọn vẹn bài toán: **Làm sao để trợ lý vừa am hiểu sâu sắc chính sách bán hàng từ tài liệu, vừa có phân quyền dữ liệu nghiêm ngặt, mà vẫn giữ an toàn tuyệt đối cho cơ sở dữ liệu vận hành**."

* **Điểm nhấn cần nhấn mạnh:**  
  "Ranh giới cốt lõi trong toàn bộ hệ thống của nhóm là: **RAG chỉ có quyền đọc để trả lời câu hỏi**; mọi quyết định liên quan đến giá tiền, số lượng tồn kho và tạo đơn đều do **FastAPI và SQLite** thẩm định độc quyền."

---

## Slide 2: Bối cảnh & Đặt vấn đề: Từ LLM sang RAG (Thời lượng: ~50 giây)

* **Nội dung thuyết minh:**  
  "Trước hết, nhìn lại nền tảng kế thừa: Nhóm tiếp tục giữ nguyên ứng dụng bán hàng đầy đủ gồm giao diện React/Vite, backend FastAPI và cơ sở dữ liệu SQLite quản lý Catalog, Tồn kho, Giỏ hàng và Audit Log. Nhóm tuyệt đối không đập đi xây lại.  
  Tuy nhiên, ở phiên bản LLM trước đây, hệ thống tồn tại 3 rào cản lớn:  
  1. **Thiếu hụt tri thức tài liệu:** Khách hỏi về chính sách đổi trả, thời hạn bảo hành, hay quy định đồng kiểm thì bot không thể trả lời chính xác vì thông tin này không nằm trong schema database.  
  2. **Nguy cơ Hallucination:** Khi bị hỏi dồn hoặc hỏi về sản phẩm ngoài danh mục, mô hình ngôn ngữ dễ tự bịa đặt ngày giao hàng hoặc tự suy diễn điều kiện bảo hành.  
  3. **Không có phân quyền:** Không thể phân biệt được thông tin nào khách hàng được xem, thông tin nào là quy trình nội bộ của nhân viên kho hay mã giảm giá đặc quyền.  
  Chính vì vậy, mục tiêu của môn RAG là bổ sung Knowledge Base có cấu trúc, áp dụng phân quyền truy xuất trước khi tìm kiếm, và trả lời có nguồn trích dẫn minh bạch."

---

## Slide 3: Kiến trúc Tổng thể & Ranh giới Bảo mật (Thời lượng: ~60 giây)

* **Nội dung thuyết minh:**  
  "Trên màn hình là sơ đồ kiến trúc tổng thể của hệ thống.  
  Khi người dùng gửi tin nhắn từ trình duyệt, request sẽ đi kèm Session Cookie và Origin Header. Điểm đến đầu tiên là **FastAPI Gateway**, nơi thực hiện kiểm tra bảo mật: giới hạn tần suất (Rate Limiting), kiểm tra session và giải quyết vai trò người dùng thông qua Token bí mật của server.  
  Tiếp theo, tin nhắn được đưa qua **Unified Router (`src/router.py`)**. Router sẽ phân tách yêu cầu thành 5 nhánh:  
  - Nhánh **Knowledge Query**: Chỉ đọc tài liệu qua RAG Index đã được lọc quyền, sinh câu trả lời kèm citation.  
  - Nhánh **Order Action**: Đi vào Chat Engine, đối chiếu SQLite để kiểm tra tồn kho và tạo đơn nháp.  
  - Nhánh **Mixed Query**: Tách độc lập thành 2 phần — vừa trả lời chính sách, vừa xử lý đơn hàng.  
  - Nhánh **Safety & Handoff**: Chặn đứng các hành vi tấn công hoặc chuyển tiếp nhân viên.  
  Nhóm đặc biệt cam kết ranh giới an toàn: RAG hoàn toàn là luồng **Read-Only**. Output của RAG không bao giờ trở thành câu lệnh ghi trực tiếp vào cơ sở dữ liệu."

---

## Slide 4: Unified Router — Phân luồng Ý định Tự nhiên (Thời lượng: ~50 giây)

* **Nội dung thuyết minh:**  
  "Điểm đột phá đầu tiên về mặt xử lý ngôn ngữ là bộ **Unified Router**.  
  Trong thực tế bán hàng online, khách không bao giờ nhắn tin theo một khuôn mẫu cứng nhắc. Họ có thể hỏi: *'Áo thun có được đổi trả không và lấy cho mình 1 chiếc size M'*.  
  Bộ router của nhóm sử dụng kỹ thuật phân tách mệnh đề tự nhiên (Heuristic Clause Splitting) dựa trên các liên từ tiếng Việt có dấu và không dấu như: *'và', 'nhưng', 'rồi', 'với lại', 'ngoài ra'* cùng các dấu ngắt câu.  
  Router sẽ phân tích độc lập: đâu là mệnh đề tri thức (knowledge clause) và đâu là mệnh đề hành động (order clause). Đồng thời, nhóm bổ sung cơ chế khử nhập nhằng (Disambiguation) để tên sản phẩm xuất hiện trong câu hỏi chính sách không bị nhận nhầm thành lệnh đặt hàng.  
  Ngoài ra, Router tích hợp sẵn bộ lọc phòng thủ Prompt Injection, chặn đứng ngay từ cửa vào các câu lệnh phá hoại như *'bỏ qua mọi chính sách'* hay *'tiết lộ API secret'*."

---

## Slide 5: Corpus & Ingestion — Knowledge Base Tái lập (Thời lượng: ~50 giây)

* **Nội dung thuyết minh:**  
  "Về mặt dữ liệu, nhóm đã xây dựng một Knowledge Base hoàn chỉnh gồm **12 tài liệu Markdown** chuẩn hóa, được chia thành **31 chunks** có ý nghĩa nghiệp vụ rõ ràng, vượt qua yêu cầu tối thiểu của đề tài.  
  Tài liệu bao phủ từ catalog chi tiết 3 nhóm sản phẩm (Áo thun cotton, Bình giữ nhiệt Everyday, Cà phê Cầu Đất), bảng hướng dẫn chọn size, 3 chính sách (Giao hàng, Bảo hành, Đổi trả), 2 bài FAQ và 2 tài liệu quy trình nội bộ của nhân viên.  
  Toàn bộ dữ liệu được quản lý qua `corpus_manifest.json`. Mỗi tài liệu bắt buộc phải khai báo đầy đủ: `doc_id`, `version`, `author` và quan trọng nhất là `access_level`. Chunk ID được sinh ổn định theo dạng `{doc_id}#cNN` và cắt theo tiêu đề cấp 2 (Markdown H2).  
  Toàn bộ chỉ mục được đóng gói thành file bundle có gắn mã kiểm tra toàn vẹn **SHA-256 Checksum**, đảm bảo tính tái lập 100% khi deploy."

---

## Slide 6: Phân quyền Đa tầng (Pre-retrieval RBAC) (Thời lượng: ~60 giây)

* **Nội dung thuyết minh:**  
  "Đây là một trong những tiêu chí quan trọng nhất trong rubric chấm điểm: **Phân quyền dữ liệu**.  
  Nhóm áp dụng nguyên tắc: **Pre-retrieval Role Filtering — Lọc quyền trước khi xếp hạng**.  
  Tại sao phải lọc trước? Bởi vì nếu chúng ta truy xuất tất cả rồi mới dùng filter ẩn câu trả lời ở bước cuối, thì thông tin mật của công ty đã vô tình đi vào candidate list, đi vào bộ nhớ đệm (cache), hoặc nguy hiểm hơn là đi vào prompt của mô hình ngôn ngữ.  
  Trong hàm `retrieve()`, hệ thống đối chiếu vai trò người dùng ngay từ đầu:  
  - Khách hàng (`customer`): Chỉ quét các chunk có nhãn `public`.  
  - Nhân viên (`staff`): Được quét tài liệu `public` và tài liệu nội bộ hỗ trợ như quy trình đối soát camera WMS hay mã giảm giá nhân viên.  
  - Quản trị viên (`admin`): Toàn quyền trên toàn bộ dữ liệu.  
  Về mặt xác thực, backend yêu cầu token bí mật (`DEMO_STAFF_TOKEN`, `DEMO_ADMIN_TOKEN`). Nút chọn vai trò trên giao diện chỉ là công cụ mô phỏng demo, backend mới là nơi thẩm định quyền hạn thực tế."

---

## Slide 7: Cơ chế Vectorizer & Retrieval Tối ưu (Thời lượng: ~50 giây)

* **Nội dung thuyết minh:**  
  "Ở tầng tìm kiếm, nhóm triển khai bộ **Lexical Hashed N-gram Term-Frequency Vectorizer** với không gian 1024 chiều.  
  Lý do nhóm lựa chọn giải pháp này cho bản demo cục bộ là: tốc độ phản hồi cực nhanh dưới 5ms, chạy hoàn toàn offline, độc lập và nhẹ nhàng, không gây tải cho máy tính demo và không bị phụ thuộc vào service bên ngoài.  
  Để khắc phục hạn chế của lexical search với các câu hỏi phức tạp nhiều điều kiện, nhóm đã tích hợp cơ chế **Topic Query Expansion**. Ví dụ, khi khách hỏi về điều kiện đổi trả do mặc thử không vừa, hệ thống tự động mở rộng truy vấn để đưa cả điều khoản thời hạn 7 ngày, điều kiện còn nguyên tem mác và quy định về phí ship vào Top-3 ranking.  
  Đồng thời, nhóm luôn tuân thủ nguyên tắc: Cosine Similarity chỉ là điểm xếp hạng mức độ khớp từ khóa, tuyệt đối không được coi là độ chắc chắn về mặt sự thật."

---

## Slide 8: Grounded Generation & Citation Contract (Thời lượng: ~50 giây)

* **Nội dung thuyết minh:**  
  "Về định dạng phản hồi, API RAG của nhóm tuân thủ nghiêm ngặt hợp đồng JSON theo yêu cầu đề bài gồm: `status`, `answer`, mảng `citations` và `missing_information`.  
  Mỗi citation đều ghi rõ `chunk_id`, `doc_id`, tiêu đề tài liệu nguồn và phiên bản phát hành.  
  Về nguyên tắc sinh câu trả lời:  
  Thứ nhất, **Grounded tuyệt đối**: Thông tin trả về được trích xuất trực tiếp từ các chunk nằm trong context. Nhóm sử dụng cơ chế tổng hợp có kiểm soát từ ngữ liệu tác giả, giúp loại bỏ 100% rủi ro hallucination đối với các cam kết chính sách nhạy cảm.  
  Thứ hai, **Safe Abstention (Từ chối an toàn)**: Khi khách hỏi về những mặt hàng shop không bán như giày sneaker hay đồng hồ, hệ thống trả về status `insufficient_evidence` và nêu rõ giới hạn, không tự suy đoán ngày giao hay chính sách bảo hành."

---

## Slide 9: Xử lý Truy vấn Kết hợp (Mixed Queries) (Thời lượng: ~55 giây)

* **Nội dung thuyết minh:**  
  "Một trong những điểm sáng kỹ thuật của dự án là khả năng xử lý **Mixed Query** hoàn toàn tách bạch.  
  Giả sử khách gửi câu: *'Áo thun basic cotton có được đổi trả không, chốt 1 Áo thun basic cotton màu Xanh size M'*.  
  Nếu xử lý thông thường, RAG sẽ không biết tạo đơn, còn Order Flow sẽ bỏ qua câu hỏi đổi trả.  
  FastAPI của nhóm điều phối theo mô hình 2 pha:  
  - **Pha 1**: Bóc tách vế tri thức, RAG truy xuất chính sách `POL-RETURN-01`, trả lời thời hạn đổi trả 07 ngày kèm trích dẫn nguồn.  
  - **Pha 2**: Chuyển vế đặt hàng sang Chat Engine, đối chiếu danh mục SQLite, kiểm tra mã SKU `TSHIRT-BLU-M`, xác nhận giá 209.000₫ và kiểm tra tồn kho còn 12 chiếc.  
  Kết quả trả về trên giao diện gắn badge `⚡ Hỗn hợp (RAG + Đơn hàng)`. Phần tri thức có căn cứ rõ ràng, phần hành động được bảo vệ an toàn bởi nghiệp vụ backend."

---

## Slide 10: Re-Index & Cơ chế Vận hành Hot Rollback (Thời lượng: ~60 giây)

* **Nội dung thuyết minh:**  
  "Đề tài yêu cầu mô phỏng quy trình nâng cấp tài liệu trong vận hành thực tế. Nhóm đã xây dựng trọn vẹn kịch bản cập nhật từ phiên bản **v1.0 lên v1.1**:  
  - Ở phiên bản v1.0: Chính sách đổi trả quy định thời hạn **07 ngày**.  
  - Ở phiên bản v1.1: Cửa hàng mở rộng thời hạn đổi trả lên **14 ngày**.  
  Khi người quản trị (Admin) kích hoạt Re-index qua API hoặc giao diện demo, hệ thống sẽ:  
  1. Kiểm tra Admin Token và ghi nhận sự kiện vào `AuditLog`.  
  2. Nạp và kiểm tra mã băm bundle v1.1.  
  3. Sử dụng cơ chế **Atomic Swap** — ghi file tạm rồi thay thế nguyên tử con trỏ `artifacts/active_index.json`.  
  Nhờ con trỏ này, tất cả các tiến trình server lập tức nhận diện index mới mà **không cần khởi động lại ứng dụng**.  
  Khi hỏi lại: *'Thời hạn đổi trả là bao nhiêu ngày?'*, hệ thống trả lời ngay là **14 ngày** với citation hiển thị bản `v1.1`. Và khi bấm Rollback về v1.0, câu trả lời lập tức quay về **07 ngày** trong chưa đầy 1 giây."

---

## Slide 11: Nâng cấp Toàn diện AI Chatbot Engine (Thời lượng: ~60 giây)

* **Nội dung thuyết minh:**  
  "Bên cạnh RAG, điểm cộng nổi bật của nhóm là đã nâng cấp toàn diện bộ não AI Chatbot trong file `backend/app/chat_engine.py`, giải quyết triệt để 15 vấn đề thực tế thường gặp:  
  1. **Bóc tách thông tin KHÔNG NHÃN:** Khách chỉ cần nhắn tự nhiên: *'Nguyễn Văn An, 0901234567, 123 Lê Lợi Q1'*, bot tự động nhận diện chính xác Tên, Số điện thoại và Địa chỉ mà không cần tiền tố.  
  2. **Hiểu cách nói đời thường:** Khách gọi *'2c áo'*, *'chốt 2 cái'*, hay *'áo trắng size M'* (bỏ chữ 'thun'), hệ thống vẫn nhận diện đúng sản phẩm.  
  3. **Bảo toàn số lượng đa lượt:** Khách nhắn turn 1 lấy 2 bình giữ nhiệt, sang turn 2 chỉ gửi thông tin người nhận, bot không hề bị mất số lượng 2 ban đầu.  
  4. **Entity Disambiguation:** Tách riêng thông tin liên hệ trước khi đối chiếu catalog, không bao giờ nhầm chữ 'Bình' trong tên người nhận thành sản phẩm Bình giữ nhiệt.  
  5. **Hủy đơn an toàn:** Hỗ trợ lệnh hủy đơn (`cancel_pending`) khi khách đổi ý, xóa sạch trạng thái chờ để giải phóng phiên chat."

---

## Slide 12: Kết quả Đánh giá Thực nghiệm (Thời lượng: ~50 giây)

* **Nội dung thuyết minh:**  
  "Nhóm đã kiểm nghiệm toàn diện hệ thống thông qua các bộ đo lường định lượng độc lập:  
  - **Tập đánh giá RAG (21 cases authored):** Đạt **Hit@3: 100%**, **Recall@5: 97.92%**, **MRR: 0.9688**, tỷ lệ phân giải trích dẫn **Citation Resolution đạt 100%**, và tỷ lệ từ chối an toàn / chặn quyền trái phép đạt **100%**.  
  - **Bộ kiểm thử tự động (Unit & Integration Tests):**  
    - `tests/test_rag.py`: Đạt **29/29 tests PASS** (bảo vệ phân quyền, toàn vẹn bundle, query expansion).  
    - `tests/test_chatbot.py`: Đạt **23/23 tests PASS** (bảo vệ hội thoại đa lượt, bóc tách không nhãn, out-of-stock, idempotency, prompt injection và re-index API).  
    - Toàn bộ **52 ca kiểm thử** đều chạy trên cơ sở dữ liệu SQLite cô lập trong bộ nhớ tạm, thời gian thực thi dưới 2 giây.  
  - Nhóm cũng đã ghi nhận và phân tích chi tiết **5 trường hợp lỗi và near-miss** trong báo cáo `evaluation_report.md` cùng các biện pháp cải tiến tương ứng."

---

## Slide 13: Tổng kết & Định hướng Phát triển (Thời lượng: ~45 giây)

* **Nội dung kết luận:**  
  "Tóm lại, dự án của Group 7 đã đáp ứng trọn vẹn và vượt mức các yêu cầu đề ra của môn học RAG:  
  - Kế thừa vững chắc nền tảng thương mại từ môn LLM.  
  - Xây dựng pipeline RAG chuẩn chỉnh với phân quyền trước truy xuất, trích dẫn minh bạch và cơ chế Re-index / Rollback nóng.  
  - Nâng cấp AI Chatbot mượt mà, thân thiện với ngôn ngữ đời thường của người Việt.  
  Về mặt minh bạch kỹ thuật, nhóm nhận định phiên bản demo hiện dùng Lexical Hashed Vectorizer và Template synthesis nhằm ưu tiên tính ổn định tuyệt đối và tốc độ phản hồi cục bộ.  
  Khi triển khai môi trường sản xuất thực tế (Production), định hướng tiếp theo sẽ là tích hợp mô hình Neural Embedding đa ngôn ngữ như **BGE-M3**, kết nối hệ thống định danh doanh nghiệp SSO/OAuth2 và phân tán chỉ mục trên Redis Vector Store.  
  Em xin chân thành cảm ơn quý thầy cô và các bạn đã chú ý lắng nghe! Sau đây nhóm xin bước vào phần Demo trực tiếp."

---

## Hướng dẫn Trả lời Câu hỏi Phản biện (Q&A Defense Guide)

Dưới đây là các câu hỏi trọng tâm mà Hội đồng / Giám khảo thường chất vấn và câu trả lời chuẩn xác nhất cho nhóm:

### Câu 1: Tại sao nhóm dùng Lexical N-gram Vectorizer thay vì một mô hình Neural Embedding như BGE-M3 hay OpenAI text-embedding-3?
* **Cách trả lời:**  
  "Dạ thưa thầy/cô, đây là một quyết định kiến trúc có chủ đích cho phạm vi đồ án demo:  
  1. **Hiệu năng & Tự chủ cục bộ:** Bộ vectorizer băm n-gram từ/ký tự (1024 chiều) chạy hoàn toàn trên CPU tiêu chuẩn, độ trễ cực thấp (< 5ms), không đòi hỏi GPU đắt đỏ và không phụ thuộc vào kết nối mạng hay tiến trình Ollama cục bộ.  
  2. **Độ chính xác cao trên miền nghiệp vụ cụ thể:** Với 12 tài liệu và 31 chunks trong catalog của shop, kết hợp với cơ chế Topic Query Expansion, bộ vectorizer đạt Hit@3 100% và Recall@5 97.92%.  
  Nhóm hoàn toàn ý thức được giới hạn là lexical search có thể giảm độ chính xác nếu gặp các từ đồng nghĩa quá xa lạ, và trong kiến trúc ở file `src/rag.py`, nhóm đã thiết kế theo mẫu Adapter để có thể cắm trực tiếp mô hình BGE-M3 vào mà không cần thay đổi bất kỳ dòng code nào ở tầng Router hay API."

---

### Câu 2: Tại sao câu trả lời RAG lại dùng Template synthesis thay vì để LLM tự sinh câu trả lời tự do?
* **Cách trả lời:**  
  "Dạ thưa thầy/cô, trong lĩnh vực thương mại điện tử, các thông tin về **chính sách đổi trả, thời hạn bảo hành và bồi thường** là những cam kết pháp lý mang tính ràng buộc:  
  - Nếu để LLM tự do sinh lời tóm tắt, mô hình có thể gặp ảo giác (hallucination) dù tỷ lệ rất nhỏ — ví dụ đổi 'không áp dụng bảo hành' thành 'được bảo hành', hoặc bị ảnh hưởng bởi prompt injection từ câu chat của khách.  
  - Việc tổng hợp câu trả lời dựa trên trích xuất trực tiếp từ text chunk và gán citation chính xác giúp đảm bảo **độ tin cậy factual là 100%**, triệt tiêu hoàn toàn rủi ro bịa đặt.  
  Đây chính là mô hình *Constrained Grounded Generation* thường được áp dụng trong các hệ thống Q&A tài chính và pháp lý."

---

### Câu 3: Làm thế nào để chứng minh tài liệu nội bộ (Staff/Admin) không bị rò rỉ cho Khách hàng?
* **Cách trả lời:**  
  "Dạ thưa thầy/cô, nhóm chứng minh điều này qua 2 tầng:  
  1. **Tầng Retrieval (Pre-filtering):** Trong hàm `RAGIndex.retrieve()`, điều kiện kiểm tra vai trò được đặt ngay trước khi tính toán cosine similarity. Nếu vai trò là `customer`, toàn bộ các chunk có `access_level` là `staff` hoặc `admin` bị loại bỏ hoàn toàn khỏi không gian tìm kiếm, không hề xuất hiện trong candidate list.  
  2. **Tầng API & Tests:** Nhóm có ca kiểm thử tự động `test_customer_access_control_prefiltering` trong `test_rag.py` và ca `ST-05` trong evaluation runner. Khi khách hàng hỏi về mã giảm giá 20% của nhân viên hay quy trình camera WMS, hệ thống trả về status `access_denied`, mảng `citations` rỗng và không tiết lộ bất kỳ nội dung nào."

---

### Câu 4: Cơ chế Hot Rollback của Re-index hoạt động như thế nào và có an toàn khi có nhiều người truy cập cùng lúc không?
* **Cách trả lời:**  
  "Dạ thưa thầy/cô, cơ chế Hot Rollback hoạt động dựa trên **Atomic File Pointer**:  
  - Khi Admin gọi API re-index lên v1.1 hoặc rollback về v1.0, backend kiểm tra Admin Token, ghi `AuditLog` và tải bundle mới.  
  - Để cập nhật con trỏ `artifacts/active_index.json`, hệ thống ghi dữ liệu vào một file tạm có tên ngẫu nhiên UUID rồi thực hiện lệnh `os.replace()` nguyên tử của hệ điều hành. Lệnh này đảm bảo không bao giờ xảy ra tình trạng file bị đọc dở dang khi đang ghi.  
  - Mỗi khi một request RAG đến, hàm `get_active_rag_index()` kiểm tra con trỏ này, nếu thấy phiên bản bundle thay đổi thì tự động hoán đổi index trong bộ nhớ mà không cần khởi động lại tiến trình server."

---

### Câu 5: Hệ thống làm thế nào để đảm bảo RAG không tự ý thay đổi dữ liệu đơn hàng?
* **Cách trả lời:**  
  "Dạ thưa thầy/cô, sự an toàn này được bảo vệ bởi sự phân tách kiến trúc nghiêm ngặt:  
  - Module RAG (`src/rag.py`) là một thư viện thuần tính toán và tra cứu, hoàn toàn **không import SQLAlchemy Session hay kết nối database**. Nó chỉ nhận query văn bản và trả về dictionary tri thức.  
  - Tất cả các thao tác liên quan đến giỏ hàng, đơn hàng, cập nhật số lượng tồn kho đều phải đi qua module `chat_engine.py` và các API endpoint của FastAPI.  
  - Tại đây, hệ thống thực hiện validation độc lập: kiểm tra phiên đăng nhập hợp lệ, đối chiếu SKU trong database SQLite, kiểm tra số lượng tồn kho khả dụng và tính toán lại tổng tiền dựa trên giá niêm yết trong DB chứ không dựa vào con số do khách hàng hay RAG đưa ra."
