# POS QA Lab — Robot Framework + Python

[![robot-core](https://github.com/PaulinoLogicLab/pos-qa-lab/actions/workflows/robot.yml/badge.svg)](https://github.com/PaulinoLogicLab/pos-qa-lab/actions/workflows/robot.yml)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)

Laboratório público de qualidade para uma **jornada de pagamento simulada** e um **terminal Android de demonstração**.
O objetivo é exercitar, com evidência, o tipo de falha que aparece em POS: timeout, perda de conexão, retry,
idempotência, cancelamento, estorno, parcelamento, reinício e atualização de aplicativo.

> **Escopo e honestidade:** este projeto é um laboratório. Não é um POS real, não se conecta a adquirente,
> não implementa EMV, ISO 8583 de produção ou PCI PTS e não tem afiliação com a Stone. Os dados são sintéticos.

## Resultado atual

| Métrica | Valor |
|---|---:|
| Casos Robot executados | **49** |
| Aprovados | **49** |
| Reprovados | **0** |
| Tempo somado dos casos | **4,08 s (núcleo/ISO/hardware) + 104,69 s (device)** |
| Execução paralela | **44/44 em 4 processos Pabot** |
| Docker Compose | **44/44 no container Linux** |
| Testes unitários Python | **52 aprovados** |
| Cobertura de linhas | **88,9%** |
| k6 | **436 req, 0% falha, p95 77,50 ms** |
| Casos de dispositivo | **5/5 aprovados em emulador Android 16** |
| Defeitos do laboratório corrigidos | **3** (+10 achados de automação/implementação) |
| CI | **44/44 em Python 3.11, 3.12 e 3.13 + Docker + k6** |

Detalhes em [relatório de execução](docs/05_relatorio-execucao.md) e [relatório de defeitos](docs/06_relatorio-defeitos.md).

**Evidências versionadas:** [índice](docs/evidencias/README.md) · [núcleo/ISO](docs/evidencias/core-2026-11-19/summary.json) · [device](docs/evidencias/device-2026-11-19/summary.json)

## O que o projeto cobre

- **Venda** aprovada e negada, com código de resposta.
- **Cancelamento** antes da captura.
- **Pré-autorização + captura** total e parcial.
- **Estorno** total e parcial, limitado ao valor capturado.
- **Parcelamento** com arredondamento de centavos.
- **Liquidação/fechamento** por terminal, com bruto, estorno e líquido.
- **Idempotência** por `Idempotency-Key`, inclusive sob concorrência.
- **Timeout + retry** sem duplicar transação.
- **Fila offline** em SQLite e sincronização.
- **Reinício do terminal** preservando a fila.
- **Contratos de erro** (400/422/409) e `correlation_id` em API, banco e evento.
- **ISO 8583**: MTI, bitmap, campos fixos/LLVAR, `0100/0110`, `0400/0410` e `0800/0810`.
- **Android**: login, validação, carrinho, background/foreground e atualização de APK.
- **Robot de produção**: library Python de negócio, testes data-driven, Pabot, listener de evidência
  e CI matrix em três versões do Python.
- **Linux e operação**: Dockerfile, Docker Compose, Makefile, scripts shell, runbook e job Docker no CI.
- **Hardware simulado**: impressora (papel/acesso), pinpad (timeout/cancelamento), reboot,
  atualização de firmware e configuração.
- **Qualidade de API**: contrato OpenAPI, property-based testing, cobertura e k6.

## Arquitetura

```mermaid
flowchart LR
    R[Robot Framework] --> A[PaymentApi.py]
    R --> T[Terminal.py]
    R --> I[Iso8583.py]
    R --> IA[Iso8583Acquirer.py]
    R --> D[Database.py]
    T --> API[FastAPI - simulado]
    A --> API
    API --> DB[(SQLite)]
    IA --> ISO[iso8583_lab]
    R --> DEV[AppiumLibrary]
    DEV --> APP[Sauce Labs My Demo App]
```

- `src/api`: API FastAPI, regras de pagamento, idempotência, eventos e refunds.
- `src/terminal`: simulador de terminal com fila offline persistida em SQLite.
- `libraries`: bibliotecas Robot que isolam HTTP, banco, estado e parsing.
- `robot/suites`: 32 casos de negócio, resiliência, captura/liquidação, concorrência e ISO 8583.
- `robot/device`: smoke de dispositivo no app público.
- `iso8583_lab`: parser/construtor limitado a ASCII e dados sintéticos.

## Quickstart

```bash
python -m venv .venv
# Windows
.venv\Scripts\activate
# Linux/macOS
source .venv/bin/activate

pip install -r requirements.txt
python scripts/run_suite.py --exclude device
```

Relatórios:

- `reports/robot/report.html`
- `reports/robot/log.html`
- `reports/robot/output.xml`
- `reports/robot/summary.json`
- `reports/robot/api.log`

Testes unitários e cobertura:

```bash
pytest --cov=src --cov=iso8583_lab --cov-report=term --cov-fail-under=85
```

Rodar apenas um grupo:

```bash
python scripts/run_suite.py --include resilience
python scripts/run_suite.py --include iso8583
python scripts/run_suite.py --include contract
python scripts/run_suite.py --include data_driven
```

Execução paralela com Pabot:

```bash
python scripts/run_parallel.py --processes 4
```

O listener grava um JSONL por processo em `reports/*/evidence/`, com início, fim, tags, status e tempo
de cada caso.

Performance com k6:

```bash
docker compose up -d api
docker compose --profile perf run --rm k6
# ou
make perf
```

## Docker

```bash
docker compose up -d api
docker compose up --abort-on-container-exit --exit-code-from tests tests
docker compose down -v
```

O serviço `tests` compartilha o volume SQLite com a API e grava os relatórios em `./reports`.
O profile `parallel` roda a suíte com Pabot dentro do container.

Guia completo: [runbook Linux](docs/09_runbook-linux.md).

## Device suite

**Resultado:** 5/5 aprovados em 19/11/2026 no emulador `Pixel_8_Pro`
(`sdk_gphone64_x86_64`, Android 16 / API 36), com My Demo App 2.3.0, Appium 3.5.0 e
UiAutomator2 7.0.0. Tempo dos casos: 104,69 s.

Pré-requisitos: Android SDK/`adb`, emulador ou dispositivo, Appium 2+ e `UiAutomator2`.

```bash
pip install -r requirements-device.txt
python scripts/download_demo_app.py
appium --address 127.0.0.1 --port 4723
```

Windows PowerShell:

```powershell
$env:RUN_DEVICE_TESTS="1"
python scripts/run_suite.py --device --no-api --outputdir reports/device_run
```

Atualização de APK (evidência de install/update):

```bash
python scripts/device_upgrade_check.py --old device/apps/<antigo>.apk --new device/apps/<novo>.apk
```

O script instala a versão antiga, abre o app, instala a nova com `adb install -r`, verifica se o processo
continua vivo e salva `reports/device/upgrade-check.txt` e o `logcat`. Ele ainda não foi executado.

## Estrutura

```text
pos-qa-lab/
  docs/                 # escopo, plano, casos, matriz, execução, defeitos, limitações
  src/api/              # FastAPI + SQLite
  src/terminal/         # simulador com fila offline
  iso8583_lab/          # parser/construtor didático
  libraries/            # bibliotecas Robot
  robot/suites/         # 44 casos de núcleo, hardware, captura/liquidação, concorrência, data-driven e ISO
  robot/device/         # 5 casos de dispositivo
  tests/                # 52 testes unitários
  scripts/              # runner, resumo, download e upgrade
```

## Limitações

- Adquirente, terminal e dados são simulados.
- ISO 8583 é um laboratório de formato: ASCII, sem BCD, MAC ou rede.
- A suíte de dispositivo está implementada, mas **não foi executada** neste ambiente por ausência de
  emulador/Appium; o README explica como reproduzir.
- Não há teste de impressão térmica, pinpad, EMV ou certificação de bandeira.
- Não há autenticação na API do laboratório.

## Documentação

- [Escopo e riscos](docs/01_escopo-e-riscos.md)
- [Plano de teste](docs/02_plano-de-teste.md)
- [Casos de teste](docs/03_casos-de-teste.md)
- [Matriz de rastreabilidade](docs/04_matriz-rastreabilidade.md)
- [Relatório de execução](docs/05_relatorio-execucao.md)
- [Relatório de defeitos](docs/06_relatorio-defeitos.md)
- [Limitações](docs/07_limitacoes.md)
- [Arquitetura Robot](docs/08_robot-arquitetura.md)
- [Runbook Linux](docs/09_runbook-linux.md)
- [Hardware e periféricos](docs/10_hardware-perifericos.md)
- [Métricas de qualidade](docs/11_metricas-qualidade.md)

## Licença

MIT. Veja [LICENSE](LICENSE).
