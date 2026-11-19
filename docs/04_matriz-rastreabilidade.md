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
| RF-13 | Login e validação no app público | CT-DEV-01, CT-DEV-02, CT-DEV-03 | suíte implementada | Pendente de execução |
| RF-14 | Carrinho no app público | CT-DEV-04 | suíte implementada | Pendente de execução |
| RF-15 | Ciclo de vida do app (background/foreground) | CT-DEV-05 | suíte implementada | Pendente de execução |

## 2. Requisitos não funcionais

| ID | Requisito | Casos / artefato | Evidência | Status |
|---|---|---|---|---|
| RNF-01 | Execução determinística e repetível | todos os casos | UUIDs e massas isoladas | Coberto |
| RNF-02 | CI/CD | `.github/workflows/robot.yml` | lint, pytest, Robot, artifacts | Coberto |
| RNF-03 | Privacidade e dados sintéticos | CT-ISO-01, CT-ISO-05 | PAN sintético e mascarado | Coberto |
| RNF-04 | Relatórios por caso | todos | `output.xml`, `log.html`, `report.html` | Coberto |
| RNF-05 | Reprodutibilidade | `scripts/run_suite.py` | sobe API, espera health, executa e encerra | Coberto |

## 3. Cobertura

| Métrica | Valor |
|---|---:|
| Requisitos funcionais | 15 |
| Requisitos não funcionais | 5 |
| Casos executados | 18 |
| Casos de dispositivo implementados | 5 |
| Casos executados com requisito mapeado | 18/18 |
| Casos de dispositivo com requisito mapeado | 5/5 |

## 4. Lacunas declaradas

- RF-13 a RF-15 estão implementados, mas **não executados** neste ambiente.
- Não há requisito de impressão térmica, pinpad, EMV, PCI PTS ou certificação de bandeira.
- O ISO 8583 cobre apenas ASCII e um subconjunto de campos; BCD, MAC e rede não estão implementados.
- Não há teste de carga, segurança ofensiva ou acessibilidade nesta versão.
