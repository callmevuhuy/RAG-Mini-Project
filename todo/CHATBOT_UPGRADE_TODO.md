# TODO: Nâng cấp AI chatbot (ưu tiên Fake mode)

## Mục tiêu

Làm chatbot nhận diện ý định và trích xuất thông tin tiếng Việt linh hoạt hơn, đặc biệt trong hội thoại nhiều lượt; giảm hỏi lặp và tránh hành động khi dữ liệu chưa rõ. Giữ giá, SKU, tồn kho, quyền sở hữu và trạng thái đơn do backend/SQLite xác minh.

## Khả thi trong Fake mode?

**Có, trong phạm vi hội thoại thương mại đã biết.** Fake mode hiện là bộ luật/regex (không phải mô hình AI sinh hay hiểu ngôn ngữ tự do). Có thể nâng cấp đáng kể bằng cách chuẩn hóa văn bản, từ điển cách nói tương đương, trích xuất theo slot, đối chiếu catalog, quản lý trạng thái hội thoại và hỏi xác nhận khi mơ hồ. Cách này chạy offline, tái lập và dễ kiểm thử.

Giới hạn: độ linh hoạt vẫn phụ thuộc các mẫu/ngữ liệu được thiết kế. Fake mode không thể hiểu mọi cách diễn đạt mới như một LLM; khi cần mở rộng ngôn ngữ tự nhiên ngoài phạm vi luật đã đánh giá, dùng provider LLM tùy chọn cho bước diễn giải, còn backend tiếp tục xác thực và quyết định mọi side effect.

## Việc cần làm

### P0 — Ghi baseline và hợp đồng trích xuất

- [x] Rà soát router, extractor, pending state và order handler; ghi lại luồng hiện tại và các lỗi tái hiện được (chi tiết tại `artifacts/p0_baseline_report.md`).
- [x] Chốt schema extractor có kiểu cho `intent`, sản phẩm, biến thể, số lượng, tên, điện thoại, địa chỉ, mã tham chiếu và độ mơ hồ.
- [x] Quy định rõ `null` khi thiếu; không tự đặt số lượng, không tự chọn biến thể hoặc tự tạo thông tin người nhận.
- [x] Tạo bộ hội thoại tổng hợp/ẩn danh gồm cách diễn đạt có nhãn, không nhãn, lỗi chính tả phổ biến và nhiều lượt (`artifacts/chatbot_baseline_cases.json`).

### P1 — Nâng cấp nhận diện intent và trích xuất trong Fake mode

- [x] Chuẩn hóa Unicode, dấu tiếng Việt, viết hoa/thường, khoảng trắng và một số dạng viết tắt an toàn (`chat_engine.normalize_text`).
- [x] Gom intent thành các nhóm rõ ràng: hỏi giá, hỏi tồn, tạo đơn, bổ sung thông tin đơn đang chờ, sửa đơn, hỏi kiến thức, mixed, cần làm rõ và handoff.
- [x] Thêm từ đồng nghĩa/biến thể câu tiếng Việt có kiểm soát; ưu tiên luật đặc hiệu, tránh các phép dò substring rộng gây match nhầm.
- [x] Trích xuất quantity và thuộc tính variant độc lập với thứ tự từ; hỗ trợ các định dạng viết tắt ('2c', '2 cái', 'chốt 2'...).
- [x] Trích xuất tên/điện thoại/địa chỉ theo nhãn và KHÔNG NHÃN ('Nguyễn Văn An, 0901..., 123 Lê Lợi Q1') qua `extract_contact_info`.
- [x] Tách phần sản phẩm khỏi phần thông tin nhận hàng (`residual_text`) trước khi đối chiếu tên/alias với catalog SQLite.
- [x] Thêm ngưỡng/luật xử lý match mơ hồ; không chọn bừa kết quả đầu tiên khi có nhiều sản phẩm hoặc variant phù hợp.

### P1 — Làm hội thoại nhiều lượt đáng tin cậy

- [x] Biến pending order thành state/slot flow tường minh: intent, SKU đã xác nhận, quantity, recipient fields, trường còn thiếu và thời hạn (30 phút).
- [x] Khi đang có pending order, diễn giải tin tiếp theo theo ngữ cảnh; hỗ trợ khách gửi từng trường hoặc nhắc lại sản phẩm mà không mất quantity/variant.
- [x] Chỉ cập nhật đúng pending state của session hiện tại; hỗ trợ hủy ý định (`cancel_pending`) và xóa state sạch sẽ.
- [x] Hỏi đúng trường còn thiếu, không lặp lại trường đã có. Trước khi tạo draft, gửi tóm tắt để người dùng xác nhận.
- [x] Giữ idempotency, ownership, kiểm tra tồn kho, audit và quyền quyết định side effect ở backend.

### P2 — Tách module vừa đủ để bảo trì

- [x] Tách logic khỏi endpoint chat lớn thành module `backend/app/chat_engine.py` phụ trách: entity extraction, catalog matching, multi-turn state machine và order action validation.
- [x] Giữ endpoint `chat_message` làm nhiệm vụ kiểm tra request/session, gọi orchestration và trả response.
- [x] Dùng chung schema và hợp đồng giữa Fake extractor và Ollama extractor; xem mọi đầu ra extractor là dữ liệu không tin cậy.
- [x] Chuẩn hóa response cho `answer`, `needs_information`, `handoff`, `pending_confirmation`, `out_of_stock` và `error` để UI diễn đạt đúng trạng thái.

### P2 — Evaluation và theo dõi lỗi

- [x] Thêm case đa lượt tái hiện ảnh demo: thông tin không nhãn, gửi bổ sung từng trường, gửi lại cả yêu cầu và câu trả lời mơ hồ (`artifacts/chatbot_baseline_cases.json`).
- [x] Bổ sung case intent gần nhau, phủ định, câu hỏi mixed, nhiều sản phẩm/variant, số lượng viết tắt, prompt injection.
- [x] Viết bộ kiểm thử unit & integration `tests/test_chatbot.py` (14/14 PASS bao gồm truy vấn tồn kho/sản phẩm tự nhiên, hỏi giảm giá/chiết khấu, tìm kiếm catalog tiếng Việt, out-of-stock biến thể và loại bỏ toàn bộ cảnh báo demo) và runner `eval/run_chatbot_evaluation.py` (100% Accuracy).
- [x] Bảo toàn 100% bộ kiểm thử kế thừa (14/14 PASS tại `eval/run_evaluation.py`).
- [x] Chỉ log metadata cần thiết; không ghi raw message, số điện thoại, tên hoặc địa chỉ vào báo cáo evaluation/runtime log.

### P3 — Tùy chọn tăng độ linh hoạt ngoài Fake mode

- [ ] Sau khi Fake mode có baseline vững, so sánh extractor LLM với cùng evaluation set.
- [ ] Nếu bật provider LLM, dùng nó để diễn giải/trích xuất có schema; backend vẫn kiểm tra catalog, quyền, tồn kho và state trước mọi hành động.
- [ ] Đo chất lượng, độ trễ, chi phí, lỗi provider và fallback trước khi chọn provider làm mặc định.
- [ ] Giữ Fake mode làm lựa chọn offline/tái lập cho demo và kiểm thử.

## Tiêu chí hoàn tất

- [ ] Bộ hội thoại tổng hợp bao phủ single-turn và multi-turn, gồm các biến thể nhập liệu thực tế.
- [ ] Các trường đã nói không bị hỏi lại; trường mơ hồ được xác nhận; thông tin thiếu không bị tự bịa.
- [ ] Không tạo/sửa đơn nếu intent, sản phẩm, variant, quantity hoặc thông tin bắt buộc chưa đủ; không có side effect trùng khi retry.
- [ ] Giá, tồn, SKU, ownership và trạng thái đơn vẫn được backend/DB xác minh.
- [ ] Báo cáo so sánh baseline và phiên bản cải tiến bằng evaluation chạy trên SQLite tạm; cập nhật README/kiến trúc/evaluation khi hành vi thay đổi.

## Tham chiếu trong repository

- `backend/app/llm.py` — extractor Fake/Ollama và schema extraction.
- `backend/app/main.py` — orchestration chat, routing tích hợp, pending state và order actions.
- `src/router.py` — heuristic router RAG/order/mixed/handoff.
- `eval/test_cases.json` — evaluation kế thừa cho intent/order multi-turn.
- `artifacts/evaluation_cases.jsonl` — evaluation RAG/router/mixed.
- `given/LLM_Architecture.md`, `given/RAG_Architecture.md`, `given/RAG_Workflow.md` — ranh giới và trạng thái kiến trúc hiện tại.
