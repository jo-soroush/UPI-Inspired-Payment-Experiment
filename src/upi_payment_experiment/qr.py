"""C05 merchant QR generation, decoding, and strict payload parsing."""

from urllib.parse import parse_qsl, urlencode, urlsplit

import zxingcpp


QR_SCHEME = "upi-demo"
QR_AUTHORITY = "pay"
QR_MERCHANT_FIELD = "merchant_id"


class QrError(Exception):
    """Base class for controlled QR application errors."""

    code = "QR_ERROR"


class InvalidQrPayloadError(QrError, ValueError):
    """The decoded QR text does not satisfy the canonical C05 contract."""

    code = "INVALID_QR_PAYLOAD"


class QrGenerationError(QrError):
    """A real QR symbol could not be generated."""

    code = "QR_GENERATION_FAILED"


class QrDecodingError(QrError):
    """A QR image could not be decoded."""

    code = "QR_DECODING_FAILED"


def build_merchant_qr_payload(merchant_id: str) -> str:
    """Build the sole canonical C05 merchant QR URI."""

    if not isinstance(merchant_id, str) or not merchant_id.strip():
        raise InvalidQrPayloadError("merchant_id must be a non-empty string")
    query = urlencode(((QR_MERCHANT_FIELD, merchant_id),))
    return f"{QR_SCHEME}://{QR_AUTHORITY}?{query}"


def parse_merchant_qr_payload(payload: str) -> str:
    """Return merchant_id only when payload exactly matches the C05 contract."""

    if not isinstance(payload, str) or not payload:
        raise InvalidQrPayloadError("QR payload must be a non-empty string")
    if _has_ascii_control_character(payload):
        raise InvalidQrPayloadError("QR payload contains ASCII control characters")
    if _has_raw_fragment_delimiter(payload):
        raise InvalidQrPayloadError("QR fragments are not allowed")

    raw_scheme, separator, _ = payload.partition(":")
    if separator != ":" or raw_scheme != QR_SCHEME:
        raise InvalidQrPayloadError("QR scheme must be exactly 'upi-demo'")

    try:
        parsed = urlsplit(payload)
        if _has_invalid_percent_encoding(parsed.query):
            raise ValueError("invalid percent encoding")
        query_items = parse_qsl(
            parsed.query,
            keep_blank_values=True,
            strict_parsing=True,
            encoding="utf-8",
            errors="strict",
        )
    except (TypeError, ValueError) as error:
        raise InvalidQrPayloadError("QR payload is malformed") from error

    if parsed.scheme != QR_SCHEME:
        raise InvalidQrPayloadError("QR scheme must be exactly 'upi-demo'")
    if parsed.netloc != QR_AUTHORITY:
        raise InvalidQrPayloadError("QR authority must be exactly 'pay'")
    if parsed.path:
        raise InvalidQrPayloadError("QR path must be empty")
    if parsed.fragment:
        raise InvalidQrPayloadError("QR fragments are not allowed")
    if any(
        _has_ascii_control_character(component)
        for query_item in query_items
        for component in query_item
    ):
        raise InvalidQrPayloadError(
            "QR query contains decoded ASCII control characters"
        )
    if len(query_items) != 1 or query_items[0][0] != QR_MERCHANT_FIELD:
        raise InvalidQrPayloadError(
            "QR query must contain exactly one merchant_id parameter"
        )

    merchant_id = query_items[0][1]
    if not merchant_id.strip():
        raise InvalidQrPayloadError("merchant_id must be non-empty")
    return merchant_id


def _has_ascii_control_character(value: str) -> bool:
    """Reject raw characters that URI parsing may silently normalize away."""

    return any(ord(character) < 32 or ord(character) == 127 for character in value)


def _has_raw_fragment_delimiter(value: str) -> bool:
    """Reject a fragment delimiter even when its fragment text is empty."""

    return "#" in value


def _has_invalid_percent_encoding(value: str) -> bool:
    """Return whether a URI component contains an invalid percent escape."""

    hexadecimal = frozenset("0123456789abcdefABCDEF")
    index = 0
    while index < len(value):
        if value[index] == "%":
            if index + 2 >= len(value):
                return True
            if (
                value[index + 1] not in hexadecimal
                or value[index + 2] not in hexadecimal
            ):
                return True
            index += 3
            continue
        index += 1
    return False


def generate_merchant_qr(merchant_id: str) -> zxingcpp.Image:
    """Generate a real QR image for one canonical merchant payload."""

    payload = build_merchant_qr_payload(merchant_id)
    try:
        barcode = zxingcpp.create_barcode(
            payload,
            zxingcpp.BarcodeFormat.QRCode,
        )
        return barcode.to_image(scale=5, add_quiet_zones=True)
    except Exception as error:
        raise QrGenerationError("merchant QR generation failed") from error


def decode_merchant_qr(image: object) -> str:
    """Decode a real QR image and return its strictly validated merchant ID."""

    try:
        barcode = zxingcpp.read_barcode(
            image,
            formats=zxingcpp.BarcodeFormat.QRCode,
            is_pure=True,
        )
    except Exception as error:
        raise QrDecodingError("merchant QR decoding failed") from error

    if barcode is None:
        raise QrDecodingError("no QR code could be decoded")
    return parse_merchant_qr_payload(barcode.text)
