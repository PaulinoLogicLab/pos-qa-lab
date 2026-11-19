from __future__ import annotations

from src.terminal.simulator import TerminalSimulator


def test_offline_queue_survives_restart(tmp_path):
    db_file = tmp_path / "terminal.db"
    terminal = TerminalSimulator(terminal_id="TERM9001", db_path=str(db_file))
    terminal.go_offline()
    result = terminal.start_sale("25.00", idempotency_key="queue-key-0001")
    assert result["status"] == "QUEUED_OFFLINE"
    assert terminal.queue_size() == 1

    restarted = TerminalSimulator(terminal_id="TERM9001", db_path=str(db_file))
    assert restarted.queue_size() == 1
    queued = restarted.queued_transactions()
    assert queued[0]["idempotency_key"] == "queue-key-0001"
    assert queued[0]["payload"]["amount"] == "25.00"


def test_restart_returns_to_online(tmp_path):
    terminal = TerminalSimulator(terminal_id="TERM9002", db_path=str(tmp_path / "t.db"))
    terminal.go_offline()
    assert terminal.online is False
    state = terminal.restart()
    assert state["online"] is True
    assert state["queue_size"] == 0
