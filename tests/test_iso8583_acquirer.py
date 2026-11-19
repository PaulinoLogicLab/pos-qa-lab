from __future__ import annotations

import pytest

from iso8583_lab.acquirer import Acquirer
from iso8583_lab.parser import Iso8583Error, build_message


def auth_message(pan: str = "4111111111111111", stan: str = "000123") -> str:
    return build_message(
        "0100",
        {
            2: pan,
            3: "000000",
            4: "000000010000",
            7: "1119183000",
            11: stan,
            12: "183000",
            13: "1119",
            41: "TERM0001",
            42: "MERCH0000000001",
            49: "986",
        },
    )


def test_authorization_approved():
    acquirer = Acquirer()
    result = acquirer.process(auth_message())
    assert result["status"] == "APPROVED"
    assert result["parsed"]["mti"] == "0110"
    assert result["parsed"]["fields"]["39"] == "00"
    assert result["parsed"]["fields"]["38"] == "A12345"
    assert "37" in result["parsed"]["fields"]


def test_duplicate_authorization_is_idempotent():
    acquirer = Acquirer()
    first = acquirer.process(auth_message())
    second = acquirer.process(auth_message())
    assert first["response"] == second["response"]
    assert second["duplicate"] is True
    assert acquirer.transaction_count() == 1


def test_declined_authorization():
    acquirer = Acquirer()
    result = acquirer.process(auth_message(pan="4000000000000002"))
    assert result["status"] == "DECLINED"
    assert result["parsed"]["fields"]["39"] == "05"
    assert "38" not in result["parsed"]["fields"]


def test_reversal_and_duplicate_reversal():
    acquirer = Acquirer()
    acquirer.process(auth_message())
    reversal = build_message(
        "0400",
        {
            2: "4111111111111111",
            3: "000000",
            4: "000000010000",
            7: "1119183000",
            11: "000123",
            12: "183000",
            13: "1119",
            41: "TERM0001",
            42: "MERCH0000000001",
            49: "986",
        },
    )
    first = acquirer.process(reversal)
    second = acquirer.process(reversal)
    assert first["status"] == "REVERSED"
    assert first["parsed"]["fields"]["39"] == "00"
    assert second["status"] == "ALREADY_REVERSED"
    assert second["duplicate"] is True


def test_network_management_echo():
    acquirer = Acquirer()
    message = build_message("0800", {7: "1119183000", 11: "000900", 70: "301"})
    result = acquirer.process(message)
    assert result["status"] == "NETWORK_OK"
    assert result["parsed"]["mti"] == "0810"
    assert result["parsed"]["fields"]["39"] == "00"


def test_unsupported_mti_is_rejected():
    acquirer = Acquirer()
    with pytest.raises(Iso8583Error, match="not supported"):
        acquirer.process(build_message("0200", {11: "000901"}))
