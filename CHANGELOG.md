# Changelog

## 0.4.0 — 19/11/2026

### Added

- Dockerfile multi-stage simples em `python:3.12-slim`, usuário não-root e volume `/app/data`.
- `docker-compose.yml` com `api`, `tests` e profile `parallel`.
- Makefile com `lint`, `unit`, `robot`, `parallel`, `device`, `test`, `up`, `down`, `logs` e `docker-test`.
- Scripts shell `run_core.sh`, `run_device.sh` e `collect_logs.sh`.
- Runbook Linux em `docs/09_runbook-linux.md`.
- Job Docker no GitHub Actions.

### Changed

- Bibliotecas Robot leem `API_URL` do ambiente, permitindo API local ou `http://api:8000`.
- Runner falha se já houver uma API na porta 8000, evitando misturar banco local e Docker.

### Fixed

- `FIND-LAB-011`: runner local podia usar a API do Docker e ler banco diferente.

## 0.3.0 — 19/11/2026

### Added

- Library Python de negócio `SalesWorkflow` (`Create And Assert Sale`, captura e liquidação).
- Suíte data-driven `09_data_driven_sales` com 5 casos de valores, parcelas e recusa.
- Execução paralela com Pabot (`scripts/run_parallel.py`, 4 processos).
- Listener `RobotListener` com evidência JSONL por processo.
- CI matrix Python 3.11/3.12/3.13; Pabot na versão 3.12.
- Documento `docs/08_robot-arquitetura.md`.

### Fixed

- `FIND-LAB-009`: Pabot não encontrava o executável `robot` porque o `PATH` não incluía o venv.
- `FIND-LAB-010`: listener usava `data.starttime`, inexistente no Robot 7.

## 0.2.0 — 19/11/2026

### Added

- Pré-autorização e captura total/parcial (`POST /payments/{id}/capture`).
- Liquidação por terminal (`POST /terminals/{id}/settlement`), com bruto, estorno e líquido.
- Tabelas `settlements` e `settlement_items`; `captured_cents`, `settlement_id` e `settled_at`.
- Teste de concorrência com 10 requisições e a mesma `Idempotency-Key`.
- Injeção de latência (`simulate_delay_ms`) e teste de timeout + retry.
- Fluxo ISO 8583 `0100/0110`, `0400/0410` e `0800/0810` em memória.
- Campos ISO 37 (RRN) e 38 (approval code).
- Suítes Robot `05_capture_settlement`, `07_concurrency_faults` e `08_iso8583_flow`.

### Changed

- Estorno agora é limitado ao valor capturado, não ao valor autorizado.
- `create_payment` trata conflito de idempotência concorrente sem retornar 500.
- SQLite usa WAL, `busy_timeout` e migração automática das novas colunas.
- Documentação, matriz, relatório e evidências atualizados para 37 casos.

### Fixed

- `FIND-LAB-007`: keyword `Reset Acquirer` não era exposta pelo método `reset`.
- `FIND-LAB-008`: `Acquirer` sem `transaction_count` para o teste de duplicidade.

## 0.1.0 — 19/11/2026

- Versão inicial com venda, cancelamento, estorno, parcelamento, resiliência, contratos,
  ISO 8583 parser e device suite.
