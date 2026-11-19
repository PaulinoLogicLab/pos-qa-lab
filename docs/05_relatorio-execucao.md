# 05 — Relatório de execução

**Projeto:** POS QA Lab
**Data:** 19/11/2026
**Ambiente:** Windows, Python 3.13.14
**API:** FastAPI 0.165.0 + Uvicorn 0.54.0 + SQLite
**Robot Framework:** 7.5.1
**Comando:** `python scripts/run_suite.py --exclude device`

## 1. Resumo

| Métrica | Valor |
|---|---:|
| Casos Robot | 18 |
| Aprovados | 18 |
| Reprovados | 0 |
| Ignorados | 0 |
| Tempo somado dos casos | 0,64 s |
| Testes unitários Python | 25 aprovados |
| Suítes | 5 |
| Casos de dispositivo | 5 implementados, não executados |

## 2. Resultado por suíte

| Suíte | Casos | Aprovados | Reprovados | Tempo |
|---|---:|---:|---:|---:|
| 01 Sales | 3 | 3 | 0 | 0,084 s |
| 02 Cancellation Refund | 3 | 3 | 0 | 0,220 s |
| 03 Resilience | 4 | 4 | 0 | 0,183 s |
| 04 Contracts Observability | 3 | 3 | 0 | 0,133 s |
| 06 ISO 8583 Lab | 5 | 5 | 0 | 0,016 s |

## 3. Cobertura de estados

Estados exercitados: `CAPTURED`, `DECLINED`, `AUTHORIZED`, `CANCELLED`, `PARTIALLY_REFUNDED`,
`REFUNDED` e `FAILED`.

Transições exercitadas:

- criação → capturado;
- criação → negado;
- criação → autorizado;
- autorizado → cancelado;
- capturado → parcialmente estornado;
- parcialmente estornado → estornado;
- criação → falha por timeout;
- tentativas inválidas: estorno de autorizada, cancelamento de capturada.

## 4. Testes unitários

`pytest`: **25 aprovados**. Cobrem a API (contratos, idempotência, transições, timeout, correlação e sync),
o parser ISO 8583 e a fila offline do terminal.

## 5. Dispositivo

A suíte `robot/device/05_device_smoke.robot` tem 5 casos implementados para o Sauce Labs My Demo App:
login válido, validação sem credenciais, usuário bloqueado, carrinho e background/foreground.

**Dry-run:** 5/5 casos passaram na validação de keywords e argumentos em 19/11/2026.
**Execução real:** ignorada (`SKIP`) por ausência de `RUN_DEVICE_TESTS=1` e Appium/emulador neste ambiente.
O script `scripts/device_upgrade_check.py` implementa a evidência de instalação + atualização por
`adb install -r` e coleta de `logcat`; também não foi executado.

## 6. Defeitos e achados

| ID | Descrição | Severidade | Status |
|---|---|---|---|
| DEF-LAB-001 | Runner bloqueava a API ao não drenar o `stdout`; após alguns casos, o servidor parava de responder | Média | Corrigido |
| DEF-LAB-002 | `POST /terminals/{id}/sync` aceitava transação de outro terminal | Média | Corrigido |
| DEF-LAB-004 | Fila offline falhava no Linux no CI por caminho sem separador | Média | Corrigido |
| FIND-LAB-003 | Nome `Get Payment` ambíguo em três libraries Robot | Baixa | Corrigido |

Detalhes no [relatório de defeitos](06_relatorio-defeitos.md).

## 7. Evidências

- `reports/robot/report.html`
- `reports/robot/log.html`
- `reports/robot/output.xml`
- `reports/robot/summary.json`
- `reports/robot/api.log`
- `reports/logcat/` (quando o device suite for executado)

## 8. Observações e limites

- O tempo de 0,64 s é a soma dos casos, não o tempo de parede do runner.
- A API é local e simulada; não há latência de rede real.
- O ISO 8583 é um laboratório de formato, não uma implementação de produção.
- A primeira execução teve 9 falhas causadas por `DEF-LAB-001`; após a correção, 18/18 passaram.
- O device suite precisa ser executado em ambiente com Android/Appium antes de ser declarado aprovado.
