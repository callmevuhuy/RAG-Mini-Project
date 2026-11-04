"""Chat Engine - Trung tâm xử lý trí tuệ nhân tạo (AI) và luồng hội thoại đơn hàng.

Module này chịu trách nhiệm:
1. Chuẩn hóa tiếng Việt, tách thực thể người nhận (tên, sđt, địa chỉ) kể cả khi KHÔNG CÓ NHÃN.
2. Nhận diện ý định (Intent): đặt hàng, hỏi giá, kiểm tra tồn kho, sửa đơn, hủy đơn pending, handoff.
3. Quản lý trạng thái đa lượt (Multi-turn State Machine): gom slot lũy tiến, không làm mất số lượng hoặc thuộc tính đã chọn.
4. Đối chiếu Catalog SQLite: Tuyệt đối không để AI tự bịa giá, kho hoặc SKU.
5. Kiểm tra an toàn (Safety & Idempotency): Mọi side-effect đều phải qua xác thực của Backend.
"""
from __future__ import annotations

import re
import time
import unicodedata
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any
from uuid import uuid4

from sqlalchemy import select
from sqlalchemy.orm import Session, selectinload

from .models import AuditLog, ChatState, Order, OrderItem, Product, ProductVariant


# ==============================================================================
# 1. HẰNG SỐ & MÔ HÌNH DỮ LIỆU NỘI BỘ (SLOT EXTRACTION CONTRACT)
# ==============================================================================

# Thời gian tồn tại của trạng thái chờ bổ sung thông tin đơn hàng (30 phút)
PENDING_ORDER_TTL_SECONDS = 1800

# Các từ khóa nhận diện hủy đơn pending giữa chừng
CANCELLATION_KEYWORDS = [
    "thôi không mua", "thoi khong mua",
    "thôi không lấy", "thoi khong lay",
    "không mua nữa", "khong mua nua",
    "không lấy nữa", "khong lay nua",
    "không đặt nữa", "khong dat nua",
    "hủy đơn giúp", "huy don giup",
    "hủy đơn giùm", "huy don gium",
    "hủy đơn này", "huy don nay",
    "hủy đơn", "huy don",
    "hủy order", "huy order",
    "bỏ đơn", "bo don",
    "đổi ý rồi", "doi y roi",
    "thôi hủy", "thoi huy"
]

# Từ khóa định danh địa chỉ giao hàng thông dụng tại Việt Nam
ADDRESS_INDICATORS = [
    "đường", "duong", "phố", "pho", "phường", "phuong", "quận", "quan",
    "huyện", "huyen", "thị xã", "thi xa", "tỉnh", "tinh", "thành phố", "thanh pho",
    "tp.", "tp ", "hcm", "hà nội", "ha noi", "đà nẵng", "da nang",
    "q.", "q1", "q2", "q3", "q4", "q5", "q6", "q7", "q8", "q9", "q10", "q11", "q12",
    "p.", "p1", "p2", "p3", "p4", "p5", "p6", "p7", "p8", "p9", "p10",
    "số nhà", "so nha", "ngõ", "ngo", "hẻm", "hem", "tòa nhà", "chung cư",
    "street", "st.", "st ", "road", "rd", "avenue", "ave", "ward", "district", "dist."
]


@dataclass
class ContactInfo:
    """Thông tin liên lạc người nhận được bóc tách từ tin nhắn."""
    name: str | None = None
    phone: str | None = None
    address: str | None = None
    # Phần văn bản còn lại sau khi đã loại bỏ tên, sđt, địa chỉ để đối chiếu sản phẩm
    residual_text: str = ""


# ==============================================================================
# 2. BỘ CHUẨN HÓA VĂN BẢN & TIỆN ÍCH XỬ LÝ TIẾNG VIỆT
# ==============================================================================

def normalize_text(value: str) -> str:
    """Loại bỏ dấu tiếng Việt, chuyển chữ thường để so sánh đối chiếu quy tắc."""
    if not value:
        return ""
    val = value.lower().replace("đ", "d")
    normalized = unicodedata.normalize("NFD", val)
    stripped = "".join(c for c in normalized if unicodedata.category(c) != "Mn")
    return " ".join(stripped.split())


# ==============================================================================
# 3. BỘ BÓC TÁCH THỰC THỂ (SLOT EXTRACTOR - HỖ TRỢ DỮ LIỆU KHÔNG NHÃN)
# ==============================================================================

def extract_phone(text: str) -> str | None:
    """Trích xuất số điện thoại theo định dạng số Việt Nam (+84 hoặc 0...) với 8-12 số."""
    match = re.search(r"(?<!\d)(?:\+?84|0)(?:[.\s-]?\d){8,11}(?!\d)", text)
    if match:
        raw = match.group(0).strip()
        digits = re.sub(r"\D", "", raw)
        if 8 <= len(digits) <= 12:
            return raw
    # Fallback cho chuỗi số điện thoại dạng demo
    fallback = re.search(r"(?<!\d)(?:\+?\d[\d()\s.-]{6,}\d)(?!\d)", text)
    if fallback:
        raw = fallback.group(0).strip()
        digits = re.sub(r"\D", "", raw)
        if 8 <= len(digits) <= 12:
            return raw
    return None


def extract_quantity(text: str, is_awaiting_qty: bool = False) -> int | None:
    """Trích xuất số lượng mua:
    - Bắt các tiền tố hành động: 'chốt 2', 'mua 2', 'lấy 2', 'đặt 2', 'số lượng 2'
    - Bắt các hậu tố đơn vị: '2 cái', '2c', '2 chiếc', '2 áo', '2 bình', '2 hộp', '2 gói'
    - Nếu đang ở lượt hỏi riêng số lượng: bắt số nguyên đứng độc lập (1-99).
    """
    norm = normalize_text(text)

    # 1. Bắt số đứng độc lập nếu bot đang chờ số lượng hoặc tin nhắn chỉ có số
    if is_awaiting_qty or re.fullmatch(r"\s*\d{1,2}\s*", norm):
        standalone = re.search(r"\b(\d{1,2})\b", norm)
        if standalone:
            qty = int(standalone.group(1))
            if 1 <= qty <= 99:
                return qty

    # 2. Bắt cụm hành động + số lượng: 'chot 2', 'mua 1', 'lay 3', 'so luong: 2'
    action_match = re.search(r"\b(?:so luong|chot|mua|lay|dat|tang|giam)\s*[:=]?\s*(\d{1,2})\b", norm)
    if action_match:
        qty = int(action_match.group(1))
        if 1 <= qty <= 99:
            return qty

    # 3. Bắt số lượng đi kèm đơn vị tính tự nhiên tiếng Việt: '2c', '2 cái', '2 chiếc', '2 áo'
    unit_match = re.search(r"\b(\d{1,2})\s*(?:c|cai|chiec|hop|goi|ao|binh|ly|tui|bich|lon|chai|set|phan|suat)\b", norm)
    if unit_match:
        qty = int(unit_match.group(1))
        if 1 <= qty <= 99:
            return qty

    return None


def extract_contact_info(text: str) -> ContactInfo:
    """Trích xuất tên, số điện thoại và địa chỉ giao hàng.

    Hỗ trợ 2 hình thức:
    1. CÓ NHÃN: 'tên là...', 'sđt...', 'địa chỉ giao hàng...', 'gửi cho...'
    2. KHÔNG NHÃN: 'Nguyễn Văn An, 0901234567, 123 Lê Lợi, Phường Bến Nghé, Quận 1'

    Đồng thời tính toán `residual_text` (văn bản đã loại bỏ thông tin liên lạc)
    để không bị nhầm tên người (ví dụ: 'Trần Bình') thành sản phẩm ('Bình giữ nhiệt').
    """
    phone = extract_phone(text)
    name: str | None = None
    address: str | None = None

    residual = text
    if phone:
        residual = residual.replace(phone, " ")

    # 1. BÓC TÁCH CÓ NHÃN RÕ RÀNG
    name_label_match = re.search(
        r"(?i)(?:tên(?: người nhận| khách hàng)?|ten(?: nguoi nhan| khach hang)?|người nhận|nguoi nhan|gửi cho|gui cho|giao cho|cho bạn|cho anh|cho chị|cho em|họ tên|ho ten)\s*(?:là|la|:|-)?\s*([^,;.]{2,80})",
        residual
    )
    if name_label_match:
        cand_name = name_label_match.group(1).strip()
        cand_name = re.sub(r"^(?:là|la|:|-)\s*", "", cand_name, flags=re.I).strip()
        words = cand_name.split()
        if words and words[0].lower() in ("tôi", "toi", "minh", "em"):
            if len(words) > 1 and words[1][0].isupper():
                cand_name = " ".join(words[1:])
            else:
                cand_name = ""
        # Đảm bảo không nhầm địa chỉ bắt đầu bằng 'đến...', 'về...' hoặc 'ở...'
        if cand_name and not re.search(r"\b(?:den|ve|o)\b", normalize_text(cand_name)):
            name = cand_name
            residual = residual.replace(name_label_match.group(0), " ")

    addr_label_match = re.search(
        r"(?i)(?:địa chỉ(?: giao hàng)?|dia chi(?: giao hang)?|giao đến|giao về|giao den|giao ve|ship đến|ship den|nhận tại|nhan tai)\s*(?:là|la|:|-)?\s*([^;.]{6,300})",
        residual
    )
    if addr_label_match:
        cand_addr = addr_label_match.group(1).strip()
        cand_addr = re.sub(r"^(?:là|la|:|-)\s*", "", cand_addr, flags=re.I).strip()
        if cand_addr:
            address = cand_addr
            residual = residual.replace(addr_label_match.group(0), " ")

    # 2. BÓC TÁCH KHÔNG NHÃN (UNLABELED HEURISTIC)
    if not name or not address:
        segments = [s.strip() for s in re.split(r"[,;\n]|\bva giao ve\b|\bva giao den\b", text) if s.strip()]

        # Tìm phân đoạn là Tên trước nếu chưa có
        if not name:
            for seg in segments:
                if phone and phone in seg:
                    seg_clean = seg.replace(phone, "").strip(" -:,")
                else:
                    seg_clean = seg.strip(" -:,")
                if not seg_clean:
                    continue
                norm_seg = normalize_text(seg_clean)
                words = seg_clean.split()
                has_action = any(k in norm_seg for k in ("chot", "mua", "lay", "dat", "ao", "binh", "ca phe", "gia", "ton", "size", "mau", "don", "order", "shop"))
                has_addr = any(ind in norm_seg for ind in ADDRESS_INDICATORS)
                if 2 <= len(words) <= 4 and not has_action and not has_addr:
                    if sum(1 for w in words if w and w[0].isupper()) >= len(words) - 1:
                        name = seg_clean
                        residual = residual.replace(seg, " ")
                        break

        # Tìm Địa chỉ nếu chưa có
        if not address:
            addr_segments = []
            for seg in segments:
                if phone and phone in seg:
                    seg_clean = seg.replace(phone, "").strip(" -:,")
                else:
                    seg_clean = seg.strip(" -:,")
                if not seg_clean or (name and seg_clean == name):
                    continue
                norm_seg = normalize_text(seg_clean)
                has_action = any(k in norm_seg for k in ("chot", "mua", "lay", "dat", "ao", "binh", "ca phe", "don", "order", "shop"))
                has_addr_ind = any(ind in norm_seg for ind in ADDRESS_INDICATORS)
                has_digits = bool(re.search(r"\d", seg_clean))
                has_product_word = any(k in norm_seg for k in ("ao", "binh", "ca phe", "hat", "phin", "size", "mau", "den", "trang", "xanh", "hong", "kem"))
                if (has_addr_ind or has_digits or (len(segments) > 1 and not has_product_word)) and not has_action:
                    addr_segments.append(seg_clean)
                    residual = residual.replace(seg, " ")

            if addr_segments:
                address = ", ".join(addr_segments)

    residual = " ".join(residual.split())
    return ContactInfo(name=name, phone=phone, address=address, residual_text=residual)


def extract_cancellation(text: str) -> bool:
    """Kiểm tra người dùng có muốn hủy đơn nháp đang chờ xử lý hay không."""
    norm = normalize_text(text)
    return any(kw in norm for kw in CANCELLATION_KEYWORDS)


# ==============================================================================
# 4. BỘ ĐỐI CHIẾU DANH MỤC & BIẾN THỂ (CATALOG & VARIANT RESOLUTION)
# ==============================================================================

# Danh sách các trang phục / phụ kiện loại trừ (không bán tại shop) để tránh nhận diện nhầm từ "áo" (Issue 13, 14)
EXCLUDED_GARMENTS = (
    "ao khoac", "ao so mi", "ao len", "ao mua", "ao vest", "ao polo",
    "quan", "quan jean", "quan tay", "quan short", "giay", "dep", "non", "mu"
)


def resolve_catalog_candidates(
    search_text: str,
    active_products: list[Product]
) -> list[Product]:
    """Tìm kiếm sản phẩm trong danh mục database SQLite theo tên hoặc alias.

    Sử dụng search_text đã loại trừ thông tin liên lạc để tránh đối chiếu sai lệch.
    Hỗ trợ nhận diện cách gọi đời thường của khách hàng (ví dụ 'áo trắng', 'áo màu xanh' -> Áo thun basic cotton).
    """
    norm_query = normalize_text(search_text)
    candidates = []

    # Kiểm tra xem câu chat có chứa từ "áo" hợp lệ (không thuộc danh mục bị loại trừ)
    has_excluded_garment = any(ex in norm_query for ex in EXCLUDED_GARMENTS)
    has_ao_word = bool(re.search(r"\bao\b", norm_query)) and not has_excluded_garment

    # Từ khóa mở rộng an toàn đặc thù từng sản phẩm trong danh mục
    PRODUCT_SHORT_KEYWORDS = {
        "Áo thun basic cotton": ["ao thun", "ao basic", "ao cotton", "ao phong", "cai ao", "chiec ao"],
        "Bình giữ nhiệt Everyday": ["binh giu nhiet", "binh nuoc", "binh inox", "binh everyday", "binh"],
        "Cà phê rang xay Đà Lạt": ["ca phe", "cafe", "coffee", "rang xay"]
    }

    for product in active_products:
        # Nếu khách gọi chung là "áo" hoặc "áo trắng", "áo màu xanh" và shop chỉ có duy nhất 1 dòng áo thun
        if product.name == "Áo thun basic cotton" and has_ao_word:
            candidates.append(product)
            continue

        names = [product.name, *(product.aliases or [])]
        extra_keywords = PRODUCT_SHORT_KEYWORDS.get(product.name, [])
        all_terms = names + extra_keywords
        norm_names = [normalize_text(n) for n in all_terms if n]

        # 1. So khớp trực tiếp chuỗi con có ranh giới từ
        if any(re.search(rf"\b{re.escape(name)}\b", norm_query) for name in norm_names):
            candidates.append(product)
        else:
            # 2. So khớp từ khóa tập hợp (ít nhất 2 từ khóa trùng khớp)
            query_words = set(norm_query.split())
            if any(len(query_words & set(name.split())) >= 2 for name in norm_names):
                candidates.append(product)

    return candidates


def resolve_variant(
    product: Product,
    message: str,
    pending_variant_attrs: dict[str, str] | None = None
) -> tuple[ProductVariant | None, dict[str, str]]:
    """Xác định biến thể (Variant) của sản phẩm dựa trên thuộc tính: màu sắc, size, dung tích, trọng lượng, kiểu xay.

    Hỗ trợ gom lũy tiến: kết hợp thuộc tính từ pending state (ví dụ size M ở turn 1)
    với thuộc tính mới xuất hiện ở tin nhắn hiện tại (màu Xanh ở turn 2).
    """
    norm_msg = normalize_text(message)
    accumulated_attrs = dict(pending_variant_attrs or {})

    # 1. Quét tìm các thuộc tính xuất hiện trong tin nhắn hiện tại
    all_possible_attrs: dict[str, set[str]] = {}
    for v in product.variants:
        for attr_key, attr_val in (v.attributes or {}).items():
            all_possible_attrs.setdefault(attr_key, set()).add(attr_val)

    for attr_key, attr_vals in all_possible_attrs.items():
        for val in attr_vals:
            norm_val = normalize_text(val)
            pattern = rf"(?<!\w){re.escape(norm_val)}(?!\w)"
            if re.search(pattern, norm_msg):
                accumulated_attrs[attr_key] = val
                break

    # 2. Tìm biến thể khớp với tất cả thuộc tính đã tích lũy
    matching_variants = []
    for v in product.variants:
        v_attrs = v.attributes or {}
        # Biến thể khớp nếu tất cả thuộc tính trong accumulated_attrs đều trùng khớp
        if all(v_attrs.get(k) == val for k, val in accumulated_attrs.items()):
            matching_variants.append(v)

    # Nếu chỉ còn đúng 1 biến thể duy nhất và người dùng đã cung cấp thuộc tính nhận diện (Issue 15)
    # Ví dụ: Bình giữ nhiệt màu đen chỉ có duy nhất 1 biến thể (Đen, 750ml), không bắt khách xác nhận lặp lại
    if len(matching_variants) == 1 and accumulated_attrs:
        matched = matching_variants[0]
        full_attrs = dict(matched.attributes or {})
        return matched, full_attrs

    return None, accumulated_attrs


# ==============================================================================
# 5. MÁY TRẠNG THÁI HỘI THOẠI ĐA LƯỢT (MULTI-TURN CHAT ORCHESTRATION)
# ==============================================================================

async def process_chat_turn(
    message: str,
    db: Session,
    session_id: int,
    request_id: str,
    client_message_id: str,
    rag_mixed_res: dict[str, Any] | None = None
) -> dict[str, Any]:
    """Hàm điều phối trung tâm xử lý một lượt chat của khách hàng.

    Quy trình chặt chẽ:
    1. Kiểm tra lệnh hủy pending order (`cancel_pending`).
    2. Bóc tách thực thể người nhận (kể cả không nhãn) và số lượng.
    3. Tra cứu danh mục và phân loại biến thể từ SQLite.
    4. Cập nhật và bảo toàn trạng thái pending (không mất số lượng, không mất thuộc tính).
    5. Chỉ ghi đơn nháp vào DB khi đầy đủ mọi trường và kho hàng còn đáp ứng.
    """
    now = int(time.time())

    # 1. NẠP TRẠNG THÁI PENDING HIỆN CÓ CỦA SESSION
    state = db.scalar(select(ChatState).where(ChatState.session_id == session_id))
    pending = dict(state.pending_order or {}) if state and state.expires_at > now else {}
    if state and state.expires_at <= now:
        db.delete(state)
        db.flush()
        state = None
        pending = {}

    norm_msg = normalize_text(message)

    # 2. XỬ LÝ LỆNH HỦY Ý ĐỊNH ĐẶT HÀNG (CANCEL PENDING)
    if pending and extract_cancellation(message):
        if state:
            db.delete(state)
            db.commit()
        return {
            "route": "answer",
            "intent": "cancel_pending",
            "message": "Đã hủy yêu cầu đặt hàng đang chờ của bạn. Nếu cần tư vấn thêm sản phẩm hoặc chính sách khác, bạn cứ nhắn mình nhé!"
        }

    # 3. TRÍCH XUẤT THỰC THỂ LIÊN LẠC & SỐ LƯỢNG
    is_awaiting_qty = bool(pending and not pending.get("quantity"))
    contact = extract_contact_info(message)
    quantity = extract_quantity(message, is_awaiting_qty=is_awaiting_qty)
    order_ref_match = re.search(r"(?:don|order)\s*(?:#|ma)?\s*([a-f0-9]{8,32})", message, re.I)

    # 4. NHẬN DIỆN Ý ĐỊNH (INTENT RECOGNITION)
    pending_has_variant_match = False
    if pending.get("product_id"):
        p_obj = db.scalar(select(Product).where(Product.id == pending["product_id"]).options(selectinload(Product.variants)))
        if p_obj:
            for v in p_obj.variants:
                for val in (v.attributes or {}).values():
                    if normalize_text(val) in norm_msg:
                        pending_has_variant_match = True
                        break

    # Nhận diện phản hồi đồng thuận / xác nhận (Affirmation - Issue 15)
    is_affirmation = any(
        re.search(rf"\b{re.escape(k)}\b", norm_msg)
        for k in ("yes", "yep", "ok", "oke", "dung roi", "chinh xac", "chinh no", "dong y", "chot", "dung")
    )

    if any(k in norm_msg for k in ("nhan vien", "gap nguoi", "ho tro truc tiep", "khieu nai")):
        intent = "unknown_or_handoff"
    elif any(k in norm_msg for k in ("sua don", "doi don", "cap nhat don", "tang so luong", "giam so luong")):
        intent = "update_order"
    elif any(k in norm_msg for k in ("con hang", "ton kho", "co hang", "co size", "con size", "het hang", "con bao nhieu", "con bn", "con may", "trong kho", "kiem tra kho", "co san", "con khong", "con ko", "so luong con", "so luong ton", "shop co", "shop con", "nhung loai", "cac loai", "loai nao", "dang tim", "tim mua")):
        intent = "check_stock"
    elif re.search(r"\b(?:gia|bao nhieu tien|bao nhieu vnd|gia sao|gia the nao)\b", norm_msg):
        intent = "check_price"
    elif any(k in norm_msg for k in ("dat mua", "dat hang", "muon dat", "muon mua", "toi muon mua", "minh muon mua", "muon lay", "dat ", "mua ", "chot ", "lay ", "cho toi", "cho minh", "them vao don")):
        intent = "create_order"
    elif pending and (contact.phone or contact.name or contact.address or quantity or pending_has_variant_match or is_affirmation):
        # Nếu đang có pending order và người dùng gửi thông tin bổ sung (kể cả chọn biến thể hoặc xác nhận) -> tiếp tục luồng tạo đơn
        intent = "create_order"
    else:
        intent = "unknown_or_handoff"

    # 5. ĐỐI CHIẾU DANH MỤC SẢN PHẨM (CATALOG MATCHING TỪ SQLITE)
    active_products = db.scalars(
        select(Product).where(Product.active.is_(True)).options(
            selectinload(Product.variants).selectinload(ProductVariant.inventory)
        )
    ).all()

    # Sử dụng chuỗi đã tách thông tin liên lạc để tìm sản phẩm
    search_query = contact.residual_text if contact.residual_text else message
    candidates = resolve_catalog_candidates(search_query, active_products)

    # Nếu đang có pending order và lượt này người dùng không nhắc đến sản phẩm mới,
    # giữ nguyên sản phẩm đã chọn từ pending order
    if pending.get("product_id") and not candidates:
        saved_prod = db.scalar(
            select(Product).where(Product.id == pending["product_id"]).options(
                selectinload(Product.variants).selectinload(ProductVariant.inventory)
            )
        )
        if saved_prod:
            candidates = [saved_prod]

    # 6. ĐIỀU PHỐI HÀNH ĐỘNG DỰA TRÊN Ý ĐỊNH

    # --- NHÁNH: CẬP NHẬT ĐƠN HÀNG ĐANG CHỜ XÁC NHẬN ---
    if intent == "update_order":
        orders = db.scalars(
            select(Order).where(
                Order.session_id == session_id,
                Order.status == "pending_confirmation"
            ).options(selectinload(Order.items))
        ).all()
        ref = (order_ref_match.group(1) if order_ref_match else "").lower()
        matched = [o for o in orders if not ref or o.id.lower().startswith(ref)]

        if len(matched) == 1 and len(matched[0].items) == 1 and quantity:
            order = matched[0]
            item = order.items[0]
            variant = db.scalar(
                select(ProductVariant).where(ProductVariant.sku == item.sku).options(
                    selectinload(ProductVariant.inventory)
                )
            )
            available = variant.inventory.available_quantity if variant and variant.inventory else 0
            if quantity > available:
                return {
                    "route": "out_of_stock",
                    "intent": intent,
                    "message": f"Kho hiện chỉ còn {available} sản phẩm; mình chưa thể cập nhật số lượng thành {quantity}."
                }
            else:
                item.quantity = quantity
                item.unit_price_snapshot = variant.unit_price
                order.total_amount = quantity * variant.unit_price
                db.add(AuditLog(
                    request_id=request_id,
                    order_id=order.id,
                    actor_session_id=session_id,
                    action="order.updated_from_chat",
                    details={"quantity": quantity, "total_amount": order.total_amount},
                    created_at=datetime.now(timezone.utc)
                ))
                db.commit()
                return {
                    "route": "updated_order",
                    "intent": intent,
                    "order_id": order.id,
                    "message": f"Đã cập nhật đơn nháp #{order.id[:10].upper()} thành số lượng {quantity}. Tổng mới {order.total_amount:,}₫; đơn vẫn chờ xác nhận."
                }
        else:
            return {
                "route": "needs_information",
                "intent": intent,
                "message": "Mình chỉ có thể sửa đơn nháp đang chờ xác nhận. Vui lòng gửi mã đơn (10 ký tự đầu) và số lượng mới; nếu có nhiều sản phẩm cần chỉ rõ sản phẩm."
            }

    # --- NHÁNH: HỎI GIÁ HOẶC KIỂM TRA TỒN KHO ---
    if intent in ("check_price", "check_stock"):
        if len(candidates) == 0:
            avail_names = ", ".join(p.name for p in active_products)
            return {
                "route": "answer",
                "intent": intent,
                "message": f"Hiện tại shop chưa có sản phẩm này. Bạn có thể tham khảo các sản phẩm hiện có của shop: {avail_names}."
            }
        if len(candidates) > 1:
            return {
                "route": "needs_information",
                "intent": intent,
                "message": f"Bạn muốn hỏi về sản phẩm nào trong các sản phẩm sau: {', '.join(p.name for p in candidates)}?"
            }

        product = candidates[0]
        variant, accumulated_attrs = resolve_variant(product, message, pending.get("variant_attributes"))

        # Kiểm tra nếu người dùng đang tìm kiếm / hỏi tư vấn sản phẩm chung chung
        is_discovery = any(k in norm_msg for k in ("dang tim", "tim ca phe", "tim ao", "tim binh", "tim mua"))
        if is_discovery and not variant and not accumulated_attrs:
            min_price = min(v.unit_price for v in product.variants)
            max_price = max(v.unit_price for v in product.variants)
            return {
                "route": "answer",
                "intent": "check_price",
                "message": f"Shop có sản phẩm {product.name} (giá từ {min_price:,}₫ đến {max_price:,}₫). {product.description} Bạn muốn chọn phân loại nào để shop tư vấn nhé?"
            }

        # Kiểm tra nếu hỏi danh sách các loại ("còn những loại nào", "có các loại nào", "những loại cà phê nào")
        is_asking_all_types = any(k in norm_msg for k in ("nhung loai", "cac loai", "loai nao"))
        if is_asking_all_types and not variant:
            details = "; ".join(
                f"{', '.join((v.attributes or {}).values())} ({v.unit_price:,}₫: còn {v.inventory.available_quantity if v.inventory else 0})"
                for v in product.variants
            )
            return {
                "route": "answer",
                "intent": "check_stock",
                "message": f"Hiện tại shop có {product.name} với các phân loại: {details}."
            }

        # Kiểm tra nếu người dùng chọn tổ hợp thuộc tính không tồn tại hoặc chỉ khớp 1 phần
        if accumulated_attrs and not variant:
            matching_sub = [
                v for v in product.variants
                if all(v.attributes.get(k) == val for k, val in accumulated_attrs.items() if k in v.attributes)
            ]
            if not matching_sub:
                suggestions = []
                for k, val in accumulated_attrs.items():
                    sub = [v for v in product.variants if v.attributes.get(k) == val]
                    if sub:
                        other_attrs = [f"{', '.join(v.attributes.values())} (còn {v.inventory.available_quantity if v.inventory else 0})" for v in sub]
                        suggestions.append(f"{val} hiện có: {'; '.join(other_attrs)}")
                sug_str = ". ".join(suggestions)
                return {
                    "route": "answer",
                    "intent": "check_stock",
                    "message": f"{product.name} hiện không có phân loại {', '.join(accumulated_attrs.values())}. {sug_str}."
                }
            else:
                details = "; ".join(
                    f"{', '.join(v.attributes.values())}: còn {v.inventory.available_quantity if v.inventory else 0}"
                    for v in matching_sub
                )
                if len(matching_sub) == 1:
                    v = matching_sub[0]
                    return {
                        "route": "answer",
                        "intent": "check_stock",
                        "message": f"Shop có {product.name} ({', '.join(v.attributes.values())}) - hiện còn {v.inventory.available_quantity if v.inventory else 0} sản phẩm trong kho bạn nhé."
                    }
                else:
                    return {
                        "route": "answer",
                        "intent": "check_stock",
                        "message": f"Shop còn các phân loại sau của {product.name}: {details}. Bạn muốn chọn phân loại nào?"
                    }

        if intent == "check_price":
            is_discount_query = any(k in norm_msg for k in ("giam gia", "chiet khau", "bot", "ma giam gia", "voucher", "uu dai"))
            if is_discount_query:
                if variant:
                    v_desc = f"{product.name} ({', '.join(variant.attributes.values())})"
                    if quantity and quantity > 1:
                        total = quantity * variant.unit_price
                        msg = f"{v_desc} hiện có giá niêm yết {variant.unit_price:,}₫/chiếc (tổng {quantity} chiếc là {total:,}₫). Hiện shop bán đúng giá niêm yết và chưa áp dụng giảm giá thêm cho số lượng này bạn nhé."
                    else:
                        msg = f"{v_desc} hiện có giá niêm yết {variant.unit_price:,}₫. Hiện shop bán đúng giá niêm yết và chưa áp dụng chương trình giảm giá bạn nhé."
                else:
                    unique_prices = sorted(list(set(v.unit_price for v in product.variants)))
                    p_str = f"{unique_prices[0]:,}₫" if len(unique_prices) == 1 else f"từ {unique_prices[0]:,}₫ đến {unique_prices[-1]:,}₫"
                    msg = f"Hiện shop bán đúng giá niêm yết ({p_str} tùy phân loại) và chưa áp dụng chương trình giảm giá cho {product.name} bạn nhé."
                return {
                    "route": "answer",
                    "intent": intent,
                    "message": msg
                }

            if variant:
                return {
                    "route": "answer",
                    "intent": intent,
                    "message": f"{product.name} ({', '.join(variant.attributes.values())}) có giá {variant.unit_price:,}₫."
                }
            unique_prices = sorted(list(set(v.unit_price for v in product.variants)))
            p_str = f"{unique_prices[0]:,}₫" if len(unique_prices) == 1 else f"từ {unique_prices[0]:,}₫ đến {unique_prices[-1]:,}₫"
            return {
                "route": "answer",
                "intent": intent,
                "message": f"{product.name} có giá {p_str} tùy phân loại. Bạn muốn xem phân loại nào?"
            }
        elif intent == "check_stock":
            if variant:
                return {
                    "route": "answer",
                    "intent": intent,
                    "message": f"Tình trạng hàng của {product.name} ({', '.join(variant.attributes.values())}): còn {variant.inventory.available_quantity if variant.inventory else 0}."
                }
            stock_variants = product.variants
            details = "; ".join(
                f"{', '.join((v.attributes or {}).values()) or v.sku}: còn {v.inventory.available_quantity if v.inventory else 0}"
                for v in stock_variants
            )
            return {
                "route": "answer",
                "intent": intent,
                "message": f"Tình trạng hàng của {product.name}: {details}." + ("" if variant else " Bạn muốn kiểm tra phân loại cụ thể nào?")
            }

    # --- NHÁNH: ĐẶT HÀNG & GOM SLOT ĐA LƯỢT (CREATE ORDER) ---
    if intent == "create_order":
        if len(candidates) != 1:
            return {
                "route": "needs_information",
                "intent": intent,
                "message": "Bạn muốn hỏi về sản phẩm nào? Hãy gửi tên sản phẩm để mình tra cứu chính xác."
            }

        product = candidates[0]
        pending["product_id"] = product.id
        pending["product_name"] = product.name

        # Nhận diện biến thể và bảo toàn thuộc tính đã chọn
        variant, accumulated_attrs = resolve_variant(product, message, pending.get("variant_attributes"))
        pending["variant_attributes"] = accumulated_attrs

        # Bảo toàn số lượng: Nếu lượt này không gửi số lượng mới, giữ nguyên số lượng đã ghi nhận trước đó
        if quantity:
            pending["quantity"] = quantity

        # Cập nhật thông tin người nhận nếu có
        if contact.name:
            pending["name"] = contact.name
        if contact.phone:
            pending["phone"] = contact.phone
        if contact.address:
            pending["address"] = contact.address

        # 1. Kiểm tra phân loại sản phẩm (variant)
        # Nếu khách xác nhận đồng thuận (yes/ok/đúng rồi) và danh sách lựa chọn phù hợp chỉ có 1 biến thể -> chốt biến thể đó ngay
        if variant is None and is_affirmation and pending.get("product_id"):
            matching_opts = [
                v for v in product.variants
                if all(v.attributes.get(k) == val for k, val in accumulated_attrs.items())
            ] if accumulated_attrs else product.variants
            if len(matching_opts) == 1:
                variant = matching_opts[0]
                accumulated_attrs = dict(variant.attributes or {})
                pending["variant_attributes"] = accumulated_attrs

        if variant is None:
            # Lưu state để chờ khách chọn phân loại
            if state is None:
                state = ChatState(session_id=session_id, pending_order=pending, expires_at=now + PENDING_ORDER_TTL_SECONDS)
                db.add(state)
            else:
                state.pending_order = pending
                state.expires_at = now + PENDING_ORDER_TTL_SECONDS
            db.commit()

            matching_opts = [
                v for v in product.variants
                if all(v.attributes.get(k) == val for k, val in accumulated_attrs.items())
            ] if accumulated_attrs else product.variants
            target_list = matching_opts if matching_opts else product.variants
            options = "; ".join(", ".join(v.attributes.values()) for v in target_list)
            return {
                "route": "needs_information",
                "intent": intent,
                "message": f"{product.name} có nhiều phân loại. Bạn muốn chọn: {options}?"
            }

        # Đã xác định được SKU cụ thể
        pending["sku"] = variant.sku

        # Kiểm tra tồn kho ngay lập tức: nếu phân loại đã hết hàng (available <= 0)
        available = variant.inventory.available_quantity if variant.inventory else 0
        if available <= 0:
            avail_options = "; ".join(
                f"{', '.join(v.attributes.values())}: còn {v.inventory.available_quantity}"
                for v in product.variants if v.inventory and v.inventory.available_quantity > 0
            )
            return {
                "route": "out_of_stock",
                "intent": intent,
                "message": f"Phân loại {product.name} ({', '.join(variant.attributes.values())}) hiện đã hết hàng. Bạn có muốn đổi sang phân loại khác còn hàng không ({avail_options})?"
            }

        # 2. Kiểm tra số lượng
        qty = pending.get("quantity")
        if qty is None:
            # Lưu state và yêu cầu số lượng + các trường còn thiếu
            missing = ["số lượng"] + [
                label for key, label in (("name", "tên người nhận"), ("phone", "số điện thoại"), ("address", "địa chỉ giao hàng"))
                if not pending.get(key)
            ]
            if state is None:
                state = ChatState(session_id=session_id, pending_order=pending, expires_at=now + PENDING_ORDER_TTL_SECONDS)
                db.add(state)
            else:
                state.pending_order = pending
                state.expires_at = now + PENDING_ORDER_TTL_SECONDS
            db.commit()

            variant_desc = ", ".join(variant.attributes.values())
            return {
                "route": "needs_information",
                "intent": intent,
                "message": f"Bạn muốn đặt {product.name} ({variant_desc}). Vui lòng gửi {', '.join(missing)}."
            }

        # 3. Kiểm tra số lượng đặt so với tồn kho
        if qty > available:
            return {
                "route": "out_of_stock",
                "intent": intent,
                "message": f"Phân loại này hiện còn {available} sản phẩm, nên chưa thể đặt {qty}."
            }

        # 4. Kiểm tra thông tin nhận hàng bắt buộc (tên, sđt, địa chỉ)
        missing_contact = [
            label for key, label in (("name", "tên người nhận"), ("phone", "số điện thoại"), ("address", "địa chỉ giao hàng"))
            if not pending.get(key)
        ]

        if missing_contact:
            # Lưu state chờ khách bổ sung thông tin nhận hàng
            if state is None:
                state = ChatState(session_id=session_id, pending_order=pending, expires_at=now + PENDING_ORDER_TTL_SECONDS)
                db.add(state)
            else:
                state.pending_order = pending
                state.expires_at = now + PENDING_ORDER_TTL_SECONDS
            db.commit()

            variant_desc = ", ".join(variant.attributes.values())
            return {
                "route": "needs_information",
                "intent": intent,
                "message": f"Mình đã ghi nhận {qty} × {product.name} ({variant_desc}). Để tạo đơn nháp, bạn vui lòng gửi {', '.join(missing_contact)}."
            }

        # 5. TẤT CẢ SLOTS ĐÃ ĐẦY ĐỦ -> TẠO ĐƠN HÀNG NHÁP (DRAFT ORDER)
        order = Order(
            id=uuid4().hex,
            session_id=session_id,
            status="pending_confirmation",
            recipient_name=pending["name"],
            phone_number=pending["phone"],
            delivery_address=pending["address"],
            total_amount=qty * variant.unit_price,
            created_at=datetime.now(timezone.utc)
        )
        order.items.append(OrderItem(
            sku=variant.sku,
            product_name_snapshot=product.name,
            variant_snapshot=variant.attributes or {},
            quantity=qty,
            unit_price_snapshot=variant.unit_price
        ))
        db.add(order)
        db.flush()

        # Ghi nhật ký kiểm toán (Audit Trail)
        db.add(AuditLog(
            request_id=request_id,
            order_id=order.id,
            actor_session_id=session_id,
            action="order.created_from_chat",
            details={"item_count": 1, "total_amount": order.total_amount},
            created_at=datetime.now(timezone.utc)
        ))

        # Xóa pending state sau khi đã tạo đơn nháp thành công
        if state:
            db.delete(state)
        db.commit()

        variant_desc = f" ({', '.join(variant.attributes.values())})" if (variant and variant.attributes) else ""
        return {
            "route": "pending_confirmation",
            "intent": intent,
            "order_id": order.id,
            "message": (
                f"Đã tạo đơn nháp #{order.id[:10].upper()} cho {qty} × {product.name}{variant_desc}, tổng {order.total_amount:,}₫.\n"
                f"Thông tin người nhận:\n"
                f"- Tên người nhận: {order.recipient_name}\n"
                f"- Số điện thoại: {order.phone_number}\n"
                f"- Địa chỉ giao hàng: {order.delivery_address}\n"
                f"Đơn đang chờ xác nhận; chưa thanh toán hoặc trừ kho."
            )
        }

    # --- NHÁNH: HANDOFF HOẶC KHÔNG XÁC ĐỊNH ĐƯỢC Ý ĐỊNH ---
    return {
        "route": "handoff",
        "intent": intent,
        "message": "Yêu cầu này cần nhân viên hỗ trợ trực tiếp. Mình đã ghi nhận và chuyển tiếp thông tin tới bộ phận chăm sóc khách hàng; bạn có thể tiếp tục hỏi về sản phẩm, chính sách hoặc đơn hàng nhé."
    }
