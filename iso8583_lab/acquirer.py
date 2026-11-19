"""A small ISO 8583 message-flow lab.

It processes synthetic ASCII messages for authorization (0100), reversal (0400)
and network management (0800). There is no socket, BCD, MAC, EMV or real
acquirer connection.
"""

from __future__ import annotations

from typing import Any

from .parser import Iso8583Error, build_message, parse_message


class Acquirer:
    def __init__(self) -> None:
        self.transactions: dict[tuple[str, str], dict[str, Any]] = {}

    def reset(self) -> None:
        self.transactions.clear()

    def transaction_count(self) -> int:
        return len(self.transactions)

    def process(self, raw: str) -> dict[str, Any]:
        parsed = parse_message(raw)
        mti = parsed["mti"]
        if mti == "0100":
            return self._authorize(parsed)
        if mti == "0400":
            return self._reverse(parsed)
        if mti == "0800":
            return self._network(parsed)
        raise Iso8583Error(f"MTI {mti} is not supported by this lab")

    @staticmethod
    def _key(fields: dict[str, str]) -> tuple[str, str]:
        try:
            return fields["41"], fields["11"]
        except KeyError as exc:
            raise Iso8583Error("terminal (41) and STAN (11) are required") from exc

    @staticmethod
    def _copy(fields: dict[str, str], numbers: list[int]) -> dict[str, str]:
        return {str(number): fields[str(number)] for number in numbers if str(number) in fields}

    def _authorize(self, parsed: dict[str, Any]) -> dict[str, Any]:
        fields = parsed["fields"]
        for required in ("2", "4", "11", "41", "42", "49"):
            if required not in fields:
                raise Iso8583Error(f"field {required} is required for 0100")
        key = self._key(fields)
        existing = self.transactions.get(key)
        if existing:
            if existing["amount"] != fields["4"]:
                raise Iso8583Error("duplicate STAN with a different amount")
            return {
                "response": existing["response"],
                "parsed": parse_message(existing["response"]),
                "status": existing["status"],
                "duplicate": True,
            }

        pan = fields["2"]
        if pan.endswith("0002"):
            code, status, approval = "05", "DECLINED", None
        elif pan.endswith("0003"):
            code, status, approval = "91", "TIMEOUT", None
        else:
            code, status, approval = "00", "APPROVED", "A12345"

        response_fields = self._copy(fields, [2, 3, 4, 7, 11, 12, 13, 37, 41, 42, 49])
        response_fields.setdefault("37", f"RRN{fields['11'].zfill(9)}")
        response_fields["39"] = code
        if approval:
            response_fields["38"] = approval
        response = build_message("0110", response_fields)
        self.transactions[key] = {
            "response": response,
            "status": status,
            "amount": fields["4"],
            "reversed": False,
        }
        return {
            "response": response,
            "parsed": parse_message(response),
            "status": status,
            "duplicate": False,
        }

    def _reverse(self, parsed: dict[str, Any]) -> dict[str, Any]:
        fields = parsed["fields"]
        key = self._key(fields)
        existing = self.transactions.get(key)
        if not existing:
            response = build_message(
                "0410",
                self._copy(fields, [2, 3, 4, 7, 11, 12, 13, 37, 41, 42, 49])
                | {"39": "12"},
            )
            return {
                "response": response,
                "parsed": parse_message(response),
                "status": "NOT_FOUND",
                "duplicate": False,
            }

        if existing["reversed"]:
            response = build_message(
                "0410",
                self._copy(fields, [2, 3, 4, 7, 11, 12, 13, 37, 41, 42, 49]) | {"39": "00"},
            )
            return {
                "response": response,
                "parsed": parse_message(response),
                "status": "ALREADY_REVERSED",
                "duplicate": True,
            }

        existing["reversed"] = True
        response = build_message(
            "0410",
            self._copy(fields, [2, 3, 4, 7, 11, 12, 13, 37, 41, 42, 49]) | {"39": "00"},
        )
        return {
            "response": response,
            "parsed": parse_message(response),
            "status": "REVERSED",
            "duplicate": False,
        }

    def _network(self, parsed: dict[str, Any]) -> dict[str, Any]:
        fields = parsed["fields"]
        response_fields = self._copy(fields, [7, 11, 70])
        response_fields["39"] = "00"
        response = build_message("0810", response_fields)
        return {
            "response": response,
            "parsed": parse_message(response),
            "status": "NETWORK_OK",
            "duplicate": False,
        }
