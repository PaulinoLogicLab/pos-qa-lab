from __future__ import annotations

import pytest

from iso8583_lab.parser import Iso8583Error, build_message, mask_pan, parse_message


def sample_0100():
    return build_message(
        "0100",
        {
            2: "4111111111111111",
            3: "000000",
            4: "000000012590",
            7: "1119183000",
            11: "000123",
            12: "183000",
            13: "1119",
            41: "TERM0001",
            42: "MERCH0000000001",
            49: "986",
        },
    )


def test_parse_valid_0100():
    parsed = parse_message(sample_0100())
    assert parsed["mti"] == "0100"
    assert parsed["secondary_bitmap"] is False
    assert parsed["fields"]["2"] == "4111111111111111"
    assert parsed["fields"]["4"] == "000000012590"
    assert parsed["fields"]["11"] == "000123"
    assert parsed["pan_masked"] == "411111******1111"


def test_parse_response_0110_with_code_39():
    message = build_message(
        "0110",
        {
            2: "4111111111111111",
            3: "000000",
            4: "000000012590",
            7: "1119183000",
            11: "000123",
            39: "00",
            41: "TERM0001",
            42: "MERCH0000000001",
            49: "986",
        },
    )
    parsed = parse_message(message)
    assert parsed["mti"] == "0110"
    assert parsed["fields"]["39"] == "00"


def test_secondary_bitmap_with_field_70():
    message = build_message(
        "0100",
        {
            2: "4111111111111111",
            3: "000000",
            4: "000000000100",
            11: "000124",
            70: "301",
        },
    )
    parsed = parse_message(message)
    assert parsed["secondary_bitmap"] is True
    assert parsed["fields"]["70"] == "301"


def test_invalid_bitmap_is_rejected():
    with pytest.raises(Iso8583Error, match="primary bitmap|too short"):
        parse_message("0100")


def test_truncated_field_is_rejected():
    message = sample_0100()
    with pytest.raises(Iso8583Error):
        parse_message(message[:-1])


def test_round_trip_build_and_parse():
    fields = {
        2: "4111111111111111",
        3: "000000",
        4: "000000000100",
        7: "1119183000",
        11: "000125",
        12: "183000",
        13: "1119",
        41: "TERM0001",
        42: "MERCH0000000001",
        49: "986",
    }
    parsed = parse_message(build_message("0100", fields))
    assert parsed["fields"] == {str(key): value for key, value in fields.items()}


def test_mask_pan_short_value():
    assert mask_pan("12345") == "*****"


def test_fixed_alphanumeric_is_space_padded():
    message = build_message("0100", {41: "TERM1"})
    parsed = parse_message(message)
    assert parsed["fields"]["41"] == "TERM1   "
