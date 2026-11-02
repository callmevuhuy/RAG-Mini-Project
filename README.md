# RAG Extension — AI Live Commerce Order Assistant

Dự án mở rộng từ trợ lý thương mại LLM kế thừa, bổ sung tra cứu tài liệu có phân quyền (RAG) và nâng cấp bộ não AI Chatbot hội thoại đa lượt linh hoạt. RAG sử dụng corpus mẫu local và vectorizer hashed n-gram; chatbot hỗ trợ bóc tách thực thể không nhãn, bảo toàn trạng thái đơn nháp và đổi ý an toàn. Giá, SKU, tồn kho và đơn hàng vẫn do SQLite database quản lý độc quyền.

## Trạng thái hiện tại (02/11/2026)

- **Corpus & Quyền hạn RAG**: 12 tài liệu, 31 chunks; corpus v1.0 và candidate v1.1. Khách hàng chỉ xem tài liệu public; staff/admin yêu cầu token demo do backend cấu hình.
- **RAG Retriever**: Tìm kiếm lexical bằng hashed word/character n-gram term-frequency vectors (1024 chiều), cosine similarity. Trả về trích dẫn (citations) có thể xác minh metadata.
- **AI Chatbot Engine linh hoạt (`chat_engine.py`)**:
  - Tự động bóc tách thông tin liên hệ người nhận (Tên, SĐT, Địa chỉ) ngay cả khi **hoàn toàn không có nhãn** (ví dụ: *"Nguyễn Văn An, 0901234567, 123 Lê Lợi Q1"*).
  - Hỗ trợ số lượng và biến thể tự nhiên theo thói quen người Việt (*"2c"*, *"2 cái"*, *"chốt 2"*...).
  - Quản lý máy trạng thái đa lượt: không bị ghi đè mất số lượng khi khách nhắc lại sản phẩm, gom slot lũy tiến và xử lý lệnh hủy/đổi ý (`cancel_pending`) an toàn.
  - Phân tách thực thể khỏi câu chat trước khi đối chiếu Catalog SQLite, chống nhầm lẫn tên người hoặc tên đường thành sản phẩm.
- **Kiểm thử tái lập**: Đạt **100%** trên toàn bộ các bộ kiểm thử: 8/8 Chatbot unit/integration tests, 9/9 Chatbot multi-turn evaluation cases, 10/10 RAG tests, 20/20 RAG eval cases, và 14/14 Inherited e-commerce cases.

## Hướng dẫn tái hiện Project (Chạy Local)

Yêu cầu hệ thống: **Python 3.11+** và **Node.js 20+**.

### Bước 1: Khởi tạo và kích hoạt Môi trường ảo (Python Virtual Environment)

Mở terminal PowerShell tại thư mục gốc của project:

```powershell
# 1. Khởi tạo môi trường ảo Python
python -m venv .venv

# 2. Kích hoạt môi trường ảo
.\.venv\Scripts\Activate.ps1
```

> [!TIP]
> Nếu gặp lỗi chính sách thực thi script của PowerShell (*ExecutionPolicy*), hãy mở PowerShell và chạy lệnh sau trước khi kích hoạt:
> ```powershell
> Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass
> ```

### Bước 2: Cài đặt Dependencies và Khởi chạy Backend

Trong cùng terminal đã kích hoạt môi trường ảo `(.venv)`:

```powershell
# Nâng cấp pip và cài đặt thư viện
python -m pip install --upgrade pip
python -m pip install -r requirements.txt

# Thiết lập file cấu hình môi trường
Copy-Item .env.example .env

# Đặt provider mặc định là Fake mode và khởi chạy server API
$env:LLM_PROVIDER = "fake"
python -m uvicorn backend.app.main:app --reload
```

Server API chạy tại: `http://127.0.0.1:8000`, tài liệu Swagger UI tại `http://127.0.0.1:8000/docs`.

### Bước 3: Cài đặt và Khởi chạy Frontend Storefront

Mở một cửa sổ terminal mới:

```powershell
Set-Location frontend
npm ci
npm run dev
```

Giao diện Web chạy mặc định tại: `http://127.0.0.1:5173`.

> [!NOTE]
> Demo staff/admin bị tắt nếu chưa cấu hình `DEMO_STAFF_TOKEN` và `DEMO_ADMIN_TOKEN` trong file `.env` hoặc môi trường backend. UI sẽ hỏi token và chỉ lưu trong bộ nhớ tạm của tab trình duyệt.

## Build Index & Quản lý Phiên bản RAG

```powershell
# Tạo bundle index cho corpus v1.0
python -m src.indexer --version 1.0

# Tạo bundle index cho corpus v1.1
python -m src.indexer --version 1.1 --corpus data/corpus_v1_1 --manifest data_config/corpus_manifest_v1_1.json --output artifacts/index_bundle_v1_1.json
```

Bundle có mã SHA-256 để phát hiện hư hỏng vô ý, metadata vectorizer/chunking và source hashes. Kích hoạt chuyển đổi phiên bản nóng qua con trỏ active `artifacts/active_index.json`.

## Lệnh Kiểm tra Toàn diện (Testing & Evaluation)

Đảm bảo terminal đã kích hoạt môi trường ảo `(.venv)`:

```powershell
# 1. Kiểm tra unit & integration của AI Chatbot Engine mới
python -m unittest tests/test_chatbot.py -v

# 2. Đánh giá khả năng hội thoại đa lượt & bóc tách thực thể không nhãn của Chatbot
python eval/run_chatbot_evaluation.py

# 3. Kiểm tra unit & integration của RAG Engine và phân quyền
python -m unittest tests/test_rag.py -v

# 4. Đánh giá chất lượng RAG Retrieval, Citation và Routing (Toàn bộ 20 cases)
python -m eval.run_rag_evaluation --split all

# 5. Kiểm tra 14 kịch bản thương mại điện tử kế thừa và bảo mật API
python eval/run_evaluation.py --provider fake

# 6. Kiểm tra build production của Frontend
Set-Location frontend; npm run build
```

### Tóm tắt kết quả đo lường:
- **AI Chatbot Multi-turn Evaluation**: 9/9 cases đạt (**100.0%**), bóc tách chính xác thông tin không nhãn, bảo toàn số lượng đơn nháp qua nhiều lượt và hỗ trợ hủy đơn tức thì.
- **RAG Evaluation Suite**: Hit@3 **100%**, Recall@5 **93.89%**, MRR **0.9000**, Citation Resolution **100%**, Claim Support Proxy **70%**, Safe Abstention **100%**, Access-denied **100%**, Route/Status Accuracy **100%**.
- **Inherited E-commerce Flow Suite**: **14/14 PASS**, API Smoke 12/12 endpoints 200/201/204, Security Probes chặn can thiệp giá/kho và đơn hàng trái phép đạt 100%.

## Cấu trúc Thư mục

- `backend/`: FastAPI application, SQLite database models, API endpoints và **AI Chat Engine** (`backend/app/chat_engine.py`).
- `src/`: RAG ingestion, lexical vectorizer, retrieval, grounded answer generation và intent router.
- `frontend/`: React/Vite storefront, catalog browsing, shopping cart và chat interface có hỗ trợ RAG badges/citations.
- `data/`, `data_config/`: Markdown corpus và manifest giả lập có phân quyền.
- `artifacts/`: Index bundles (v1.0, v1.1), baseline evaluation cases và báo cáo kiểm nghiệm.
- `tests/`: Bộ kiểm thử tự động cho RAG (`test_rag.py`) và Chatbot Engine (`test_chatbot.py`).
- `eval/`: Các scripts đánh giá định lượng cho RAG, Chatbot và Inherited flows.
- `todo/`: Kế hoạch và tiến độ nâng cấp AI Chatbot (`CHATBOT_UPGRADE_TODO.md`).

## Giới hạn Bảo mật & Kiến trúc

Đây là phiên bản demo cục bộ: Role tokens là shared secrets, không thay thế cho hệ thống SSO/IAM doanh nghiệp thực thụ; HTTP local không mã hóa; Retriever sử dụng n-gram lexical features nên không thay thế hoàn toàn cho semantic neural embedding models (như BGE-M3 hay text-embedding-3). Xem chi tiết tại [Kiến trúc RAG](given/RAG_Architecture.md), [Kế hoạch Workflow](given/RAG_Workflow.md), và [Báo cáo Đánh giá](artifacts/evaluation_report.md).
