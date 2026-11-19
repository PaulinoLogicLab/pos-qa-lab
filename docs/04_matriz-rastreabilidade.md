# 04 — Matriz de rastreabilidade

**Projeto:** POS QA Lab
**Data:** 19/11/2026

## 1. Requisitos funcionais

| ID | Requisito | Casos | Evidência | Status |
|---|---|---|---|---|
| RF-01 | Venda aprovada e negada com código de resposta | CT-PAY-01, CT-PAY-02 | `report.html`, `payments`, `payment_events` | Coberto |
| RF-02 | Cancelamento antes da captura | CT-PAY-03 | `payments.status`, evento `PAYMENT_CANCELLED` | Coberto |
| RF-03 | Estorno total e parcial após captura | CT-PAY-04, CT-PAY-06 | `refunds`, `refunded_cents`, evento | Coberto |
| RF-04 | Parcelamento com arredondamento | CT-PAY-05 | `installment_plan` na resposta | Coberto |
| RF-05 | Idempotência de criação | CT-RES-01 | mesmo `payment_id`, contagem 1 | Coberto |
| RF-06 | Timeout e retry sem duplicidade | CT-RES-02 | HTTP 504, código `91`, contagem 1 | Coberto |
| RF-07 | Fila offline e sincronização | CT-RES-03 | `offline_queue`, `sync`, `payments` | Coberto |
| RF-08 | Reinício do terminal preserva fila | CT-RES-04 | `offline_queue` após restart | Coberto |
| RF-09 | Contratos de erro e validação | CT-CON-01 | HTTP 422 e códigos de erro | Coberto |
| RF-10 | Correlação em API, banco e evento | CT-OBS-01 | header, `correlation_id`, evento | Coberto |
| RF-11 | Sync restrito ao terminal da rota | CT-CON-02 | `TERMINAL_MISMATCH`, nenhuma linha | Coberto |
| RF-12 | Parse ISO 8583 de mensagens sintéticas | CT-ISO-01 a CT-ISO-05 | `iso8583_lab`, campos e bitmap | Coberto |
| RF-13 | Login e validação no app público | CT-DEV-01, CT-DEV-02, CT-DEV-03 | suíte executada em emulador | Coberto |
| RF-14 | Carrinho no app público | CT-DEV-04 | suíte executada em emulador | Coberto |
| RF-15 | Ciclo de vida do app (background/foreground) | CT-DEV-05 | suíte executada em emulador | Coberto |
| RF-16 | Pré-autorização e captura total/parcial | CT-CAP-01, CT-CAP-02, CT-CAP-03 | `captured_cents`, status e eventos | Coberto |
| RF-17 | Liquidação por terminal com bruto, estorno e líquido | CT-SET-01, CT-SET-02, CT-SET-03 | `settlements`, `settlement_items`, `settlement_id` | Coberto |
| RF-18 | Concorrência de idempotência | CT-RES-05 | 10 threads, um `payment_id` | Coberto |
| RF-19 | Latência/timeout e retry | CT-RES-06 | `simulate_delay_ms`, timeout e retry | Coberto |
| RF-20 | Fluxo ISO 8583 de autorização, reversão e rede | CT-ISO-06 a CT-ISO-11 | `iso8583_lab/acquirer.py` | Coberto |
| RF-21 | Cobertura data-driven de valores, parcelas e recusa | CT-DD-01 a CT-DD-05 | `SalesWorkflow.py`, template Robot | Coberto |

## 2. Requisitos não funcionais

| ID | Requisito | Casos / artefato | Evidência | Status |
|---|---|---|---|---|
| RNF-01 | Execução determinística e repetível | todos os casos | UUIDs e massas isoladas | Coberto |
| RNF-02 | CI/CD | `.github/workflows/robot.yml` | lint, pytest, Robot, artifacts | Coberto |
| RNF-03 | Privacidade e dados sintéticos | CT-ISO-01, CT-ISO-05 | PAN sintético e mascarado | Coberto |
| RNF-04 | Relatórios por caso | todos | `output.xml`, `log.html`, `report.html` | Coberto |
| RNF-05 | Reprodutibilidade | `scripts/run_suite.py` | sobe API, espera health, executa e encerra | Coberto |
| RNF-06 | Execução paralela e evidência por caso | `scripts/run_parallel.py` + listener | Pabot 4 processos e JSONL por PID | Coberto |

## 3. Cobertura

| Métrica | Valor |
|---|---:|
| Requisitos funcionais | 21 |
| Requisitos não funcionais | 6 |
| Casos de núcleo/ISO executados | 37 |
| Casos de dispositivo executados | 5 |
| Casos executados com requisito mapeado | 42/42 |
| Casos de dispositivo com requisito mapeado | 5/5 |

## 4. Lacunas declaradas

- O device suite foi executado em emulador, não em dispositivo físico/POS.
- O script de atualização de APK está implementado, mas ainda não executado.
- O fluxo ISO 8583 é em memória, sem socket, BCD, MAC ou rede real.
- A liquidação é um snapshot; estorno posterior não recalcula o lote.
- A captura parcial não libera o saldo restante da autorização.
- Não há requisito de impressão térmica, pinpad, EMV, PCI PTS ou certificação de bandeira.
- Não há teste de carga, segurança ofensiva ou acessibilidade nesta versão.
