"""Script to generate professional widescreen PowerPoint presentation for Group 7 RAG project.
"""
import collections.abc
from pptx import Presentation
from pptx.util import Inches, Pt
from pptx.enum.text import PP_ALIGN
from pptx.dml.color import RGBColor
from pptx.enum.shapes import MSO_SHAPE

def create_presentation():
    prs = Presentation()
    prs.slide_width = Inches(13.333)
    prs.slide_height = Inches(7.5)
    blank_slide_layout = prs.slide_layouts[6]

    # Colors
    COLOR_BG = RGBColor(248, 250, 252)        # #F8FAFC
    COLOR_NAVY = RGBColor(15, 23, 42)          # #0F172A
    COLOR_ORANGE = RGBColor(238, 77, 45)       # #EE4D2D (Shopee/Brand Orange)
    COLOR_SLATE = RGBColor(51, 65, 85)         # #334155
    COLOR_MUTED = RGBColor(100, 116, 139)      # #64748B
    COLOR_WHITE = RGBColor(255, 255, 255)
    COLOR_CARD_BG = RGBColor(255, 255, 255)
    COLOR_CARD_BORDER = RGBColor(226, 232, 240)# #E2E8F0
    COLOR_GREEN = RGBColor(22, 163, 74)        # #16A34A
    COLOR_BLUE = RGBColor(37, 99, 235)         # #2563EB

    def set_slide_background(slide, color=COLOR_BG):
        bg = slide.shapes.add_shape(MSO_SHAPE.RECTANGLE, 0, 0, Inches(13.333), Inches(7.5))
        bg.fill.solid()
        bg.fill.fore_color.rgb = color
        bg.line.fill.background()
        return bg

    def add_header(slide, title_text, category_text="GROUP 7 • RAG MINI-PROJECT"):
        # Category / Eyebrow
        cat_box = slide.shapes.add_textbox(Inches(0.8), Inches(0.4), Inches(11.7), Inches(0.35))
        tf_cat = cat_box.text_frame
        tf_cat.word_wrap = True
        tf_cat.margin_left = tf_cat.margin_top = tf_cat.margin_right = tf_cat.margin_bottom = 0
        p_cat = tf_cat.paragraphs[0]
        p_cat.text = category_text.upper()
        p_cat.font.size = Pt(11)
        p_cat.font.bold = True
        p_cat.font.color.rgb = COLOR_ORANGE
        p_cat.font.name = "Segoe UI"

        # Title
        title_box = slide.shapes.add_textbox(Inches(0.8), Inches(0.75), Inches(11.7), Inches(0.7))
        tf_title = title_box.text_frame
        tf_title.word_wrap = True
        tf_title.margin_left = tf_title.margin_top = tf_title.margin_right = tf_title.margin_bottom = 0
        p_title = tf_title.paragraphs[0]
        p_title.text = title_text
        p_title.font.size = Pt(22)
        p_title.font.bold = True
        p_title.font.color.rgb = COLOR_NAVY
        p_title.font.name = "Segoe UI"

        # Horizontal accent line
        line = slide.shapes.add_shape(MSO_SHAPE.RECTANGLE, Inches(0.8), Inches(1.5), Inches(11.733), Inches(0.02))
        line.fill.solid()
        line.fill.fore_color.rgb = COLOR_CARD_BORDER
        line.line.fill.background()

    def add_card(slide, left, top, width, height, title, items, badge="", badge_color=COLOR_BLUE):
        # Card container
        card = slide.shapes.add_shape(MSO_SHAPE.ROUNDED_RECTANGLE, left, top, width, height)
        card.fill.solid()
        card.fill.fore_color.rgb = COLOR_CARD_BG
        card.line.color.rgb = COLOR_CARD_BORDER
        card.line.width = Pt(1.2)

        # Card header & text
        tb = slide.shapes.add_textbox(left + Inches(0.25), top + Inches(0.2), width - Inches(0.5), height - Inches(0.4))
        tf = tb.text_frame
        tf.word_wrap = True
        tf.margin_left = tf.margin_top = tf.margin_right = tf.margin_bottom = 0

        # Title paragraph
        p_head = tf.paragraphs[0]
        p_head.text = title
        p_head.font.size = Pt(15)
        p_head.font.bold = True
        p_head.font.color.rgb = COLOR_NAVY
        p_head.font.name = "Segoe UI"
        p_head.space_after = Pt(10)

        # Bullet items
        for item in items:
            p = tf.add_paragraph()
            p.text = "• " + item
            p.font.size = Pt(12)
            p.font.color.rgb = COLOR_SLATE
            p.font.name = "Segoe UI"
            p.space_after = Pt(6)

        return card

    # =========================================================================
    # SLIDE 1: TITLE SLIDE (Dark Navy Premium Background)
    # =========================================================================
    s1 = prs.slides.add_slide(blank_slide_layout)
    set_slide_background(s1, COLOR_NAVY)

    # Accent decorative badge
    badge = s1.shapes.add_shape(MSO_SHAPE.ROUNDED_RECTANGLE, Inches(0.8), Inches(1.5), Inches(3.2), Inches(0.4))
    badge.fill.solid()
    badge.fill.fore_color.rgb = COLOR_ORANGE
    badge.line.fill.background()
    p_b = badge.text_frame.paragraphs[0]
    p_b.text = "RAG MINI-PROJECT • GROUP 7"
    p_b.font.size = Pt(11)
    p_b.font.bold = True
    p_b.font.color.rgb = COLOR_WHITE
    p_b.alignment = PP_ALIGN.CENTER

    tb1 = s1.shapes.add_textbox(Inches(0.8), Inches(2.2), Inches(11.5), Inches(2.2))
    tf1 = tb1.text_frame
    tf1.word_wrap = True
    p1_1 = tf1.paragraphs[0]
    p1_1.text = "AI Live Commerce Order Assistant"
    p1_1.font.size = Pt(36)
    p1_1.font.bold = True
    p1_1.font.color.rgb = COLOR_WHITE
    p1_1.font.name = "Segoe UI"

    p1_2 = tf1.add_paragraph()
    p1_2.text = "Mở rộng Hệ thống RAG Phân Quyền & AI Chatbot Đa Lượt"
    p1_2.font.size = Pt(22)
    p1_2.font.color.rgb = RGBColor(203, 213, 225)
    p1_2.space_before = Pt(8)

    p1_3 = tf1.add_paragraph()
    p1_3.text = "Tra cứu tri thức tài liệu có trích dẫn • Phân quyền Pre-retrieval • SQLite làm nguồn sự thật nghiệp vụ"
    p1_3.font.size = Pt(13)
    p1_3.font.color.rgb = COLOR_ORANGE
    p1_3.space_before = Pt(14)

    # Info card on slide 1
    info_box = s1.shapes.add_shape(MSO_SHAPE.ROUNDED_RECTANGLE, Inches(0.8), Inches(4.8), Inches(11.733), Inches(1.8))
    info_box.fill.solid()
    info_box.fill.fore_color.rgb = RGBColor(30, 41, 59)
    info_box.line.color.rgb = RGBColor(51, 65, 85)
    tf_info = info_box.text_frame
    tf_info.word_wrap = True
    tf_info.margin_left = Inches(0.4)
    tf_info.margin_top = Inches(0.3)

    p_in1 = tf_info.paragraphs[0]
    p_in1.text = "Kiến trúc Kế thừa & Mở rộng:"
    p_in1.font.size = Pt(14)
    p_in1.font.bold = True
    p_in1.font.color.rgb = COLOR_WHITE

    p_in2 = tf_info.add_paragraph()
    p_in2.text = "React/Vite Storefront • FastAPI Backend • SQLite Catalog & Inventory • Lexical Vectorizer RAG • Multi-turn State Machine"
    p_in2.font.size = Pt(12)
    p_in2.font.color.rgb = RGBColor(148, 163, 184)
    p_in2.space_before = Pt(4)

    p_in3 = tf_info.add_paragraph()
    p_in3.text = "Bảo vệ: 53/53 Tests PASS (29 RAG + 24 Chatbot) • 21 RAG Eval Cases (Hit@3 100%, Citation 100%) • 9/9 Chatbot Multi-turn"
    p_in3.font.size = Pt(12)
    p_in3.font.color.rgb = RGBColor(52, 211, 153)
    p_in3.space_before = Pt(4)

    # =========================================================================
    # SLIDE 2: BỐI CẢNH & ĐẶT VẤN ĐỀ (TỪ LLM SANG RAG)
    # =========================================================================
    s2 = prs.slides.add_slide(blank_slide_layout)
    set_slide_background(s2)
    add_header(s2, "Bối cảnh & Đặt Vấn đề: Từ Project LLM sang RAG")

    add_card(s2, Inches(0.8), Inches(1.8), Inches(3.7), Inches(5.0),
             "1. Nền tảng Kế thừa (LLM)", [
                 "Storefront React/Vite bán hàng trực tuyến.",
                 "FastAPI backend & cơ sở dữ liệu SQLite quản lý Catalog, tồn kho, đơn hàng, audit log.",
                 "Flow bóc tách ý định mua hàng và tạo đơn hàng nháp.",
                 "Tuyệt đối không đập đi xây lại; giữ trọn vẹn nghiệp vụ thương mại có sẵn."
             ])

    add_card(s2, Inches(4.8), Inches(1.8), Inches(3.7), Inches(5.0),
             "2. Giới hạn ở Project Cũ", [
                 "Chưa có tri thức tài liệu: Không trả lời được chính sách đổi trả, bảo hành, phí ship, cách vệ sinh bình...",
                 "Nguy cơ Hallucination: Dễ bịa đặt ngày giao, điều kiện bảo hành hoặc tự phán đoán tồn kho.",
                 "Không có phân quyền (RBAC): Chưa phân định dữ liệu công khai với tài liệu nội bộ (SOP kho, mã staff).",
                 "Khách hỏi câu hỗn hợp (hỏi chính sách + mua hàng) bị lỗi route."
             ])

    add_card(s2, Inches(8.8), Inches(1.8), Inches(3.7), Inches(5.0),
             "3. Mục tiêu Mở rộng RAG", [
                 "Bổ sung Knowledge Base tài liệu chuẩn hóa 12 docs, 31 chunks.",
                 "Lọc phân quyền trước truy xuất (Pre-retrieval role filtering).",
                 "Sinh câu trả lời có trích dẫn (Grounded + Citations) và biết từ chối khi thiếu bằng chứng.",
                 "Quản lý vòng đời Index Bundle và hỗ trợ Re-indexing/Rollback nóng."
             ])

    # =========================================================================
    # SLIDE 3: KIẾN TRÚC TỔNG THỂ & RANH GIỚI BẢO MẬT
    # =========================================================================
    s3 = prs.slides.add_slide(blank_slide_layout)
    set_slide_background(s3)
    add_header(s3, "Kiến trúc Tổng thể & Ranh giới Bảo mật Hệ thống")

    add_card(s3, Inches(0.8), Inches(1.8), Inches(5.7), Inches(5.0),
             "Luồng Yêu cầu Đa tầng (Request Flow)", [
                 "Trình duyệt (Browser) gửi request kèm Cookie Session và Origin header.",
                 "FastAPI Gateway: Kiểm tra Origin, Rate Limit, Session hết hạn và giải quyết Role Token.",
                 "Unified Router (src/router.py) điều phối 5 luồng:",
                 "  -> knowledge_query: Truy xuất RAG lọc theo role -> Grounded Answer + Citations.",
                 "  -> order_action: Chat Engine đối chiếu SQLite -> Xác nhận đơn nháp.",
                 "  -> mixed: Tách 2 vế độc lập (RAG trả lời tri thức + Chat Engine xử lý đơn).",
                 "  -> safety / handoff: Từ chối can thiệp hệ thống hoặc chuyển tiếp nhân viên."
             ])

    add_card(s3, Inches(6.8), Inches(1.8), Inches(5.7), Inches(5.0),
             "Ranh giới An toàn Cốt lõi (Safety Boundaries)", [
                 "RAG là luồng READ-ONLY: Tuyệt đối không để câu trả lời RAG tự động ghi DB, đổi giá, thay đổi tồn kho.",
                 "SQLite là Authoritative Source: Giá niêm yết, số lượng tồn kho khả dụng do backend/DB quyết định độc quyền.",
                 "Pre-retrieval RBAC: Lọc quyền trước ranking; tài liệu nhân viên/quản trị không bao giờ lọt vào candidate list của khách hàng.",
                 "Xác thực Token Backend: Role staff/admin bắt buộc có token server-side; UI role switcher chỉ là công cụ demo, không phải nguồn chứng thực.",
                 "Audit Log đầy đủ: Ghi nhận mọi sự kiện thao tác nhạy cảm (re-index, đơn hàng, bypass attempt)."
             ])

    # =========================================================================
    # SLIDE 4: UNIFIED ROUTER — PHÂN LUỒNG Ý ĐỊNH
    # =========================================================================
    s4 = prs.slides.add_slide(blank_slide_layout)
    set_slide_background(s4)
    add_header(s4, "Unified Router: Phân luồng Ý định Tự nhiên & An toàn")

    add_card(s4, Inches(0.8), Inches(1.8), Inches(3.7), Inches(5.0),
             "1. Phân loại 5 Tuyến Ý định", [
                 "KNOWLEDGE_QUERY: Câu hỏi về chất liệu, kích thước, chính sách đổi trả, bảo hành, vệ sinh, cách pha cà phê.",
                 "ORDER_ACTION: Đặt mua, chốt số lượng, thêm đơn, cung cấp thông tin giao hàng.",
                 "ORDER_READ: Hỏi giá hiện thời, kiểm tra số lượng tồn kho từng phân loại.",
                 "MIXED QUERY: Kết hợp cả hỏi tri thức và hành động đặt hàng.",
                 "SAFETY / HANDOFF: Prompt injection, can thiệp bảo mật, khiếu nại nhân viên."
             ])

    add_card(s4, Inches(4.8), Inches(1.8), Inches(3.7), Inches(5.0),
             "2. Tách Mệnh đề Tiếng Việt", [
                 "Sử dụng Heuristic Clause Splitting theo liên từ tiếng Việt: và, nhưng, rồi, với lại, ngoài ra...",
                 "Nhận diện chính xác cả từ có dấu và không dấu ('và' vs 'va').",
                 "Cơ chế Residual Disambiguation: Không để tên sản phẩm trong câu hỏi chính sách bị nhầm thành lệnh đặt hàng.",
                 "Ví dụ: 'Áo thun có đổi trả không và chốt 1 áo xanh size M' -> Tách vế tri thức riêng, vế đơn hàng riêng."
             ])

    add_card(s4, Inches(8.8), Inches(1.8), Inches(3.7), Inches(5.0),
             "3. Phòng thủ Prompt Injection", [
                 "Bộ lọc mẫu tấn công độc hại: 'bỏ qua quy tắc', 'tiết lộ secret', 'xóa mọi đơn hàng', 'hack/bypass'...",
                 "Chặn đứng ngay tại router trước khi vào tầng LLM/RAG.",
                 "Phản hồi từ chối an toàn (status: access_denied) và ghi nhật ký cảnh báo.",
                 "Bảo vệ tuyệt đối secret keys, dữ liệu phiên và tính toàn vẹn của hệ thống."
             ])

    # =========================================================================
    # SLIDE 5: CORPUS & INGESTION — KNOWLEDGE BASE TÁI LẬP
    # =========================================================================
    s5 = prs.slides.add_slide(blank_slide_layout)
    set_slide_background(s5)
    add_header(s5, "Corpus & Ingestion: Xây dựng Knowledge Base Tái lập")

    add_card(s5, Inches(0.8), Inches(1.8), Inches(3.7), Inches(5.0),
             "1. Cấu trúc Corpus Mẫu", [
                 "12 tài liệu Markdown có cấu trúc, chuẩn hóa UTF-8.",
                 "31 Chunks có ý nghĩa ngữ nghĩa (vượt yêu cầu tối thiểu 12 docs/30 chunks).",
                 "Tài liệu bao phủ:",
                 "  • 3 Catalog chi tiết (Áo thun, Bình giữ nhiệt, Cà phê Đà Lạt).",
                 "  • 1 Bảng kích thước (Sizing guide).",
                 "  • 3 Chính sách (Giao hàng, Bảo hành, Đổi trả).",
                 "  • 2 FAQ (Xử lý sự cố thiếu hàng, Vệ sinh bình).",
                 "  • 2 Tài liệu nội bộ Staff (SOP kho, Mã giảm giá)."
             ])

    add_card(s5, Inches(4.8), Inches(1.8), Inches(3.7), Inches(5.0),
             "2. Metadata Bắt buộc (Manifest)", [
                 "Quản lý qua corpus_manifest.json.",
                 "Mỗi document quy định bắt buộc:",
                 "  • doc_id, filename, title, version, author.",
                 "  • access_level: public / staff / admin.",
                 "Chunk ID sinh theo quy tắc ổn định: {doc_id}#cNN.",
                 "Cắt chunk theo tiêu đề Markdown H2 (##) giữ trọn vẹn ngữ cảnh từng điều khoản.",
                 "Không cho phép access_level rỗng hoặc tự động gán mặc định thành public."
             ])

    add_card(s5, Inches(8.8), Inches(1.8), Inches(3.7), Inches(5.0),
             "3. Index Bundle & Toàn vẹn", [
                 "Lưu trữ thành bundle độc lập: index_bundle.json.",
                 "Chứa vector matrix, chunk mapping và manifest meta.",
                 "Mã băm SHA-256 Checksum: Tự động xác thực tính toàn vẹn khi load bundle.",
                 "Từ chối tải index nếu số lượng vector, số chiều (dim=1024) hoặc access level không hợp lệ.",
                 "Tái lập 100%: Dễ dàng build lại index qua python -m src.indexer."
             ])

    # =========================================================================
    # SLIDE 6: PHÂN QUYỀN TRUY XUẤT ĐA CẤP (PRE-RETRIEVAL RBAC)
    # =========================================================================
    s6 = prs.slides.add_slide(blank_slide_layout)
    set_slide_background(s6)
    add_header(s6, "Phân quyền Truy xuất Đa cấp (Pre-retrieval RBAC)")

    add_card(s6, Inches(0.8), Inches(1.8), Inches(5.7), Inches(5.0),
             "Nguyên lý Pre-retrieval Filtering", [
                 "TẠI SAO PHẢI PRE-FILTER?",
                 "  • Nếu chỉ ẩn câu trả lời hoặc che citation ở bước cuối: nội dung mật có thể đã đi vào candidate list, cache hoặc prompt LLM.",
                 "Hệ thống áp dụng bộ lọc quyền NGAY TRƯỚC BƯỚC RANKING:",
                 "  • Customer (public): Chỉ được quét các chunk public (chính sách, FAQ, thông số sản phẩm).",
                 "  • Staff: Được quét chunk public + staff (quy trình xử lý khiếu nại, đối soát camera WMS, mã giảm giá staff).",
                 "  • Admin: Toàn quyền truy xuất toàn bộ corpus và quyền re-index.",
                 "Cam kết bảo mật: Chunks staff/admin không bao giờ tồn tại trong bộ nhớ tìm kiếm của khách hàng."
             ])

    add_card(s6, Inches(6.8), Inches(1.8), Inches(5.7), Inches(5.0),
             "Xác thực Phân quyền Demo (Backend Token Gate)", [
                 "Header X-User-Role do client gửi chỉ là nhãn giao diện.",
                 "Backend thẩm định vai trò qua biến môi trường server-side:",
                 "  • Staff: Phải kèm X-Demo-Role-Token khớp DEMO_STAFF_TOKEN.",
                 "  • Admin: Phải kèm X-Demo-Role-Token khớp DEMO_ADMIN_TOKEN.",
                 "Nếu token sai hoặc chưa cấu hình trên server: Backend lập tức trả mã HTTP 403 Forbidden.",
                 "Khách hàng hỏi tài liệu mật (mã staff, quy trình kho):",
                 "  -> Status: access_denied, từ chối an toàn, không rò rỉ bất kỳ nội dung nào."
             ])

    # =========================================================================
    # SLIDE 7: VECTORIZER & CƠ CHẾ RETRIEVAL
    # =========================================================================
    s7 = prs.slides.add_slide(blank_slide_layout)
    set_slide_background(s7)
    add_header(s7, "Cơ chế Vectorizer & Retrieval Tối ưu cho Demo")

    add_card(s7, Inches(0.8), Inches(1.8), Inches(3.7), Inches(5.0),
             "1. Hashed N-Gram TF Vectorizer", [
                 "Sử dụng bộ băm n-gram từ và ký tự (Hashed Word & Char N-gram Term Frequency).",
                 "Không gian vector cố định: 1024 chiều.",
                 "Chuẩn hóa L2 normalization và tính độ tương đồng bằng Cosine Similarity.",
                 "Lợi ích thực tế:",
                 "  • Tốc độ phản hồi cực nhanh: < 5ms.",
                 "  • Chạy offline 100%, không tốn tài nguyên GPU, không phụ thuộc service ngoài."
             ])

    add_card(s7, Inches(4.8), Inches(1.8), Inches(3.7), Inches(5.0),
             "2. Topic Query Expansion", [
                 "Khắc phục điểm yếu của lexical search đối với các truy vấn nhiều điều kiện (Multi-condition).",
                 "Tự động mở rộng từ khóa theo ngữ cảnh:",
                 "  • Hỏi đổi trả: Bổ sung từ khóa thời hạn (7 ngày), điều kiện (tem mác, unbox) và trách nhiệm phí ship.",
                 "  • Hỏi bảo hành: Tách biệt rõ lỗi ngập nước (từ chối) với lỗi rò rỉ gioăng kỹ thuật (bảo hành 12 tháng)."
             ])

    add_card(s7, Inches(8.8), Inches(1.8), Inches(3.7), Inches(5.0),
             "3. Top-k Ranking & Điểm số", [
                 "Xếp hạng Top-k ứng viên (k=3..5) kèm điểm tương đồng cosine similarity.",
                 "Cosine score chỉ phục vụ sắp xếp thứ tự ưu tiên, KHÔNG ĐƯỢC COI LÀ ĐỘ CHẮC CHẮN FACTUAL.",
                 "Cơ chế Topic Preference: Ưu tiên tài liệu đúng chủ đề hỏi, ngăn chặn các chunk điểm cao ngẫu nhiên lấn át nội dung nghiệp vụ chính."
             ])

    # =========================================================================
    # SLIDE 8: GROUNDED GENERATION & CITATION CONTRACT
    # =========================================================================
    s8 = prs.slides.add_slide(blank_slide_layout)
    set_slide_background(s8)
    add_header(s8, "Grounded Generation & Citation Contract Chuẩn hóa")

    add_card(s8, Inches(0.8), Inches(1.8), Inches(5.7), Inches(5.0),
             "Contract Đầu ra Chuẩn của API RAG", [
                 "Đáp ứng chính xác schema quy định trong tài liệu yêu cầu:",
                 "{\n  \"status\": \"answered | insufficient_evidence | access_denied | handoff | error\",\n  \"answer\": \"Câu trả lời tiếng Việt có căn cứ từ tài liệu...\",\n  \"citations\": [\n    {\n      \"chunk_id\": \"POL-RETURN-01#c01\",\n      \"doc_id\": \"POL-RETURN-01\",\n      \"source\": \"Chính sách Đổi trả và Hoàn tiền (v1.0)\",\n      \"version\": \"1.0\",\n      \"section\": \"Thời hạn đổi trả\"\n    }\n  ],\n  \"missing_information\": \"\"\n}",
                 "Mọi khẳng định nghiệp vụ quan trọng đều có citation trích dẫn tới đúng chunk và phiên bản tài liệu."
             ])

    add_card(s8, Inches(6.8), Inches(1.8), Inches(5.7), Inches(5.0),
             "Nguyên tắc Grounding & Safe Abstention", [
                 "Grounded tuyệt đối (Zero Hallucination):",
                 "  • Câu trả lời được tổng hợp trực tiếp từ nội dung văn bản trong chunk được trích xuất.",
                 "  • Tuyệt đối không tự suy diễn 'chắc chắn còn hàng' hay bịa đặt giờ giao chính xác.",
                 "Safe Abstention khi thiếu bằng chứng (No-Evidence):",
                 "  • Khách hỏi sản phẩm không kinh doanh (giày sneaker, đồng hồ, xe điện...): Hệ thống trả về status: insufficient_evidence, thông báo lịch sự sản phẩm chưa có trong danh mục.",
                 "  • Khách hỏi giờ giao cụ thể: Nêu rõ chính sách chỉ giao trong 1-2 ngày và shipper gọi trước 15-30 phút, không cam kết giờ chẵn."
             ])

    # =========================================================================
    # SLIDE 9: XỬ LÝ TRUY VẤN KẾT HỢP (MIXED QUERIES)
    # =========================================================================
    s9 = prs.slides.add_slide(blank_slide_layout)
    set_slide_background(s9)
    add_header(s9, "Xử lý Truy vấn Kết hợp (Mixed Queries) An toàn")

    add_card(s9, Inches(0.8), Inches(1.8), Inches(5.7), Inches(5.0),
             "Tình huống Nghiệp vụ Thực tế", [
                 "Khách hàng thường hỏi chính sách kết hợp đặt hàng cùng lúc trong một câu chat:",
                 "Ví dụ: 'Áo thun basic cotton có được đổi trả không, chốt 1 Áo thun basic cotton màu Xanh size M'",
                 "Thách thức kiến trúc:",
                 "  • RAG không được phép có side-effect ghi đơn vào database.",
                 "  • Order Flow không có tri thức chính sách để trả lời khách.",
                 "Giải pháp: Mô hình điều phối 2 pha độc lập trong FastAPI:"
             ])

    add_card(s9, Inches(6.8), Inches(1.8), Inches(5.7), Inches(5.0),
             "Cơ chế Điều phối 2 Pha Độc lập", [
                 "PHA 1 — Tri thức (Knowledge RAG):",
                 "  • Router bóc tách vế hỏi chính sách đổi trả.",
                 "  • RAG truy xuất tài liệu POL-RETURN-01, tạo câu trả lời đổi trả trong 7 ngày kèm nguồn trích dẫn hợp lệ.",
                 "PHA 2 — Hành động (Order Business Flow):",
                 "  • Router chuyển vế đặt hàng sang Chat Engine.",
                 "  • Đối chiếu catalog SQLite: xác định SKU TSHIRT-BLU-M, giá 209.000₫, tồn kho khả dụng 12 chiếc.",
                 "  • Hỏi thông tin giao hàng còn thiếu hoặc tạo đơn nháp an toàn.",
                 "KẾT QUẢ: Hiển thị badge ⚡ Hỗn hợp (RAG + Đơn hàng). Khách vừa nhận được câu trả lời vừa được phục vụ đặt hàng mượt mà."
             ])

    # =========================================================================
    # SLIDE 10: RE-INDEX & VẬN HÀNH HOT ROLLBACK
    # =========================================================================
    s10 = prs.slides.add_slide(blank_slide_layout)
    set_slide_background(s10)
    add_header(s10, "Re-Index & Vận hành Hot Rollback Nguyên tử")

    add_card(s10, Inches(0.8), Inches(1.8), Inches(3.7), Inches(5.0),
             "1. Kịch bản Cập nhật v1.0 -> v1.1", [
                 "Mô phỏng thay đổi chính sách kinh doanh thực tế:",
                 "  • Chính sách v1.0: Thời hạn đổi trả hàng trong 07 ngày.",
                 "  • Chính sách v1.1: Mở rộng thời hạn đổi trả lên 14 ngày.",
                 "Hai corpus và manifest độc lập:",
                 "  • data/corpus/ (v1.0)",
                 "  • data/corpus_v1_1/ (v1.1)"
             ])

    add_card(s10, Inches(4.8), Inches(1.8), Inches(3.7), Inches(5.0),
             "2. Chuyển đổi Nóng (Atomic Swap)", [
                 "API POST /api/v1/rag/reindex?version=1.1 yêu cầu Admin Token và Origin hợp lệ.",
                 "Kiểm tra tính toàn vẹn của bundle mới.",
                 "Ghi nhận nhật ký kiểm toán vào bảng AuditLog.",
                 "Ghi file tạm rồi thay thế nguyên tử con trỏ artifacts/active_index.json.",
                 "Tất cả worker tự động cập nhật active index mà không cần restart server."
             ])

    add_card(s10, Inches(8.8), Inches(1.8), Inches(3.7), Inches(5.0),
             "3. Xác minh & Rollback Tức thì", [
                 "Verification Query: 'Thời hạn đổi trả hàng là bao nhiêu ngày?'",
                 "  • Khi active v1.0 -> Trả lời 07 ngày (cite v1.0).",
                 "  • Khi active v1.1 -> Trả lời 14 ngày (cite v1.1).",
                 "Thử nghiệm Rollback về v1.0:",
                 "  • Thao tác 1-click trên UI hoặc gọi API rollback.",
                 "  • Hệ thống ngay lập tức phục hồi chính sách cũ an toàn."
             ])

    # =========================================================================
    # SLIDE 11: NÂNG CẤP TOÀN DIỆN AI CHATBOT ENGINE
    # =========================================================================
    s11 = prs.slides.add_slide(blank_slide_layout)
    set_slide_background(s11)
    add_header(s11, "Nâng cấp AI Chatbot Engine (chat_engine.py)")

    add_card(s11, Inches(0.8), Inches(1.8), Inches(5.7), Inches(5.0),
             "Giải quyết Triệt để 16 Issue Thực tế", [
                 "Bóc tách liên hệ KHÔNG NHÃN (Issue 1, 8): Khách nhắn tự nhiên 'Nguyễn Văn An, 0901234567, 123 Lê Lợi Q1' -> Tách đúng Họ tên, SĐT, Địa chỉ.",
                 "Hiểu số lượng và cách gọi đời thường (Issue 13, 14): '2c áo', '2 cái', 'áo trắng size M' (bỏ từ 'thun') -> Đối chiếu chính xác Áo thun basic cotton.",
                 "Tự động chốt biến thể duy nhất (Issue 15): Bình giữ nhiệt màu đen chỉ có dung tích 750ml -> Chốt luôn biến thể, không hỏi vòng lặp vô tận.",
                 "Phản hồi đơn hàng đầy đủ (Issue 16): Khi tạo đơn nháp, bot trả lại đầy đủ chi tiết sản phẩm/biến thể, tổng tiền và toàn bộ thông tin người nhận.",
                 "Bảo toàn số lượng đa lượt & hủy đơn: Giữ nguyên số lượng khi lặp tên sản phẩm; hỗ trợ hủy đơn tức thì (cancel_pending)."
             ])

    add_card(s11, Inches(6.8), Inches(1.8), Inches(5.7), Inches(5.0),
             "Cơ chế Disambiguation & Quản lý Tồn kho", [
                 "Entity Disambiguation:",
                 "  • Bóc tách thông tin liên hệ ra khỏi câu chat trước khi so khớp Catalog SQLite.",
                 "  • Không bị nhầm chữ 'Bình' trong tên người nhận (Trần Bình) thành sản phẩm Bình giữ nhiệt.",
                 "  • Không nhầm tên đường tiếng Anh ('Demo Street') thành sản phẩm.",
                 "Kiểm tra tồn kho tức thì (Early Stock Check):",
                 "  • Nếu biến thể khách chọn đã hết hàng (Áo thun hồng size S tồn = 0): Báo hết hàng ngay lập tức và gợi ý phân loại còn hàng, không đòi hỏi điền địa chỉ vô ích.",
                 "Chống Hallucination mặc định:",
                 "  • Khách chỉ nói tên sản phẩm -> Tuyệt đối không tự suy diễn số lượng hay tự ý tạo đơn."
             ])

    # =========================================================================
    # SLIDE 12: KẾT QUẢ ĐÁNH GIÁ THỰC NGHIỆM (EVALUATION SUITE)
    # =========================================================================
    s12 = prs.slides.add_slide(blank_slide_layout)
    set_slide_background(s12)
    add_header(s12, "Kết quả Đánh giá Thực nghiệm (Evaluation & Metrics)")

    add_card(s12, Inches(0.8), Inches(1.8), Inches(3.7), Inches(5.0),
             "1. Chỉ số RAG Suite (21 Cases)", [
                 "Hit@3: 100.0%",
                 "Recall@5: 97.92% (Dev 95.2%, Test 100%)",
                 "MRR (Mean Reciprocal Rank): 0.9688",
                 "Citation Resolution Rate: 100.0%",
                 "Expected Answer Fact Match: 96.43%",
                 "Retrieved Evidence Coverage: 100.0%",
                 "Safe Abstention & Access Denied: 100.0%",
                 "Mixed Route & Action Intent: 100.0%"
             ])

    add_card(s12, Inches(4.8), Inches(1.8), Inches(3.7), Inches(5.0),
             "2. Kiểm thử Tự động Toàn diện", [
                 "tests/test_rag.py: 29/29 tests PASS",
                 "  • Phân quyền pre-filter, integrity, query expansion, multi-condition.",
                 "tests/test_chatbot.py: 24/24 tests PASS",
                 "  • Multi-turn state, không nhãn, out-of-stock, idempotency, prompt injection, re-index API.",
                 "eval/run_chatbot_evaluation.py: 9/9 cases PASS (100.0%)",
                 "eval/run_evaluation.py (Inherited): 14/14 PASS"
             ])

    add_card(s12, Inches(8.8), Inches(1.8), Inches(3.7), Inches(5.0),
             "3. Phân tích 5 Lỗi & Near-misses", [
                 "1. Accented Mixed Conjunctions: Tách đúng liên từ có dấu ('và' vs 'va').",
                 "2. Return Policy Retrieval: Thêm query expansion đưa điều khoản 7 ngày vào top-3.",
                 "3. Try-on Clause: Bổ sung điều kiện nguyên tem mác khi khách hỏi mặc thử.",
                 "4. Multi-condition Shipping: Bổ sung trách nhiệm chịu phí ship hai chiều.",
                 "5. Care vs Caution FAQ: Tách và cite đúng cả 2 chunk khi hỏi cách rửa và lưu ý lò vi sóng."
             ])

    # =========================================================================
    # SLIDE 13: TỔNG KẾT & ĐỊNH HƯỚNG PRODUCTION
    # =========================================================================
    s13 = prs.slides.add_slide(blank_slide_layout)
    set_slide_background(s13)
    add_header(s13, "Tổng kết, Giới hạn Kỹ thuật & Hướng Phát triển")

    add_card(s13, Inches(0.8), Inches(1.8), Inches(5.7), Inches(5.0),
             "Thành tựu Cốt lõi của Đồ án", [
                 "Đáp ứng toàn diện các tiêu chí của mini-project RAG:",
                 "  • Xây dựng Knowledge Base tài liệu chuẩn hóa 12 docs/31 chunks có manifest.",
                 "  • Thiết kế cơ chế phân quyền RBAC đa cấp lọc trước truy xuất (Pre-filtering).",
                 "  • Định tuyến thông minh giữa tri thức RAG, thao tác giỏ hàng/đơn hàng và câu hỏi hỗn hợp.",
                 "  • Cơ chế Re-index v1.0 -> v1.1 với Hot Rollback nguyên tử và Audit Trail.",
                 "  • Nâng cấp AI Chatbot xử lý tiếng Việt đời thường linh hoạt vượt trội."
             ])

    add_card(s13, Inches(6.8), Inches(1.8), Inches(5.7), Inches(5.0),
             "Giới hạn Kỹ thuật & Hướng Production", [
                 "TÍNH MINH BẠCH VỀ GIỚI HẠN (TECHNICAL LIMITATIONS):",
                 "  • Vectorizer: Hiện dùng Lexical Hashed N-gram (1024 chiều) chạy local nhẹ; chưa dùng Neural Embedding sâu.",
                 "  • Generation: Sử dụng Template synthesis từ chunk để bảo đảm 100% grounded, triệt tiêu ảo giác.",
                 "  • Phân quyền Demo: Sử dụng shared tokens cấu hình backend, chưa tích hợp Identity Provider.",
                 "HƯỚNG MỞ RỘNG PRODUCTION:",
                 "  • Nâng cấp Semantic Embeddings đa ngôn ngữ (BGE-M3 / OpenAI text-embedding-3).",
                 "  • Tích hợp hệ thống SSO/IAM doanh nghiệp (OAuth2 / OpenID Connect).",
                 "  • Chuyển đổi lưu trữ vector sang cụm Redis / Qdrant hỗ trợ tìm kiếm phân tán."
             ])

    # Save presentation
    output_path = "D:/VSCode/Project/RAG/Presentation/RAG_Presentation.pptx"
    prs.save(output_path)
    print(f"Presentation saved successfully to: {output_path}")

if __name__ == "__main__":
    create_presentation()
