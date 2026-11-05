# BÁO CÁO TỔNG THỂ DỰ ÁN RAG & AI LIVE COMMERCE ORDER ASSISTANT

## Hệ Thống Trợ Lý Đặt Hàng Thương Mại Điện Tử Thông Minh Tích Hợp RAG Phân Quyền & Chatbot Đa Lượt

**Đơn vị thực hiện:** Nhóm 7 (Group 7)
**Ngày cập nhật:** 05/11/2026
**Phiên bản báo cáo:** v2.0 (Bản Bàn giao Nghiệm thu Hoàn chỉnh)
**Phạm vi hệ thống:** Kế thừa toàn diện nền tảng E-commerce từ môn LLM, mở rộng Pipeline RAG phân quyền 3 cấp (Customer/Staff/Admin) có trích dẫn nguồn, và nâng cấp toàn diện AI Chatbot hội thoại tự nhiên tiếng Việt (P0, P1, P2).

---

## MỤC LỤC

1. [Giới Thiệu &amp; Bối Cảnh Dự Án](#1-giới-thiệu--bối-cảnh-dự-án)
2. [Ngăn Xếp Công Nghệ &amp; Kiến Trúc Hệ Thống](#2-ngăn-xếp-công-nghệ--kiến-trúc-hệ-thống)
3. [Dữ Liệu Tri Thức (Corpus), Cắt Đoạn (Chunking) &amp; Ingestion](#3-dữ-liệu-tri-thức-corpus-cắt-đoạn-chunking--ingestion)
4. [Mô Hình Vector Hóa (Embedding) &amp; Thuật Toán Tìm Kiếm](#4-mô-hình-vector-hóa-embedding--thuật-toán-tìm-kiếm)
5. [Cơ Chế Phân Quyền Đa Tầng (Pre-retrieval RBAC) &amp; Hot Rollback](#5-cơ-chế-phân-quyền-đa-tầng-pre-retrieval-rbac--hot-rollback)
6. [Grounded Generation &amp; Hợp Đồng Trích Dẫn (Citation Contract)](#6-grounded-generation--hợp-đồng-trích-dẫn-citation-contract)
7. [Nâng Cấp Toàn Diện AI Chatbot Đa Lượt (P0, P1, P2)](#7-nâng-cấp-toàn-diện-ai-chatbot-đa-lượt-p0-p1-p2)
8. [Nhật Ký Điều Tra &amp; Xử Lý Sự Cố Toàn Diện (Issue Log &amp; Resolution Ledger)](#8-nhật-ký-điều-tra--xử-lý-sự-cố-toàn-diện-issue-log--resolution-ledger)
9. [Kết Quả Đánh Giá Thực Nghiệm &amp; Đo Lường Định Lượng](#9-kết-quả-đánh-giá-thực-nghiệm--đo-lường-định-lượng)
10. [Đối Chiếu Chi Tiết Với Yêu Cầu Đề Tài (Guiding Documents Audit)](#10-đối-chiếu-chi-tiết-với-yêu-cầu-đề-tài-guiding-documents-audit)
11. [Giới Hạn Hệ Thống &amp; Lộ Trình Phát Triển Sản Xuất (Production Roadmap)](#11-giới-hạn-hệ-thống--lộ-trình-phát-triển-sản-xuất-production-roadmap)
12. [Hướng Dẫn Tái Lập Môi Trường &amp; Chạy Kiểm Thử Toàn Bộ](#12-hướng-dẫn-tái-lập-môi-trường--chạy-kiểm-thử-toàn-bộ)

---

## 1. Giới Thiệu & Bối Cảnh Dự Án

### 1.1. Bối cảnh kế thừa

Dự án là bước phát triển tiếp nối trực tiếp từ mini-project môn *LLM & Prompt Engineering*. Nhóm tiếp tục kế thừa và bảo toàn 100% ứng dụng thương mại điện tử hoàn chỉnh:

- **Giao diện người dùng (Storefront):** Xây dựng bằng React 19 và Vite, hỗ trợ duyệt sản phẩm, lọc danh mục, xem chi tiết biến thể SKU, giỏ hàng, đặt hàng và khung chat tương tác trực tuyến.
- **Backend API & Dữ liệu:** Sử dụng FastAPI kết hợp SQLite và SQLAlchemy ORM quản lý Danh mục sản phẩm (Catalog), Biến thể (Variants), Kho hàng (Inventory), Giỏ hàng (Cart), Đơn hàng (Orders), Nhật ký kiểm toán (Audit Logs) và Phiên làm việc (Demo Sessions).

### 1.2. Vấn đề đặt ra & Mục tiêu của RAG

Ở phiên bản LLM kế thừa ban đầu, hệ thống gặp 3 rào cản nghiêm trọng trong môi trường thương mại thực tế:

1. **Thiếu hụt tri thức phi cấu trúc:** Không thể trả lời các câu hỏi về chính sách đổi trả, bảo hành, biểu phí vận chuyển, cách vệ sinh bình giữ nhiệt do các dữ liệu này không nằm trong bảng cơ sở dữ liệu.
2. **Ảo giác cam kết (Hallucination Risk):** Mô hình ngôn ngữ tự do dễ bịa đặt các cam kết chính sách (như tự ý hứa hoàn tiền vô điều kiện, tự hẹn giờ giao hàng).
3. **Không có phân quyền dữ liệu:** Khách hàng có thể dò hỏi các thông tin quy trình nội bộ nhạy cảm (mã giảm giá của nhân viên, đối soát camera kho WMS).

### 1.3. Nguyên tắc ranh giới an toàn cốt lõi

Hệ thống thiết lập ranh giới bất biến giữa hai luồng nghiệp vụ:

- **Luồng Tra cứu Tri thức (RAG - Read Only):** RAG chỉ có quyền đọc tài liệu trong phạm vi vai trò cho phép, tổng hợp câu trả lời và trích dẫn bằng chứng kiểm chứng được. RAG **tuyệt đối không có quyền ghi dữ liệu**.
- **Luồng Thao tác Đơn hàng (Operational & Transactional Engine):** Toàn bộ quyết định về giá bán hiện thời, số lượng tồn kho khả dụng, tính hợp lệ của SKU và cập nhật trạng thái đơn hàng đều do **FastAPI và SQLite** thẩm định độc quyền.

---

## 2. Ngăn Xếp Công Nghệ & Kiến Trúc Hệ Thống

### 2.1. Ngăn xếp công nghệ chi tiết

| Thành phần                  | Công nghệ sử dụng                                             | Vai trò trong hệ thống                                                                                                                                                                |
| :---------------------------- | :---------------------------------------------------------------- | :--------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| **Frontend**            | React 19, Vite, TailwindCSS                                       | Giao diện cửa hàng trực tuyến, khung chat trợ lý mua sắm, thanh chuyển đổi vai trò (Role Switcher), hiển thị Badge định tuyến và khối trích dẫn nguồn (Citations). |
| **Backend Gateway**     | FastAPI, Uvicorn, Python 3.12                                     | Cung cấp RESTful API, kiểm tra bảo mật Origin/CORS, giới hạn tần suất (Rate Limiting), quản lý phiên (Session Cookie), kiểm tra token vai trò Staff/Admin.                  |
| **Cơ sở dữ liệu**   | SQLite 3, SQLAlchemy ORM                                          | Lưu trữ toàn bộ dữ liệu nghiệp vụ: Catalog, Variants, Inventory, Orders, OrderItems, ChatLog, AuditLog, ChatState.                                                               |
| **Unified Router**      | Heuristic Regex & Vietnamese Clause Splitting (`src/router.py`) | Phân loại tin nhắn thành 5 nhánh ý định; bóc tách mệnh đề phức hợp tiếng Việt cho truy vấn hỗn hợp (Mixed Query).                                                    |
| **RAG Core**            | Python thuần (`src/rag.py`)                                    | Quản lý vòng đời Ingestion, H2 Chunking, Local Hashed Vectorizer, Pre-retrieval RBAC, Topic Query Expansion, Grounded Generation.                                                   |
| **Lưu trữ Chỉ mục** | Atomic File Pointer & JSON Bundles (`artifacts/`)               | Bundle v1.0 và v1.1 đóng gói sẵn vector và metadata có mã hash SHA-256; hoán đổi tức thì bằng con trỏ `active_index.json`.                                              |
| **Chat Engine**         | Multi-turn State Machine (`backend/app/chat_engine.py`)         | Bóc tách thực thể không nhãn, chuẩn hóa tiếng Việt, khử nhập nhằng, kiểm tra tồn kho tức thì, gom slot lũy tiến.                                                      |

### 2.2. Sơ đồ luồng xử lý dữ liệu (Data & Control Flow)

```text
                                  NGƯỜI DÙNG / TRÌNH DUYỆT (REACT 19)
                                                  │
                                                  │ (Message + Session Cookie + Role Headers)
                                                  ▼
                                 FASTAPI API GATEWAY (backend/app/main.py)
                   ┌─────────────────────────────────────────────────────────────┐
                   │  - Kiểm tra Origin/CORS & Session hợp lệ                    │
                   │  - Rate Limiting (Tối đa 60 requests/phút)                   │
                   │  - Idempotency Cache (Khóa lặp client_message_id)           │
                   │  - Thẩm định quyền Backend Token (DEMO_STAFF / DEMO_ADMIN)  │
                   └──────────────────────────────┬──────────────────────────────┘
                                                  │
                                                  ▼
                               UNIFIED INTENT ROUTER (src/router.py)
                                                  │
         ┌───────────────────┬────────────────────┼───────────────────┬────────────────────┐
         │                   │                    │                   │                    │
         ▼                   ▼                    ▼                   ▼                    ▼
[safety_adversarial]     [handoff]        [knowledge_query]        [mixed]           [order_action]
(Chặn Prompt Inj.,      (Chuyển nhân         (Tra cứu RAG)    (Tách 2 mệnh đề:     (Hỏi giá, tồn kho,
 Xóa đơn, API Key)     viên tư vấn)               │           Knowledge + Order)    Tạo đơn nháp)
         │                   │                    │                   │                    │
         │                   │                    │        ┌──────────┴──────────┐         │
         │                   │                    ▼        ▼                     ▼         ▼
         │                   │         ┌───────────────────────┐             ┌─────────────────────┐
         │                   │         │ RAG ENGINE (src/rag)  │             │ CHAT ENGINE (SQLite)│
         │                   │         │ - Pre-retrieval RBAC  │             │ - Bóc tách Slot     │
         │                   │         │ - Query Expansion     │             │ - Khử nhập nhằng    │
         │                   │         │ - Local Vectorizer    │             │ - Check Tồn kho     │
         │                   │         │ - Grounded Answer     │             │ - Tạo Đơn Nháp      │
         │                   │         └──────────┬────────────┘             └──────────┬──────────┘
         │                   │                    │                                     │
         └───────────────────┴────────────────────┼─────────────────────────────────────┘
                                                  │
                                                  ▼
                                      ĐÓNG GÓI JSON PHẢN HỒI
                       (Status + Message + Citations + Order Details + Action)
                                                  │
                                                  ▼
                                       GHI NHẬN AUDIT & CHATLOG
                             (Tuyệt đối không lưu raw PII vào nhật ký)
```

---

## 3. Dữ Liệu Tri Thức (Corpus), Cắt Đoạn (Chunking) & Ingestion

### 3.1. Cấu trúc tập dữ liệu mẫu (Knowledge Corpus)

Knowledge Base được thiết kế gồm **12 tài liệu Markdown** chuẩn mực, chia thành **31 chunks** bao phủ toàn diện nghiệp vụ của cửa hàng Group 7:

```
data/corpus/
├── CAT-TSHIRT-01.md      # Áo thun basic cotton: Thông số kỹ thuật, chất liệu, tính năng (3 chunks, public)
├── CAT-BOTTLE-01.md      # Bình giữ nhiệt Everyday: Cấu tạo, dung tích, lưu ý an toàn (3 chunks, public)
├── CAT-COFFEE-01.md      # Cà phê rang xay Đà Lạt: Nguồn gốc, phương pháp rang, quy cách (2 chunks, public)
├── CAT-SIZING-01.md      # Hướng dẫn chọn size áo chuẩn theo chiều cao, cân nặng (2 chunks, public)
├── POL-SHIPPING-01.md    # Chính sách Giao hàng & Đồng kiểm ngoại quan (3 chunks, public)
├── POL-WARRANTY-01.md    # Chính sách Bảo hành & Điều kiện loại trừ hư hỏng (3 chunks, public)
├── POL-RETURN-01.md      # Chính sách Đổi trả và Hoàn tiền v1.0 (3 chunks, public)
├── FAQ-ORDER-01.md       # FAQ Quy trình đặt hàng, hủy đơn, xử lý giao thiếu kiện (3 chunks, public)
├── FAQ-CARE-01.md        # FAQ Hướng dẫn vệ sinh và khử mùi bình giữ nhiệt (2 chunks, public)
├── INT-STAFF-SOP-01.md   # [NỘI BỘ] Quy trình nhân viên đối soát camera kho WMS (3 chunks, staff)
├── INT-DISCOUNT-01.md    # [NỘI BỘ] Quy định chính sách chiết khấu & Mã nhân viên STAFF20 (3 chunks, staff)
└── INT-ADMIN-OPS-01.md   # [QUẢN TRỊ] Hướng dẫn vận hành Re-index & Phục hồi hệ thống (3 chunks, admin)
```

### 3.2. Chuẩn hóa Manifest & Quy trình Ingestion An toàn

Toàn bộ tài liệu được quản lý qua file [`data/corpus/corpus_manifest.json`](file:///D:/VSCode/Project/RAG/data/corpus/corpus_manifest.json). Mỗi mục bắt buộc phải khai báo đầy đủ 6 trường metadata:
`doc_id`, `filename`, `title`, `version`, `access_level`, `author`.

Hàm [`build_index_bundle()`](file:///D:/VSCode/Project/RAG/src/rag.py#L357-L450) thực thi các chốt kiểm soát an toàn nghiêm ngặt:

1. **Phòng chống Path Traversal:** Xác thực đường dẫn file tuyệt đối không được thoát khỏi thư mục gốc `data/corpus/`.
2. **Chống trùng lặp & Rỗng:** Từ chối ngay nếu phát hiện trùng `doc_id`, trùng `filename` hoặc file rỗng.
3. **Mã băm nguồn (Source SHA-256):** Tính toán và lưu trữ mã băm cho từng file văn bản để kiểm chứng tính nguyên bản.

### 3.3. Phương pháp cắt đoạn ngữ nghĩa Markdown H2 (Semantic Chunking)

Hàm [`chunk_document()`](file:///D:/VSCode/Project/RAG/src/rag.py#L315-L355) thực hiện cắt đoạn có cấu trúc:

- **Phân rã theo tiêu đề cấp 2 (`^##\s+`):** Không cắt máy móc theo số lượng từ hay số ký tự cố định để tránh làm đứt gãy ý nghĩa của câu hoặc bảng biểu. Mỗi đề mục H2 tạo thành một đơn vị ngữ nghĩa độc lập.
- **Định danh Chunk ID duy nhất:** Sinh mã theo chuẩn `{doc_id}#c{index:02d}` (ví dụ: `POL-RETURN-01#c01`, `INT-DISCOUNT-01#c02`).
- **Gắn nhãn Metadata toàn diện:** Mỗi chunk kế thừa toàn bộ `doc_id`, `source`, `version`, `access_level`, `section` và `char_offset` (vị trí ký tự bắt đầu trong file gốc phục vụ kiểm toán).

---

## 4. Mô Hình Vector Hóa (Embedding) & Thuật Toán Tìm Kiếm

### 4.1. Kiến trúc Deterministic Hashed Embedder

Nhóm triển khai bộ vectorizer băm n-gram cục bộ có tính tái lập cao ([`DeterministicEmbedder`](file:///D:/VSCode/Project/RAG/src/rag.py#L96-L148)):

- **Không gian 1024 chiều cố định:** Ánh xạ từ khóa và n-gram vào mảng 1024 phần tử thông qua thuật toán băm xác định `md5(token) % 1024`.
- **Tách từ đa tầng (Multi-level Tokenization):**
  1. *Word tokens:* Tách các từ đơn sau khi đã chuẩn hóa bỏ dấu tiếng Việt (Unicode NFD).
  2. *Character Trigrams:* Đối với các từ có độ dài $\ge 4$ ký tự, sinh thêm các chuỗi con 3 ký tự (ví dụ: `cotton` $\rightarrow$ `cot`, `ott`, `tto`, `ton`) giúp tăng khả năng tìm kiếm gần đúng (fuzzy) và chống lỗi gõ phím.
- **Trọng số thực thể (Token Weighting):** Gán trọng số x3.0 cho các token chứa mã SKU hoặc thông số kỹ thuật (như `TSHIRT-BLU-M`, `500ml`, `220gsm`).
- **Làm mượt tần suất & Chuẩn hóa $L_2$:** Tần suất xuất hiện được tính theo $\ln(1 + \text{count})$ và chia cho chuẩn độ dài vector $\|v\|_2 = 1.0$.

### 4.2. Độ tương đồng Cosine & Topic Query Expansion

- **Cosine Similarity:** Do vector đã được chuẩn hóa độ dài đơn vị 1.0, độ tương đồng ngữ cảnh được tính toán trực tiếp bằng tích vô hướng (Dot Product) với tốc độ tức thì (< 5ms trên CPU thông thường).
- **Topic Query Expansion (Mở rộng từ khóa theo chủ đề):** Khắc phục điểm yếu của lexical search khi người dùng hỏi các câu hỏi phức tạp nhiều điều kiện. Khi phát hiện các chủ đề như *chính sách đổi trả, chi phí vận chuyển, vệ sinh bình giữ nhiệt*, hệ thống tự động bổ sung từ khóa nghiệp vụ chuyên sâu vào vector truy vấn nhằm kéo các section then chốt vào Top-k ranking.

---

## 5. Cơ Chế Phân Quyền Đa Tầng (Pre-retrieval RBAC) & Hot Rollback

### 5.1. Nguyên tắc Pre-retrieval Role Filtering (Lọc trước khi tìm kiếm)

Hệ thống kiên quyết áp dụng nguyên tắc bảo mật: **Lọc quyền truy cập TRƯỚC KHI xếp hạng (Ranking)** tại hàm [`RAGIndex.retrieve()`](file:///D:/VSCode/Project/RAG/src/rag.py#L202-L260):

```python
allowed_levels = {
    "customer": {"public"},
    "staff":    {"public", "staff"},
    "admin":    {"public", "staff", "admin"}
}.get(user_role.lower(), {"public"})

# Bộ lọc cứng: Các chunk vượt quyền bị loại bỏ hoàn toàn khỏi không gian tìm kiếm
if chunk.access_level not in allowed_levels:
    continue
```

*Lợi ích an ninh:* Tránh hoàn toàn nguy cơ tài liệu mật của nhân viên hoặc cấu hình quản trị bị lọt vào danh sách ứng viên (candidate pool), bộ nhớ đệm (cache) hoặc ngữ cảnh prompt của mô hình ngôn ngữ.

### 5.2. Thẩm định quyền qua Token Backend (Server-side Role Gate)

- Giao diện người dùng có thanh Role Switcher chỉ đóng vai trò công cụ mô phỏng demo.
- Backend FastAPI tại [`resolve_demo_role()`](file:///D:/VSCode/Project/RAG/backend/app/main.py#L121-L148) thẩm định quyền bắt buộc thông qua header `X-Demo-Role-Token`:
  - Khách hàng (`customer`): Vai trò mặc định, không cần token, chỉ xem tài liệu `public`.
  - Nhân viên (`staff`): Bắt buộc có token khớp với `DEMO_STAFF_TOKEN` cấu hình trên server (mặc định demo: `demo_staff_token`).
  - Quản trị viên (`admin`): Bắt buộc có token khớp với `DEMO_ADMIN_TOKEN` (mặc định demo: `demo_admin_token`).
- Sử dụng hàm `secrets.compare_digest` để chống tấn công so sánh chuỗi theo thời gian (Timing Attacks). Nếu thiếu token hoặc sai token, hệ thống lập tức từ chối với mã lỗi **HTTP 403 Forbidden**.

### 5.3. Cơ chế Hot Swap & Zero-Downtime Rollback (< 1 giây)

Dự án cung cấp cơ chế nâng cấp phiên bản chỉ mục RAG trong thời gian thực thông qua API `POST /api/v1/rag/reindex?version=...`:

- **Đóng gói Bundle độc lập:** `artifacts/index_bundle.json` (Corpus v1.0) và `artifacts/index_bundle_v1_1.json` (Corpus v1.1). Cả hai bundle đều mang mã kiểm tra toàn vẹn SHA-256.
- **Con trỏ nguyên tử (Atomic Pointer):** Trạng thái phiên bản hoạt động được quản lý qua file `artifacts/active_index.json`. Khi Admin kích hoạt Re-index hoặc Rollback, backend ghi file tạm UUID rồi thực hiện lệnh `os.replace()` nguyên tử của hệ điều hành.
- **Hot Reload không cần khởi động lại:** Tất cả các worker trên cùng máy chủ khi phục vụ request kế tiếp sẽ tự động phát hiện con trỏ thay đổi và nạp lại index bundle tương ứng trong vòng chưa đầy **0.5 giây**.
- **Audit Logging:** Mọi thao tác Re-index và Rollback đều được ghi vết tự động vào bảng `AuditLog` gồm thời gian, session ID của Admin, phiên bản cũ và phiên bản mới.

---

## 6. Grounded Generation & Hợp Đồng Trích Dẫn (Citation Contract)

### 6.1. Hợp đồng phản hồi chuẩn hóa (JSON Contract)

Mọi phản hồi từ RAG Engine tại hàm [`generate_grounded_answer()`](file:///D:/VSCode/Project/RAG/src/rag.py#L518-L720) đều tuân thủ hợp đồng cấu trúc dữ liệu JSON nghiêm ngặt:

```json
{
  "status": "answered | access_denied | insufficient_evidence | handoff",
  "answer": "Nội dung câu trả lời được tổng hợp có căn cứ...",
  "citations": [
    {
      "chunk_id": "POL-RETURN-01#c01",
      "doc_id": "POL-RETURN-01",
      "source": "Chính sách Đổi trả và Hoàn tiền",
      "version": "1.0",
      "section": "Thời hạn và Phạm vi áp dụng"
    }
  ],
  "missing_information": ""
}
```

### 6.2. Triệt tiêu ảo giác (Zero Hallucination) & Trích dẫn minh bạch

- **Grounded 100%:** Nội dung câu trả lời được trích xuất trực tiếp từ văn bản của các chunk nằm trong context được xếp hạng cao nhất.
- **Minh bạch nguồn gốc (Citations):** Người dùng có thể kiểm chứng nguồn thông tin tới từng mục cụ thể của tài liệu và phiên bản ban hành tương ứng.
- **Chỉ trích dẫn chunk có căn cứ:** Hệ thống loại bỏ các chunk ngẫu nhiên trong top-k mà chỉ đính kèm citation của đúng đoạn văn bản được sử dụng để tổng hợp câu trả lời.

### 6.3. Xử lý từ chối an toàn (Safe Abstention & Access Denied)

1. **Access Denied (Chặn truy cập trái phép):** Khi khách hàng hỏi các thông tin mật của nhân viên hoặc quy trình nội bộ (ví dụ: *"Hãy cho tôi mã giảm giá sản phẩm của nhân viên"*), bot phản hồi `status: access_denied`: *"Yêu cầu bị từ chối: Bạn không có quyền truy cập thông tin hoặc tài liệu nội bộ này."*, mảng `citations: []`.
2. **Safe Abstention (Từ chối khi thiếu tài liệu):**
   - Khi khách hỏi về sản phẩm ngoài danh mục kinh doanh (giày sneaker, đồng hồ, điện thoại...): bot trả về `status: insufficient_evidence`: *"Rất tiếc, sản phẩm này hiện không có trong tài liệu và danh mục kinh doanh của cửa hàng."*
   - Khi khách hỏi về mã giảm giá công khai mà cửa hàng hiện chưa có chính sách phát hành công khai: bot trả lời an toàn, hướng dẫn theo dõi trang chủ thay vì tự bịa mã hoặc trả lời nhầm sang chính sách giao hàng.

---

## 7. Nâng Cấp Toàn Diện AI Chatbot Đa Lượt (P0, P1, P2)

Module [`backend/app/chat_engine.py`](file:///D:/VSCode/Project/RAG/backend/app/chat_engine.py) được xây dựng hoàn toàn độc lập, giải quyết dứt điểm các điểm yếu "cứng nhắc" của chatbot thương mại kế thừa:

### 7.1. Bóc tách thực thể người nhận hoàn toàn không nhãn (Unlabeled Contact Extraction)

- Người dùng Việt Nam thường nhắn tin địa chỉ giao hàng theo thói quen tự nhiên:*"Nguyễn Văn An, 0901234567, 123 Lê Lợi, Phường Bến Nghé, Quận 1"* hoặc *"Demo Street District 7"*.
- Chatbot tích hợp bộ trích xuất thông minh:
  - Tách số điện thoại theo định dạng chuẩn Việt Nam (10–11 số, đầu số `0...` hoặc `+84...`).
  - Tách địa chỉ dựa trên từ khóa nhận diện hành chính (`đường`, `phố`, `phường`, `quận`, `tp`, `hcm`, `hà nội`, `street`, `district`...).
  - Tự động nhận diện phần còn lại làm Họ tên người nhận mà **không bắt buộc người dùng phải gõ các tiền tố nhãn `Tên:`, `SĐT:`, `Địa chỉ:`**.

### 7.2. Cơ chế Khử nhập nhằng thực thể (Entity Disambiguation)

Khi khách hàng gửi tin nhắn chứa cả tên người nhận và sản phẩm (ví dụ: *"Bình giữ nhiệt đó gửi cho Trần Bình, 0987654321..."*):

- Hệ thống trích xuất và loại bỏ phần thông tin liên lạc (Họ tên: `Trần Bình`) ra khỏi câu chat trước.
- Phần văn bản còn lại (*residual text*) mới được đưa vào đối chiếu với danh mục Catalog SQLite. Cơ chế này loại bỏ hoàn toàn lỗi nhận nhầm chữ "Bình" trong tên người thành "Bình giữ nhiệt".

### 7.3. Tự động chốt biến thể duy nhất & Giải quyết vòng lặp xác nhận (Issue 15)

- Trong trường hợp thuộc tính khách chọn chỉ tương ứng với **duy nhất 1 biến thể SKU khả dụng** (ví dụ: Bình giữ nhiệt màu Đen chỉ có duy nhất loại dung tích 750ml): bot lập tức xác định chính xác biến thể đó để tạo đơn nháp mà không bắt khách phải trả lời lại câu hỏi dung tích.
- Bổ sung nhận diện linh hoạt các từ khóa xác nhận tự nhiên của người dùng (*"yes"*, *"ok"*, *"đúng rồi"*, *"chuẩn rồi"*...).

### 7.4. Kiểm tra tồn kho trước khi yêu cầu thông tin nhận hàng (Issue 10)

- Đảo ngược thứ tự xử lý: Đưa bước đối chiếu tồn kho lên ngay sau khi xác định được biến thể SKU.
- Nếu sản phẩm hoặc phân loại đã hết hàng (ví dụ: Áo thun màu Hồng size S có tồn kho bằng 0): bot lập tức thông báo hết hàng và gợi ý các phân loại còn hàng, tuyệt đối không bắt khách điền thông tin người nhận một cách vô ích.

### 7.5. Bảo toàn số lượng đơn nháp đa lượt khi nhắc lại sản phẩm (Issue 14, 16)

- **State Machine gom slot lũy tiến:** Khi khách chốt số lượng ở Turn 1 (*"2 bình giữ nhiệt màu trắng"*) và bổ sung địa chỉ ở Turn 2 nhưng nhắc lại tên sản phẩm (*"bình giữ nhiệt đó gửi cho..."*): hệ thống bảo toàn nguyên vẹn số lượng `2`, không bị reset về `1`.
- **Thông báo tạo đơn nháp đầy đủ:** Khi đơn nháp `#DRAFT...` được tạo thành công, bot phản hồi đầy đủ: Tên sản phẩm, chi tiết biến thể (màu sắc, kích cỡ, dung tích), số lượng, tổng tiền và đầy đủ thông tin người nhận.

### 7.6. Hỗ trợ đổi ý và hủy đơn nháp an toàn (`cancel_pending`)

Khi khách đang trong luồng bổ sung thông tin nhưng đổi ý nhắn: *"Thôi mình không mua nữa, hủy đơn giúp mình"*:

- Hệ thống nhận diện ý định hủy thông qua tập từ khóa phong phú (`thôi không mua`, `hủy đơn`, `đổi ý rồi`...).
- Xóa sạch trạng thái `ChatState` đang chờ và phản hồi lịch sự, giải phóng phiên hội thoại an toàn mà không làm kẹt luồng đặt hàng.

---

## 8. Nhật Ký Điều Tra & Xử Lý Sự Cố Toàn Diện (Issue Log & Resolution Ledger)

Bảng tổng hợp chi tiết toàn bộ **19 issues kỹ thuật** phát hiện trong quá trình kiểm thử thực tế người dùng và giải pháp khắc phục đã triển khai:

| Mã Issue          | Tình huống người dùng & Hiện tượng lỗi ban đầu                                                                                                                | Nguyên nhân gốc rễ (Root Cause)                                                                                                                                       | Giải pháp kỹ thuật đã xử lý                                                                                                                                                              | Ca kiểm thử bảo vệ                                                         |
| :----------------- | :----------------------------------------------------------------------------------------------------------------------------------------------------------------------- | :------------------------------------------------------------------------------------------------------------------------------------------------------------------------ | :----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- | :----------------------------------------------------------------------------- |
| **Issue 2**  | Khách hỏi: *"Còn bao nhiêu cái áo thun trắng size M trong kho vậy"* ➔ Bị handoff sang nhân viên.                                                           | Router regex thiếu nhận diện mẫu câu hỏi số lượng tồn kho tự nhiên `còn bao nhiêu ... trong kho`.                                                         | Bổ sung `r"\bcon\s+bao\s+nhieu\b"`, `r"\btrong\s+kho\b"` vào `ORDER_READ_PATTERNS` và xử lý nhánh `check_stock`.                                                                   | `test_natural_stock_query`                                                   |
| **Issue 3**  | Khách hỏi chung: *"Shop có áo thun không"*, *"Shop có bình giữ nhiệt không"* ➔ Không nhận diện được sản phẩm.                                     | Thiếu mẫu câu hỏi tổng quát dạng `shop có / shop còn / bên mình có`.                                                                                        | Bổ sung pattern `r"\b(?:shop\|ben\s+minh)\s+(?:co\|con)\b"` và trích xuất danh mục đối chiếu SQLite.                                                                                     | `test_natural_product_availability_and_stock_queries`                        |
| **Issue 4**  | Khách hỏi danh mục loại: *"Shop còn những loại cà phê nào"* ➔ Phản hồi chưa đầy đủ thông tin từng loại.                                           | Chưa có nhánh chuyên biệt tổng hợp danh sách phân loại (variants) khi hỏi `những loại / các loại`.                                                       | Thêm nhận diện `is_asking_all_types`, duyệt qua toàn bộ variants và trả về chi tiết tên, giá, tồn kho từng loại.                                                                | `test_natural_product_availability_and_stock_queries`                        |
| **Issue 5**  | Khách tìm tư vấn chung: *"Tôi đang tìm cà phê"*, *"Đang tìm bình"* ➔ Không nhận diện được ý định.                                              | Router và chat engine chỉ xử lý câu mua hoặc hỏi giá/tồn kho cụ thể.                                                                                           | Thêm nhánh `is_discovery`, giới thiệu tổng quan công năng sản phẩm cùng khoảng giá niêm yết (từ min đến max).                                                                 | `test_natural_product_availability_and_stock_queries`                        |
| **Issue 6**  | Khách hỏi sản phẩm không kinh doanh: *"Shop có áo khoác không"* ➔ Phản hồi lỗi hoặc nhầm lẫn sang sản phẩm khác.                                    | Đối chiếu catalog rỗng (`candidates == []`) chưa có thông điệp hướng dẫn rõ ràng.                                                                         | Báo lịch sự shop chưa có sản phẩm này và gợi ý danh mục sản phẩm hiện có để khách tham khảo.                                                                                 | `test_natural_product_availability_and_stock_queries`                        |
| **Issue 7**  | Khách chọn tổ hợp thuộc tính không tồn tại: *"Bình giữ nhiệt Xanh bạc hà 750ml"* ➔ Bot im lặng hoặc lỗi matching.                                    | Xanh bạc hà chỉ có ở 500ml, còn 750ml chỉ có Đen và Kem (thuộc tính xung đột chéo).                                                                        | Phân tích tập con `matching_sub`, chỉ rõ tổ hợp không tồn tại và gợi ý từng phân loại thực tế còn hàng.                                                                    | `test_natural_product_availability_and_stock_queries`                        |
| **Issue 8**  | Nhầm lẫn địa chỉ tiếng Anh (*"Demo Street"*) hoặc tên người thành tên sản phẩm cần mua.                                                                 | Bộ trích xuất contact thông thường chỉ nhận diện đường phố tiếng Việt có tiền tố `"đường"`, `"phố"`.                                            | Cải tiến `extract_contact_info` nhận diện các từ khóa đường phố quốc tế/không nhãn và tách riêng residual text.                                                              | `test_order_guidance_no_demo_notice_and_street_address_extraction`           |
| **Issue 9**  | Xuất hiện câu nhắc nhở demo: *"Chỉ dùng thông tin giả cho demo nhé."* gây khó chịu cho trải nghiệm người dùng.                                       | Dư thừa chuỗi hướng dẫn demo cứng trong template câu trả lời chatbot.                                                                                           | Loại bỏ triệt để cảnh báo demo khỏi prompt và toàn bộ phản hồi của `chat_engine.py` cũng như storefront.                                                                       | `test_order_guidance_no_demo_notice_and_street_address_extraction`           |
| **Issue 10** | Khách chọn biến thể hết hàng (*"áo thun hồng size S"* - tồn kho = 0) ➔ Bot vẫn hỏi tên/sđt/địa chỉ rồi mới báo lỗi.                               | Kiểm tra tồn kho bị đặt sau bước thu thập thông tin người nhận.                                                                                               | Đưa kiểm tra tồn kho lên ngay sau khi xác định được variant; nếu `available <= 0` lập tức báo hết hàng và gợi ý phân loại còn hàng.                                    | `test_out_of_stock_variant_selection`                                        |
| **Issue 11** | Khách hỏi giảm giá: *"Mua 3 áo thun trắng size M có giảm giá không"* ➔ Bot lặp lại chuỗi giá 2 lần (`199,000₫, 199,000₫`).                         | Nhánh `check_price` ghép nối chuỗi giá đơn và chuỗi giá tổng bị trùng lặp.                                                                                | Tái cấu trúc nhánh chiết khấu: tính chính xác tổng giá trị đơn hàng (3 × 199.000₫ = 597.000₫) và khẳng định chính sách bán đúng giá niêm yết.                      | `test_discount_inquiry_for_order`                                            |
| **Issue 12** | Tìm kiếm sản phẩm storefront không ra kết quả khi gõ tiếng Việt có dấu hoặc viết tắt (*"áo"*, *"bình"*, *"cà phê"*).                            | Backend SQLite so khớp `LIKE '%q%'` phân biệt dấu (accent-sensitive).                                                                                               | Bổ sung hàm chuẩn hóa Unicode NFD `engine_norm()` cho endpoint `/api/v1/products?q=...` lọc không phân biệt hoa thường và dấu tiếng Việt.                                      | `test_vietnamese_accent_insensitive_product_search`                          |
| **Issue 13** | Khách gọi đời thường: *"Mua 2 cái áo trắng size M"* ➔ Báo không tìm thấy sản phẩm; Turn 2 khách nhắn lại bị handoff.                               | Từ khóa bắt buộc chữ `"thun"`; câu chat chỉ có `"áo"` nên `candidates == []`; Turn 2 không có pending order nên router handoff.                        | Cho phép từ `"áo"` kết hợp thuộc tính màu/size nhận diện `Áo thun basic cotton` (có danh sách loại trừ an toàn); bảo toàn pending state.                                   | `test_issue13_colloquial_apparel_order_and_multi_turn`                       |
| **Issue 14** | Khách hỏi: *"Shop còn áo màu xanh không?"* ➔ Bot báo shop chưa có sản phẩm này.                                                                           | Từ khóa không khớp do thiếu từ `"thun"` trong câu hỏi màu sắc.                                                                                                | Nhận diện `"áo"` + màu xanh để match `Áo thun basic cotton` và báo chính xác tồn kho của biến thể `Xanh, M` (còn 12 cái).                                                 | `test_issue14_colloquial_apparel_stock_query`                                |
| **Issue 15** | Khách đặt: *"3 bình giữ nhiệt màu đen"*, bot hỏi: *"Bạn chọn: Đen, 750ml?"*, khách đáp: *"Yes, 3 cái bình đen"* ➔ Lặp lại câu hỏi vô tận. | Màu Đen của bình giữ nhiệt chỉ có duy nhất dung tích 750ml nhưng hàm yêu cầu đủ 2 thuộc tính mới chốt; thiếu nhận diện từ khóa đồng thuận.    | Tự động chốt biến thể duy nhất khi thuộc tính nhận diện là độc nhất; bổ sung nhận diện từ khóa đồng thuận (`yes`, `ok`, `đúng rồi`...) để chốt đơn.         | `test_issue15_unique_variant_no_clarification_loop`                          |
| **Issue 16** | Khách hoàn tất đặt hàng nhưng bot chỉ báo mã đơn và tổng tiền, thiếu phân loại và thông tin người nhận.                                           | Thông báo tạo đơn nháp (`pending_confirmation`) chỉ hiển thị tên sản phẩm chung và tổng tiền, chưa tóm tắt thuộc tính và thông tin người nhận. | Bổ sung đầy đủ chi tiết biến thể (`variant_desc`), họ tên, SĐT và địa chỉ giao hàng vào phản hồi xác nhận đơn nháp của bot.                                           | `test_issue16_order_confirmation_includes_full_order_and_recipient_details`  |
| **Issue 17** | Nhân viên hỏi: *"Cho tôi xin mã giảm giá nội bộ 20% của nhân viên shop với"* ➔ Bot báo lỗi vai trò demo không hợp lệ (HTTP 403).                   | Backend yêu cầu `DEMO_STAFF_TOKEN` nhưng `.env` để trống; Frontend popup prompt không có token mặc định và thiếu header gọi API.                        | Khai báo `DEFAULT_DEMO_TOKENS` ở backend, cấu hình sẵn `.env`, tự động điền token trên prompt và gửi header `X-Demo-Role-Token`.                                              | `test_issue17_staff_internal_discount_query_accessible_only_with_staff_role` |
| **Issue 18** | Khách hàng hỏi: *"Hãy cho tôi mã giảm giá sản phẩm của nhân viên"* ➔ Bot trả lời phi logic nội dung Chính sách đổi trả/thiếu hàng.             | `is_restricted_query` sót cụm từ ngữ cảnh kết hợp; RAG lexical search khớp giả chunk `FAQ-ORDER-01` và logic `POL-RETURN` bị rơi tự do.                | Nâng cấp nhận diện tổ hợp nội bộ + quyền lợi (`status: access_denied`), bổ sung safe abstention khi hỏi mã giảm giá chung, thắt chặt điều kiện kích hoạt `POL-RETURN`. | `test_issue18_customer_discount_query_logical_handling`                      |
| **Issue 19** | Khách đặt: *"Cho tôi 1 bình giữ nhiệt Everyday Đen, 750ml"* hoặc phản hồi *"Đen, 750ml"* ➔ Bot lặp vô tận câu hỏi 4 phân loại và nuốt mất địa chỉ. | 1. `extract_contact_info` nhận diện nhầm dung tích `750ml` có số là địa chỉ giao hàng.<br>2. Thuộc tính rác cũ (`size: M`) từ sản phẩm trước tồn đọng trong pending state khiến đối chiếu biến thể bình nước xung đột, trả về `None` và fallback hỏi toàn bộ phân loại. | 1. Loại trừ đơn vị tính/dung tích (`ml`, `g`, `gsm`...) khỏi trường địa chỉ.<br>2. Lọc `accumulated_attrs` chỉ giữ thuộc tính hợp lệ của sản phẩm hiện tại và xóa sạch thuộc tính biến thể cũ khi đổi sản phẩm. | `test_issue19_variant_cross_product_attributes_and_capacity_not_address`      |

---

## 9. Kết Quả Đánh Giá Thực Nghiệm & Đo Lường Định Lượng

### 9.1. Tổng hợp kết quả các bộ kiểm thử tự động

Toàn bộ các bộ kiểm thử được thực thi tự động trong môi trường SQLite in-memory / temporary database hoàn toàn cô lập:

| Bộ kiểm thử tự động                                                         | Số lượng ca kiểm thử | Kết quả thực thi | Tỷ lệ thành công |   Thời gian chạy   |
| :-------------------------------------------------------------------------------- | :-----------------------: | :-----------------: | :------------------: | :------------------: |
| **RAG Unit & Security Suite** (`tests/test_rag.py`)                       |            29            |      29 Passed      |   **100.0%**   |      ~1.6 giây      |
| **Chatbot Unit & Integration Suite** (`tests/test_chatbot.py`)            |            27            |      27 Passed      |   **100.0%**   |      ~1.5 giây      |
| **TỔNG CỘNG TOÀN BỘ UNIT TESTS**                                        |       **56**       | **56 Passed** |   **100.0%**   | **~3.1 giây** |
| **AI Chatbot Multi-turn Evaluation** (`eval/run_chatbot_evaluation.py`)   |             9             |      9 Passed      |   **100.0%**   |      ~2.5 giây      |
| **RAG Quantitative Benchmark** (`eval/run_rag_evaluation.py --split all`) |            21            |      21 Passed      |   **100.0%**   |      ~0.8 giây      |
| **Inherited E-Commerce Suite** (`eval/run_evaluation.py --provider fake`) |            14            |      14 Passed      |   **100.0%**   |      ~1.2 giây      |
| **Frontend Production Build** (`npm run build`)                           |       1,566 modules       | 0 Error / 0 Warning |  **SUCCESS**  |        705 ms        |

### 9.2. Bảng chỉ số đo lường RAG chi tiết (RAG Metrics Breakdown)

| Chỉ số đánh giá                    | Giá trị đo được | Ý nghĩa nghiệp vụ & Kỹ thuật                                                                                                 |
| :-------------------------------------- | :-------------------: | :--------------------------------------------------------------------------------------------------------------------------------- |
| **Hit@3**                         |   **100.0%**   | 100% các câu hỏi truy xuất thành công chunk chứa câu trả lời trong Top 3 kết quả tìm kiếm.                           |
| **Recall@5**                      |   **97.92%**   | Tỷ lệ bao phủ toàn bộ các chunk cần thiết trong Top 5 (Dev: 95.24%, Test: 100%).                                           |
| **Mean Reciprocal Rank (MRR)**    |   **0.9688**   | Vị trí trung bình của chunk đúng đầu tiên đạt hạng 1.03 (gần như luôn đứng ở vị trí số 1).                    |
| **Citation Resolve Rate**         |   **100.0%**   | 100% các trích dẫn đều đối chiếu chính xác tới `chunk_id`, tài liệu nguồn và phiên bản hợp lệ trong manifest. |
| **Expected Fact Match Rate**      |   **96.43%**   | Mức độ khớp các sự kiện cốt lõi (thời hạn, thông số, biểu phí) trong câu trả lời tổng hợp.                     |
| **Retrieved Evidence Coverage**   |   **100.0%**   | Toàn bộ dữ kiện cần thiết đều được kéo về đầy đủ trong ngữ cảnh (context).                                      |
| **Citation Lexical Support**      |   **96.43%**   | Các câu trích dẫn được hỗ trợ bằng chứng từ vựng trực tiếp từ chunk nguồn.                                        |
| **Safe Abstention Rate**          |   **100.0%**   | 100% các câu hỏi về sản phẩm ngoài danh mục hoặc mã giảm giá công khai đều được từ chối an toàn.              |
| **Access Denied Rate**            |   **100.0%**   | 100% các truy vấn tài liệu nội bộ của vai trò Customer đều bị chặn dứt khoát không rò rỉ dữ liệu.               |
| **Mixed Route & Action Accuracy** |   **100.0%**   | 100% câu hỏi hỗn hợp được tách đúng nhánh tri thức và nhánh tạo đơn hàng độc lập.                             |

---

## 10. Đối Chiếu Chi Tiết Với Yêu Cầu Đề Tài (Guiding Documents Audit)

Bảng đối chiếu mức độ đáp ứng 13 yêu cầu kỹ thuật bắt buộc từ tài liệu [`Project_RAG_Requirements.pdf`](file:///D:/VSCode/Project/RAG/given/Project_RAG_Requirements.pdf):

|     STT     | Yêu cầu kỹ thuật từ Guiding Documents                                                                                       |       Mức độ đáp ứng       | Minh chứng triển khai trong dự án                                                                                                                                             |
| :----------: | :------------------------------------------------------------------------------------------------------------------------------- | :------------------------------: | :-------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| **1** | Kế thừa toàn bộ web, API, DB, catalog, order từ project LLM; RAG không tự ý ghi đơn.                                   |           **ĐẠT **           | Giữ nguyên React/Vite storefront, FastAPI, SQLite; RAG chỉ là module tra cứu Read-Only; test suite kế thừa 14/14 PASS.                                                     |
| **2** | Có Knowledge Corpus tối thiểu 12 tài liệu hoặc 30 chunks, có provenance và phân quyền.                                 |           **ĐẠT **           | Xây dựng 12 tài liệu Markdown, 31 chunks có ý nghĩa nghiệp vụ; manifest quản lý đầy đủ metadata và 3 cấp độ phân quyền.                                      |
| **3** | Ingestion thẩm định tính hợp lệ của file, ID, encoding, metadata; chunk có source, version, access, section.             |           **ĐẠT **           | Hàm `chunk_document()` và `build_index_bundle()` xác thực schema, chống Path Traversal, mã băm nguồn SHA-256.                                                         |
| **4** | Bundle ghi thông tin embedding, encoding, metric, chunk config và kiểm tra toàn vẹn trước khi nạp.                       |           **ĐẠT **           | `artifacts/index_bundle.json` lưu trữ metadata đầy đủ; kiểm tra toàn vẹn bằng SHA-256 Checksum qua `hmac.compare_digest`.                                           |
| **5** | Mô hình Embedding tương thích cho câu hỏi/tài liệu và đáp ứng tra cứu ngữ nghĩa.                                 | **ĐẠT MỨC THỰC DỤNG** | Triển khai `DeterministicEmbedder` 1024 chiều (N-gram từ + Character trigrams), chuẩn hóa L2, kết hợp Topic Query Expansion; đạt Hit@3 100%.                           |
| **6** | Lọc quyền người dùng (Role pre-filter) trước khi xếp hạng, context assembly và citation.                               |           **ĐẠT **           | Lọc quyền ở bước đầu tiên của `retrieve()`; backend kiểm soát token bí mật `DEMO_STAFF_TOKEN`/`DEMO_ADMIN_TOKEN`.                                              |
| **7** | Xử lý đầy đủ các nhánh: không có tài liệu (no-evidence), từ chối truy cập (access-denied), câu hỏi mâu thuẫn. |           **ĐẠT **           | Đã triển khai và có test case độc lập bảo vệ: từ chối sản phẩm lạ, chặn khách hỏi mã nhân viên, giải quyết mâu thuẫn thuộc tính sản phẩm.            |
| **8** | Mọi khẳng định nghiệp vụ quan trọng bắt buộc phải có chứng cứ và trích dẫn kiểm chứng được.                 |           **ĐẠT **           | Grounded synthesis từ chunk text; trả về cấu trúc JSON contract với mảng `citations` minh bạch; Citation Resolve Rate đạt 100%.                                       |
| **9** | Truy vấn hỗn hợp (Mixed Query) tách bạch tri thức và hành động; hành động qua validation cũ.                       |           **ĐẠT **           | Bộ tách mệnh đề tiếng Việt (`và`, `nhưng`, `rồi`...) trong `router.py`; RAG trả lời chính sách, Chat Engine kiểm tra tồn kho và tạo đơn nháp SQLite. |
| **10** | Tối thiểu 20 ca kiểm thử định lượng, đủ 7 nhóm danh mục, phân chia dev/test.                                        |           **ĐẠT **           | Xây dựng bộ 21 ca kiểm thử trong `evaluation_cases.jsonl` và 20 ca trong `evaluation_holdout_v13.jsonl` bao phủ đủ các nhóm.                                       |
| **11** | Phân tích ít nhất 5 lỗi/near-misses theo các tầng và có cải tiến hồi quy có kiểm soát.                            |           **ĐẠT **           | Phân tích chi tiết 6 ca near-misses trong `evaluation_report.md` và toàn bộ 19 issues trong Resolution Ledger có test case bảo vệ.                                     |
| **12** | Hỗ trợ Re-index từ v1.0 lên v1.1, xác minh phiên bản, kích hoạt, rollback tức thì và ghi audit log an toàn.         |           **ĐẠT **           | API `POST /api/v1/rag/reindex` hoán đổi con trỏ nguyên tử `active_index.json` < 1 giây; rollback tức thì; lưu vết đầy đủ trong `AuditLog`.                   |
| **13** | Kịch bản demo 10–12 phút + Q&A thể hiện đầy đủ các luồng nghiệp vụ bắt buộc.                                     |           **ĐẠT **           | Đã hoàn thiện kịch bản 7 bước trong [`Presentation/demo.md`](Presentation/demo.md), Slide thuyết trình và Speaker Notes chi tiết.                                    |

---

## 11. Giới Hạn Hệ Thống & Lộ Trình Phát Triển Sản Xuất (Production Roadmap)

### 11.1. Các giới hạn kỹ thuật hiện tại

1. **Mô hình Vectorizer dạng Lexical N-gram:** Hệ thống hiện dùng hashed term-frequency vectors nhằm ưu tiên tính độc lập, ổn định tuyệt đối và tốc độ phản hồi cực nhanh (< 5ms trên CPU) cho môi trường demo cục bộ. Do đó, khả năng hiểu các câu diễn đạt mang tính hoán dụ hoặc từ đồng nghĩa quá xa lạ ngoài từ điển còn hạn chế so với các mô hình Neural Embedding lớn.
2. **Cơ chế Token Demo đơn giản:** Hiện dùng token cấu hình qua biến môi trường (`DEMO_STAFF_TOKEN`, `DEMO_ADMIN_TOKEN`) để phục vụ chấm điểm đồ án, chưa tích hợp với hệ thống quản lý định danh doanh nghiệp thực thụ (SSO, OAuth2, LDAP).
3. **Phạm vi Hoán đổi Con trỏ trên Single-host:** Cơ chế thay thế nguyên tử `active_index.json` hoạt động trên cùng một hệ thống tệp tin (filesystem), chưa có cơ chế Distributed Lock (như Redis Redlock hay ZooKeeper) để đồng bộ đa cụm máy chủ (multi-host cluster).

### 11.2. Lộ trình nâng cấp môi trường Production

- **Tầng Embedding:** Tích hợp mô hình Neural Embedding đa ngôn ngữ như **BGE-M3** hoặc **OpenAI text-embedding-3-small** thông qua mô hình Adapter có sẵn trong `src/rag.py` để tăng cường khả năng hiểu ngữ nghĩa sâu.
- **Tầng Vector Store:** Chuyển đổi từ file bundle JSON sang cơ sở dữ liệu vector chuyên dụng phân tán như **Qdrant**, **Milvus** hoặc **Pgvector**.
- **Tầng Xác thực:** Thay thế Header Token bằng chuẩn xác thực doanh nghiệp **JSON Web Token (JWT)** có chữ ký mã hóa RSA, phân quyền theo nhóm người dùng (RBAC Claims).
- **Đánh giá Chuyên gia (Human-in-the-loop):** Tổ chức quy trình đánh giá gán nhãn thủ công (Human claim-by-claim entailment review) để chấm điểm câu trả lời theo 5 mức độ: *Supported, Partially Supported, Unsupported, Contradicted, Unverifiable*.

---

## 12. Hướng Dẫn Tái Lập Môi Trường & Chạy Kiểm Thử Toàn Bộ

### 12.1. Cài đặt môi trường

```powershell
# 1. Kích hoạt môi trường ảo Python
.\.venv\Scripts\Activate.ps1

# 2. Cài đặt các thư viện phụ thuộc (nếu chưa có)
pip install -r requirements.txt

# 3. Cài đặt dependencies cho frontend
Set-Location frontend
npm install
Set-Location ..
```

### 12.2. Lệnh thực thi toàn bộ các bộ kiểm thử tự động

```powershell
# Chạy toàn bộ 56 Unit & Integration Tests (RAG + Chatbot)
python -m unittest tests/test_rag.py tests/test_chatbot.py -v

# Chạy bộ đo lường định lượng RAG (toàn bộ 21 cases)
python -m eval.run_rag_evaluation --split all

# Chạy bộ đo lường hội thoại Chatbot đa lượt
python eval/run_chatbot_evaluation.py

# Chạy bộ kiểm thử luồng E-commerce kế thừa
python eval/run_evaluation.py --provider fake

# Kiểm tra build giao diện Frontend production
npm --prefix frontend run build
```

### 12.3. Khởi chạy ứng dụng phục vụ Demo trực tiếp

```powershell
# Terminal 1: Khởi chạy Backend FastAPI
.\.venv\Scripts\Activate.ps1
$env:LLM_PROVIDER = "fake"
python -m uvicorn backend.app.main:app --reload --port 8000

# Terminal 2: Khởi chạy Frontend React Storefront
Set-Location frontend
npm run dev
```

Truy cập trình duyệt tại địa chỉ: `http://localhost:5173`.
