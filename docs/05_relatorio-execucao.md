# 05 — Relatório de execução

**Projeto:** POS QA Lab
**Data:** 19/11/2026
**Ambiente:** Windows, Python 3.13.14
**API:** FastAPI 0.165.0 + Uvicorn 0.54.0 + SQLite
**Robot Framework:** 7.5.1
**Comando (núcleo/ISO):** `python scripts/run_suite.py --exclude device`
**Comando (device):** `RUN_DEVICE_TESTS=1 python scripts/run_suite.py --device --no-api --outputdir reports/device_run`

**CI:** GitHub Actions `robot-core` em Ubuntu + Python 3.12, execução 32/32 aprovada em 19/11/2026.

## 1. Resumo

| Métrica | Valor |
|---|---:|
| Casos Robot executados | 37 |
| Aprovados | 37 |
| Reprovados | 0 |
| Ignorados | 0 |
| Tempo | 4,01 s (núcleo/ISO) + 104,69 s (device) |
| Testes unitários Python | 39 aprovados |
| Suítes | 9 (8 de núcleo/ISO + 1 de device) |
| Casos de dispositivo | 5/5 aprovados em emulador |

## 2. Resultado por suíte

| Suíte | Casos | Aprovados | Reprovados | Tempo |
|---|---:|---:|---:|---:|
| 01 Sales | 3 | 3 | 0 | 0,102 s |
| 02 Cancellation Refund | 3 | 3 | 0 | 0,286 s |
| 03 Resilience | 4 | 4 | 0 | 0,208 s |
| 04 Contracts Observability | 3 | 3 | 0 | 0,129 s |
| 05 Capture Settlement | 6 | 6 | 0 | 0,613 s |
| 06 ISO 8583 Lab | 5 | 5 | 0 | 0,015 s |
| 07 Concurrency Faults | 2 | 2 | 0 | 2,633 s |
| 08 ISO 8583 Flow | 6 | 6 | 0 | 0,020 s |
| Device 05 Device Smoke (emulador) | 5 | 5 | 0 | 104,689 s |

## 3. Cobertura de estados

Estados exercitados: `CAPTURED`, `DECLINED`, `AUTHORIZED`, `CANCELLED`, `PARTIALLY_CAPTURED`,
`PARTIALLY_REFUNDED`, `REFUNDED` e `FAILED`.

Transições exercitadas:

- criação → capturado;
- criação → negado;
- criação → autorizado;
- autorizado → cancelado;
- autorizado → capturado;
- autorizado → parcialmente capturado;
- parcialmente capturado → estornado;
- capturado → parcialmente estornado;
- parcialmente estornado → estornado;
- criação → falha por timeout;
- tentativas inválidas: estorno de autorizada, cancelamento de capturada, captura após cancelamento;
- liquidação: bruto, estorno, líquido e lote vazio.

## 4. Testes unitários

`pytest`: **39 aprovados**. Cobrem a API (contratos, idempotência, transições, timeout, concorrência,
captura, liquidação, correlação e sync), o parser/fluxo ISO 8583 e a fila offline do terminal.

## 5. Dispositivo

A suíte `robot/device/05_device_smoke.robot` tem 5 casos para o Sauce Labs My Demo App:
login válido, validação sem credenciais, usuário bloqueado, carrinho e background/foreground.

**Execução real:** **5/5 aprovados** em 19/11/2026.
**Ambiente:** emulador `Pixel_8_Pro` (`sdk_gphone64_x86_64`), Android 16 / API 36, x86_64,
My Demo App 2.3.0, Appium 3.5.0 e UiAutomator2 7.0.0.
**Tempo:** 104,69 s.
**Evidência:** `reports/device_run/report.html`, `log.html`, `output.xml` e `summary.json`.

O script `scripts/device_upgrade_check.py` implementa a evidência de instalação + atualização por
`adb install -r` e coleta de `logcat`; ele ainda não foi executado.

## 6. Defeitos e achados

| ID | Descrição | Severidade | Status |
|---|---|---|---|
| DEF-LAB-001 | Runner bloqueava a API ao não drenar o `stdout`; após alguns casos, o servidor parava de responder | Média | Corrigido |
| DEF-LAB-002 | `POST /terminals/{id}/sync` aceitava transação de outro terminal | Média | Corrigido |
| DEF-LAB-004 | Fila offline falhava no Linux no CI por caminho sem separador | Média | Corrigido |
| FIND-LAB-003 | Nome `Get Payment` ambíguo em três libraries Robot | Baixa | Corrigido |
| FIND-LAB-005 | Activity relativa não abria o app no Appium; faltava `udid` e nome completo | Baixa | Corrigido |
| FIND-LAB-006 | CT-DEV-04 clicava no container não clicável e no botão de adicionar, não no ícone do carrinho | Baixa | Corrigido |
| FIND-LAB-007 | Keyword `Reset Acquirer` não existia porque o método se chamava `reset` | Baixa | Corrigido |
| FIND-LAB-008 | `Acquirer` não expunha `transaction_count`; teste unitário detectou | Baixa | Corrigido |

Detalhes no [relatório de defeitos](06_relatorio-defeitos.md).

## 7. Evidências

- `reports/robot/report.html`
- `reports/robot/log.html`
- `reports/robot/output.xml`
- `reports/robot/summary.json`
- `reports/robot/api.log`
- `reports/device_run/report.html`
- `reports/device_run/log.html`
- `reports/device_run/output.xml`
- `reports/device_run/summary.json`
- `docs/evidencias/device-2026-11-19/summary.json`
- `docs/evidencias/core-2026-11-19/summary.json`
- `reports/logcat/` (quando houver falha de device)

## 8. Observações e limites

- Os 4,01 s são a soma dos casos de núcleo/ISO; o device suite levou 104,69 s.
- A concorrência usa 10 threads e uma barreira; o timeout usa atraso de 1,5 s e cliente de 0,5 s.
- A API é local e simulada; não há latência de rede real.
- O ISO 8583 é um laboratório de formato, não uma implementação de produção.
- A primeira execução do núcleo teve 9 falhas causadas por `DEF-LAB-001`; após a correção, 18/18 passaram (v0.1.0).
- O device suite foi executado em emulador, não em dispositivo físico/POS.
