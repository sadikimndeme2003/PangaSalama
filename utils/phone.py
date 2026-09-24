"""Kubadilisha namba za simu za ndani (0712...) kuwa muundo wa kimataifa
kwa ajili ya viungo vya wa.me (WhatsApp) na tel:. Default ni Tanzania (+255)."""

import re
from urllib.parse import quote


def to_international(raw, default_country_code="255"):
    """
    '0712345678' -> '255712345678'
    '+255712345678' -> '255712345678'
    '255712345678' -> '255712345678'
    Inarudisha None kama namba haionekani sahihi.
    """
    digits = re.sub(r"\D", "", raw or "")
    if not digits:
        return None
    if digits.startswith("0"):
        digits = default_country_code + digits[1:]
    if len(digits) < 9:
        return None
    return digits


def whatsapp_link(raw_phone, message=""):
    number = to_international(raw_phone)
    if not number:
        return None
    return f"https://wa.me/{number}?text={quote(message)}"


def tel_link(raw_phone):
    number = to_international(raw_phone)
    if not number:
        return None
    return f"tel:+{number}"
