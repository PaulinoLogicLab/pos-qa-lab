# Changelog

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
