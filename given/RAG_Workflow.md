# RAG Project Workflow

## Mục tiêu

Mở rộng trợ lý thương mại LLM kế thừa bằng ingestion tài liệu, vector retrieval có phân quyền, câu trả lời tiếng Việt có nguồn, và nâng cấp AI Chatbot xử lý hội thoại đa lượt thông minh. Giá, tồn kho, SKU hợp lệ và trạng thái đơn vẫn do backend/SQLite quyết định độc quyền; câu trả lời RAG không được ghi dữ liệu nghiệp vụ.

## Trạng thái hiện tại (02/11/2026)

| Giai đoạn | Trạng thái | Bằng chứng / giới hạn |
|---|---|---|
| Baseline LLM và tích hợp | Hoàn tất cho demo | FastAPI, React, SQLite, luồng giỏ hàng/đơn, Fake provider; legacy eval chạy 14/14 sau cập nhật router. |
| Nâng cấp AI Chatbot (P0, P1, P2) | Hoàn tất cho demo | Module `backend/app/chat_engine.py` bóc tách thực thể không nhãn (hỗ trợ cả street address), gom slot đa lượt, bảo toàn số lượng khi lặp tên sản phẩm, hủy đơn pending tức thì, xử lý tự nhiên các câu hỏi tồn kho/sản phẩm (Issue 2..10), giải đáp chiết khấu/giảm giá (Issue 11), tìm kiếm sản phẩm tiếng Việt có dấu/không dấu (Issue 12) và loại bỏ toàn bộ cảnh báo demo trong ứng dụng. Đạt 14/14 unit tests và 9/9 chatbot eval cases (100%). |
| Corpus và provenance | Hoàn tất cho corpus mẫu | 12 tài liệu, 31 chunks, public/staff/admin; manifest bắt buộc metadata và từ chối đường dẫn ra ngoài corpus. |
| Ingestion và index | Một phần | Chunk Markdown H2, vector hashed word/character n-gram TF, bundle có SHA-256 và metadata. Có retrieval offline nhưng chưa dùng semantic neural embedding model, nên mục tiêu embedding chất lượng ngữ nghĩa sâu chưa hoàn tất. |
| Permission-aware RAG | Hoàn tất cho demo cục bộ | Lọc role trước xếp hạng; staff/admin cần token backend cấu hình. Token không đồng nghĩa với SSO hay danh tính người dùng doanh nghiệp. |
| API/UI | Hoàn tất cho demo | Knowledge, mixed, order và handoff; role token chỉ giữ trong bộ nhớ frontend. API re-index yêu cầu admin token, session và origin hợp lệ. |
| Evaluation | Đạt toàn bộ các bộ test | 20 RAG cases (100% route/status, 100% citation resolve, 70% claim proxy); 9 Chatbot multi-turn cases (100%); 14/14 inherited fake-flow cases. |
| Re-index/rollback | Đã triển khai; cần vận hành kiểm soát | Bundle v1.0/v1.1 đã có; API đổi file con trỏ active bằng replace nguyên tử. Không có distributed lock hoặc kiểm soát đa máy chủ. |

## Quy tắc làm việc

1. Đọc `RAG_Architecture.md`, `Project_RAG_Requirements.pdf`, README và tài liệu LLM kế thừa trước khi đổi pipeline.
2. Giữ dữ liệu vận hành trong DB. Không dùng RAG làm nguồn giá/tồn kho hoặc cho phép câu trả lời RAG gọi hành động ghi.
3. Chỉ dùng dữ liệu giả đã được phép; không commit secret, PII thật hoặc tài liệu nội bộ chưa được duyệt.
4. Sửa code thì cập nhật caller, tests, fixture/config và tài liệu liên quan. Báo cáo số liệu từ lần chạy thực tế, ghi rõ giới hạn của evaluator.

## Các ranh giới phải giữ

- Customer chỉ truy xuất `public`; staff truy xuất `public` + `staff`; admin truy xuất tất cả.
- Header `X-User-Role` là lựa chọn role demo, không phải chứng thực. Staff/admin chỉ được chấp nhận khi token khớp `DEMO_STAFF_TOKEN`/`DEMO_ADMIN_TOKEN` phía backend.
- Index bundle phải qua checksum và kiểm tra cấu trúc trước khi load. SHA-256 trong cùng file phát hiện hỏng vô ý; nó không chứng minh nguồn gốc trước kẻ có thể sửa cả bundle lẫn hash.
- Citation phải resolve đúng metadata chunk. Không dùng citation resolution như bằng chứng tự động rằng mọi claim đều đúng.
- Không tự suy đoán hoặc gán mặc định thông tin người nhận hay số lượng đơn hàng nếu khách chưa cung cấp.

## Lệnh kiểm tra

```powershell
# Kích hoạt môi trường ảo
.\.venv\Scripts\Activate.ps1

# Chạy kiểm thử Chatbot Engine mới
python -m unittest tests/test_chatbot.py -v
python eval/run_chatbot_evaluation.py

# Chạy kiểm thử RAG Engine
python -m unittest tests/test_rag.py -v
python -m eval.run_rag_evaluation --split all

# Chạy kiểm thử luồng thương mại kế thừa
python eval/run_evaluation.py --provider fake

# Kiểm tra build Frontend
Set-Location frontend; npm run build
```

Không chạy Ollama nếu chưa có model/service và yêu cầu hiện tại không cần kiểm tra provider đó.
