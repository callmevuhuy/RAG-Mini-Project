# Slide Deck: Mở rộng AI Live Commerce Order Assistant với Hệ thống RAG Phân Quyền & AI Chatbot Đa Lượt
**Nhóm thực hiện:** Group 7  
**Môn học:** Retrieval-Augmented Generation (RAG)  
**Thời lượng thuyết trình:** 10–12 phút + 3–5 phút Q&A  

---

## Slide 1: Trang tiêu đề (Title Slide)
- **Tiêu đề chính:** HỆ THỐNG RAG PHÂN QUYỀN & AI CHATBOT THƯƠNG MẠI ĐIỆN TỬ
- **Tiêu đề phụ:** Mở rộng AI Live Commerce Order Assistant từ mini-project LLM & Prompt Engineering
- **Thông điệp cốt lõi:** *"RAG tra cứu tri thức chính sách và catalog có nguồn trích dẫn; Database & Backend API độc quyền quyết định đơn hàng, giá bán và tồn kho."*
- **Thực hiện:** Group 7
- **Tech Stack:** React/Vite • FastAPI • SQLite • RAG Lexical Vectorizer • Chat Engine State Machine

---

## Slide 2: Bối cảnh & Đặt vấn đề — Từ LLM sang RAG
- **Kế thừa từ Project LLM:**
  - Nền tảng storefront React, API FastAPI, cơ sở dữ liệu SQLite (catalog, tồn kho, đơn hàng, audit log).
  - Khả năng trích xuất ý định mua hàng và tạo đơn nháp.
- **Vấn đề cốt lõi mà Project LLM trước đây chưa giải quyết được:**
  - Không có tri thức về chính sách bán hàng: Đổi trả, bảo hành, đồng kiểm, giao hàng, vệ sinh sản phẩm.
  - Dễ gặp ảo giác (hallucination) nếu hỏi các thông tin ngoài danh mục hoặc điều kiện bảo hành phức tạp.
  - Chưa có phân quyền truy cập thông tin giữa Khách hàng (Customer) và Nội bộ (Staff/Admin).
- **Mục tiêu của giai đoạn RAG:**
  - Bổ sung Knowledge Base tài liệu chuẩn hóa có cấu trúc.
  - Phân quyền dữ liệu trước khi truy xuất (Pre-filtering RBAC).
  - Trả lời grounded có citation kiểm chứng được, an toàn từ chối khi thiếu bằng chứng (safe abstention).

---

## Slide 3: Kiến trúc Tổng thể & Ranh giới Bảo mật (System Architecture)
- **Mô hình luồng yêu cầu (Request Flow):**
  - Trình duyệt (Browser) + Session Cookie $\rightarrow$ FastAPI Gateway (Kiểm tra Origin, Session, Role Token).
  - **Unified Router (`src/router.py`)** phân loại luồng:
    1. `knowledge_query` $\rightarrow$ RAG Index (Pre-filtered) $\rightarrow$ Grounded Answer + Citations.
    2. `order_action` $\rightarrow$ Chat Engine $\rightarrow$ SQLite Validation $\rightarrow$ Phản hồi/Tạo đơn nháp.
    3. `mixed` $\rightarrow$ Tách độc lập: RAG trả lời tri thức có trích dẫn + Chat Engine xử lý nghiệp vụ đơn hàng.
    4. `handoff` / `safety_adversarial` $\rightarrow$ Từ chối hoặc chuyển tiếp nhân viên an toàn.
- **Ranh giới an toàn then chốt:**
  - RAG là luồng **Read-Only**: Câu trả lời RAG tuyệt đối không được tự động ghi/sửa cơ sở dữ liệu.
  - SQLite là **Nguồn sự thật duy nhất (Single Source of Truth)** cho SKU, giá, tồn kho thực tế.
  - Token phân quyền được kiểm tra tại server (`DEMO_STAFF_TOKEN`, `DEMO_ADMIN_TOKEN`), client không thể tự phong quyền.

---

## Slide 4: Unified Router — Phân luồng Ý định Tự nhiên
- **Thách thức:** Tin nhắn người dùng trong thương mại rất đa dạng: hỏi chính sách, đặt hàng, kiểm tra giá/kho, hoặc kết hợp cả hai.
- **Giải pháp:** Bộ Router kết hợp Regex Heuristics và Heuristic Clause Splitting tiếng Việt:
  - Nhận diện các liên từ phân tách: `và`, `nhưng`, `rồi`, `với lại`, `ngoài ra`, dấu phẩy, dấu chấm hỏi.
  - Phân định rõ mệnh đề chứa tri thức (`knowledge clause`) và mệnh đề hành động (`action clause`).
- **Xử lý An toàn (Safety First):**
  - Phát hiện các mẫu câu tấn công prompt injection: *"Bỏ qua mọi quy tắc"*, *"Tiết lộ secret"*, *"Xóa mọi đơn hàng"*.
  - Chặn đứng ngay tại router, ghi nhận mã sự cố và trả về `status: access_denied` / `handoff` mà không gọi LLM hay RAG backend.

---

## Slide 5: Corpus & Ingestion — Xây dựng Knowledge Base Tái lập
- **Quy mô Corpus:**
  - 12 tài liệu Markdown có cấu trúc phân tầng (`data/corpus/`).
  - 31 chunks có ý nghĩa ngữ nghĩa, cắt theo tiêu đề Markdown H2.
- **Metadata bắt buộc trong Manifest (`corpus_manifest.json`):**
  - `doc_id`, `chunk_id`: Định danh duy nhất theo định dạng `{doc_id}#cNN`.
  - `source`, `title`, `author`, `version`: Đảm bảo nguồn gốc tài liệu (provenance).
  - `access_level`: Phân quyền rõ ràng (`public`, `staff`, `admin`). Tuyệt đối không cho phép giá trị mặc định là public nếu manifest thiếu trường.
- **Tính toàn vẹn của Index Bundle:**
  - Bundle lưu toàn bộ vector, chunk mapping và manifest meta.
  - Kiểm tra mã băm **SHA-256 integrity checksum** khi tải index để phát hiện sai lệch hoặc hư hỏng file.

---

## Slide 6: Phân quyền Đa tầng (Permission-Aware Retrieval & RBAC)
- **Nguyên tắc vàng:** **Pre-retrieval Role Filtering (Lọc quyền trước khi xếp hạng)**:
  - Nếu chỉ lọc kết quả ở bước cuối (hậu kiểm), tài liệu mật có thể đã lọt vào candidate list, cache hoặc ngữ cảnh LLM.
  - Hệ thống áp bộ lọc `chunk.access_level` ngay từ bước duyệt ứng viên:
    - `customer`: Chỉ được truy xuất tài liệu `public` (Catalog, Chính sách đổi trả, bảo hành public, FAQ).
    - `staff`: Truy xuất tài liệu `public` + `staff` (Quy trình nội bộ SOP, camera kho WMS, mã giảm giá nhân viên).
    - `admin`: Truy xuất toàn bộ tài liệu và có quyền kích hoạt re-index.
- **Xác thực Token Phía Backend:**
  - Header `X-User-Role` chỉ là lựa chọn giao diện demo.
  - Backend yêu cầu header bí mật `X-Demo-Role-Token` khớp với cấu hình server. Nếu sai hoặc thiếu $\rightarrow$ HTTP 403 Forbidden.

---

## Slide 7: Cơ chế Vectorizer & Retrieval
- **Lexical Hashed N-gram Vectorizer (1024 chiều):**
  - Vector hóa dựa trên tần suất n-gram từ và ký tự (term-frequency) kết hợp hàm băm Murmur-style.
  - Chuẩn hóa vector $L_2$ và đo độ tương đồng bằng Cosine Similarity.
  - **Ưu điểm thực tế:** Chạy hoàn toàn cục bộ, tốc độ phản hồi cực nhanh (< 5ms), dung lượng nhẹ, không phụ thuộc vào GPU hay tiến trình Ollama nền.
- **Tối ưu hóa Truy vấn (Topic Query Expansion):**
  - Tự động mở rộng từ khóa cho các câu hỏi nhiều điều kiện (Multi-condition) về chính sách đổi trả (`POL-RETURN`) và bảo hành (`POL-WARRANTY`).
  - Đảm bảo các section quan trọng (Thời hạn 7 ngày, Điều kiện tem mác, Trách nhiệm phí ship) luôn lọt vào Top-3 ranking.

---

## Slide 8: Grounded Generation & Citation Contract
- **Hợp đồng dữ liệu đầu ra chuẩn (API Response Contract):**
  ```json
  {
    "route": "knowledge_query",
    "status": "answered | insufficient_evidence | access_denied | handoff | error",
    "message": "Câu trả lời tiếng Việt có căn cứ từ tài liệu...",
    "citations": [
      {
        "chunk_id": "POL-RETURN-01#c01",
        "doc_id": "POL-RETURN-01",
        "source": "Chính sách Đổi trả và Hoàn tiền (v1.0)",
        "version": "1.0",
        "section": "Thời hạn đổi trả"
      }
    ],
    "missing_information": ""
  }
  ```
- **Nguyên tắc Grounding:**
  - Mọi thông tin trả về đều trích dẫn chính xác chunk nguồn.
  - **Safe Abstention (Từ chối an toàn):** Nếu câu hỏi về sản phẩm không kinh doanh (ví dụ: *giày sneaker*, *đồng hồ*) hoặc thông tin không có trong tài liệu $\rightarrow$ Trả về `insufficient_evidence`, không bịa đặt ngày giao hàng hay chính sách.

---

## Slide 9: Xử lý Truy vấn Kết hợp (Mixed Queries)
- **Tình huống thực tế:** Khách hàng nhắn câu phức hợp:  
  *"Áo thun basic cotton có được đổi trả không, chốt 1 Áo thun basic cotton màu Xanh size M"*
- **Cơ chế phân tách 2 pha:**
  1. **Pha 1 — Tri thức (Knowledge RAG):**
     - Router trích xuất vế: *"Áo thun basic cotton có được đổi trả không"*
     - RAG truy xuất tài liệu `POL-RETURN-01`, trả về quy định đổi trả trong 07 ngày kèm trích dẫn nguồn.
  2. **Pha 2 — Hành động (Order Flow):**
     - Router trích xuất vế: *"chốt 1 Áo thun basic cotton màu Xanh size M"*
     - Chat Engine xác thực SKU trong SQLite, kiểm tra tồn kho (còn 12 sản phẩm).
     - Nếu thiếu thông tin người nhận $\rightarrow$ Yêu cầu bổ sung; nếu đủ $\rightarrow$ Tạo đơn nháp `#DRAFT...`.
- **Kết quả:** Phản hồi hiển thị badge `⚡ Hỗn hợp (RAG + Đơn hàng)` với thông tin minh bạch, rõ ràng.

---

## Slide 10: Re-Index & Cơ chế Vận hành Hot Rollback
- **Kịch bản thực tế:** Cửa hàng cập nhật chính sách đổi trả từ phiên bản 1.0 lên 1.1:
  - *Chính sách v1.0:* Thời hạn đổi trả trong vòng **07 ngày**.
  - *Chính sách v1.1:* Thời hạn đổi trả mở rộng lên **14 ngày**.
- **Cơ chế Chuyển đổi Nóng (Atomic Hot Swap):**
  - Quản trị viên gọi API `POST /api/v1/rag/reindex?version=1.1` (kèm Admin Token).
  - Backend ghi nhận sự kiện vào `AuditLog`, xác thực bundle `index_bundle_v1_1.json`.
  - Thay thế nguyên tử file con trỏ `artifacts/active_index.json`.
  - Toàn bộ worker tự động nạp lại index mới mà **không cần khởi động lại server**.
- **Kiểm chứng Rollback:** Bấm rollback về v1.0 $\rightarrow$ Câu trả lời lập tức hoàn về 07 ngày, phiên bản citation hiển thị đúng `1.0`.

---

## Slide 11: Nâng cấp Toàn diện AI Chatbot Engine (`chat_engine.py`)
- **Giải quyết triệt để 15 Issue hội thoại thực tế:**
  1. **Bóc tách liên hệ KHÔNG NHÃN:** Khách nhắn *"Nguyễn Văn An, 0901234567, 123 Lê Lợi Q1"*, bot tự nhận diện đúng Tên, SĐT, Địa chỉ.
  2. **Số lượng tự nhiên:** Hiểu *"2c"*, *"2 cái"*, *"chốt 2"*, *"mua 1 đôi"*.
  3. **Bảo toàn số lượng đa lượt:** Khách nhắc lại tên sản phẩm ở lượt sau nhưng không nói số lượng $\rightarrow$ Số lượng không bị ghi đè hay mất mát.
  4. **Entity Disambiguation:** Tách riêng họ tên và địa chỉ đường phố trước khi so khớp Catalog SQLite, chống nhầm tên người (ví dụ: anh "Bình") thành sản phẩm (bình giữ nhiệt).
  5. **Hủy đơn an toàn (`cancel_pending`):** Khách đổi ý không mua nữa $\rightarrow$ Xóa sạch state chờ, không kẹt luồng hội thoại.

---

## Slide 12: Kết quả Đánh giá Thực nghiệm (Evaluation Suite)
- **Tập kiểm thử RAG (21 Cases tác giả):**
  - **Hit@3:** 100.0% • **Recall@5:** 97.92% • **MRR:** 0.9688
  - **Citation Metadata Resolution:** 100.0%
  - **Expected Answer Fact Match:** 96.43%
  - **Safe Abstention & Access Denied:** 100.0%
  - **Mixed Route & Query Split Accuracy:** 100.0%
- **Bộ Kiểm thử Tự động:**
  - `tests/test_rag.py`: **29/29 tests PASS** (Phân quyền, chunking, tampered bundle, query expansion, multi-condition).
  - `tests/test_chatbot.py`: **23/23 tests PASS** (Đa lượt, không nhãn, out-of-stock, idempotency, prompt injection, re-index).
  - Chatbot Multi-turn Evaluation (`eval/run_chatbot_evaluation.py`): **9/9 cases PASS (100%)**.
  - Inherited E-commerce Suite (`eval/run_evaluation.py`): **14/14 PASS**.
- **Phân tích 5 Near-misses:** Được khắc phục và có ca kiểm thử hồi quy độc lập bảo vệ.

---

## Slide 13: Tổng kết, Giới hạn Kỹ thuật & Hướng Phát triển
- **Thành tựu chính:**
  - Hoàn thành trọn vẹn tất cả mục tiêu của đồ án RAG: Ingestion, Pre-filtered Retrieval, Grounded Generation, Re-indexing và Phân quyền RBAC.
  - Nâng cấp trải nghiệm AI Chatbot thương mại điện tử mượt mà, thông minh và an toàn.
- **Tính minh bạch về giới hạn kỹ thuật (Technical Limitations):**
  - Hiện tại dùng Lexical N-gram Vectorizer (chạy local nhẹ); chưa dùng Neural Embedding sâu (như BGE-M3).
  - Token demo phục vụ môi trường cục bộ, chưa tích hợp hệ thống SSO/OAuth2 doanh nghiệp.
  - Câu trả lời RAG dùng Template synthesis từ chunk để triệt tiêu hoàn toàn rủi ro bịa đặt.
- **Định hướng mở rộng cho Production:**
  - Tích hợp mô hình Semantic Embedding đa ngôn ngữ (BGE-M3).
  - Kết nối Gateway SSO/IAM và phân tán chỉ mục với Redis Vector Store.
