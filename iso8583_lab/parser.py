"""Small ISO 8583 message lab.

This is intentionally limited: ASCII messages, a subset of fixed/LLVAR fields,
no BCD, no MAC, no network connection. It exists to practise MTI, bitmap,
field parsing and response codes with synthetic data.
"""

from __future__ import annotations

from typing import Any

# field -> (type, max_length, length_kind)
FIELD_SPECS: dict[int, tuple[str, int, str]] = {
    2: ("n", 19, "LLVAR"),
    3: ("n", 6, "FIXED"),
    4: ("n", 12, "FIXED"),
    7: ("n", 10, "FIXED"),
    11: ("n", 6, "FIXED"),
    12: ("n", 6, "FIXED"),
    13: ("n", 4, "FIXED"),
    37: ("an", 12, "FIXED"),
    38: ("an", 6, "FIXED"),
    39: ("an", 2, "FIXED"),
    41: ("an", 8, "FIXED"),
    42: ("an", 15, "FIXED"),
    49: ("an", 3, "FIXED"),
    70: ("n", 3, "FIXED"),
}


class Iso8583Error(ValueError):
    """Raised when a synthetic message cannot be parsed or built."""


def mask_pan(pan: str) -> str:
    if len(pan) <= 10:
        return "*" * len(pan)
    return f"{pan[:6]}{'*' * (len(pan) - 10)}{pan[-4:]}"


def _hex_to_bits(value: str) -> str:
    if len(value) % 2 != 0:
        raise Iso8583Error("bitmap must have an even number of hex characters")
    try:
        return "".join(f"{int(char, 16):04b}" for char in value)
    except ValueError as exc:
        raise Iso8583Error("bitmap must contain only hex characters") from exc


def _bits_to_hex(bits: str) -> str:
    if len(bits) % 4 != 0:
        raise Iso8583Error("bitmap bit string must be a multiple of four")
    return "".join(f"{int(bits[index:index + 4], 2):X}" for index in range(0, len(bits), 4))


def _validate_value(field: int, value: str, spec: tuple[str, int, str]) -> None:
    field_type, max_length, _ = spec
    if len(value) > max_length:
        raise Iso8583Error(f"field {field} exceeds max length {max_length}")
    if field_type == "n" and not value.isdigit():
        raise Iso8583Error(f"field {field} must be numeric")
    if field_type == "an" and not value.replace(" ", "").isalnum():
        raise Iso8583Error(f"field {field} must be alphanumeric")


def parse_message(raw: str) -> dict[str, Any]:
    # Keep internal and trailing spaces: fixed alphanumeric fields may be padded.
    message = raw.replace("\n", "").replace("\r", "")
    if len(message) < 20:
        raise Iso8583Error("message is too short to contain MTI and primary bitmap")
    mti = message[:4]
    if len(mti) != 4 or not mti.isdigit():
        raise Iso8583Error("MTI must be four digits")

    primary_hex = message[4:20]
    bits = _hex_to_bits(primary_hex)
    offset = 20
    secondary = bits[0] == "1"
    if secondary:
        secondary_hex = message[offset : offset + 16]
        if len(secondary_hex) != 16:
            raise Iso8583Error("secondary bitmap is missing or incomplete")
        bits += _hex_to_bits(secondary_hex)
        offset += 16

    fields: dict[str, str] = {}
    for field_number in range(2, len(bits) + 1):
        if bits[field_number - 1] != "1":
            continue
        spec = FIELD_SPECS.get(field_number)
        if spec is None:
            raise Iso8583Error(f"field {field_number} is not supported by this lab")
        field_type, max_length, length_kind = spec
        if length_kind == "LLVAR":
            length_digits = message[offset : offset + 2]
            if len(length_digits) != 2 or not length_digits.isdigit():
                raise Iso8583Error(f"field {field_number} has an invalid length prefix")
            length = int(length_digits)
            offset += 2
        else:
            length = max_length
        if length > max_length:
            raise Iso8583Error(f"field {field_number} exceeds max length {max_length}")
        value = message[offset : offset + length]
        if len(value) != length:
            raise Iso8583Error(f"field {field_number} is truncated")
        _validate_value(field_number, value, spec)
        fields[str(field_number)] = value
        offset += length

    if offset != len(message):
        raise Iso8583Error("trailing data after the last parsed field")

    return {
        "mti": mti,
        "secondary_bitmap": secondary,
        "fields": fields,
        "pan_masked": mask_pan(fields["2"]) if "2" in fields else None,
    }


def build_message(mti: str, fields: dict[str | int, str]) -> str:
    if len(mti) != 4 or not mti.isdigit():
        raise Iso8583Error("MTI must be four digits")
    normalized: dict[int, str] = {}
    for key, value in fields.items():
        field_number = int(key)
        spec = FIELD_SPECS.get(field_number)
        if spec is None:
            raise Iso8583Error(f"field {field_number} is not supported by this lab")
        _validate_value(field_number, str(value), spec)
        normalized[field_number] = str(value)

    secondary = any(field_number > 64 for field_number in normalized)
    bit_count = 128 if secondary else 64
    bits = ["0"] * bit_count
    if secondary:
        bits[0] = "1"
    for field_number in normalized:
        bits[field_number - 1] = "1"

    message = mti + _bits_to_hex("".join(bits[:64]))
    if secondary:
        message += _bits_to_hex("".join(bits[64:]))

    for field_number in sorted(normalized):
        value = normalized[field_number]
        field_type, max_length, length_kind = FIELD_SPECS[field_number]
        if length_kind == "LLVAR":
            message += f"{len(value):02d}{value}"
        elif field_type == "n":
            message += value.zfill(max_length)
        else:
            message += value.ljust(max_length)

    return message
