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
| Casos Robot executados | **18** |
| Aprovados | **18** |
| Reprovados | **0** |
| Tempo somado dos casos | **0,64 s** |
| Testes unitários Python | **25 aprovados** |
| Casos de dispositivo implementados | **5** (não executados neste ambiente) |
| Defeitos do laboratório corrigidos | **3** (+1 achado de automação) |
| CI | **18/18 no Ubuntu + Python 3.12** |

Detalhes em [relatório de execução](docs/05_relatorio-execucao.md) e [relatório de defeitos](docs/06_relatorio-defeitos.md).

## O que o projeto cobre

- **Venda** aprovada e negada, com código de resposta.
- **Cancelamento** antes da captura.
- **Estorno** total e parcial.
- **Parcelamento** com arredondamento de centavos.
- **Idempotência** por `Idempotency-Key`.
- **Timeout + retry** sem duplicar transação.
- **Fila offline** em SQLite e sincronização.
- **Reinício do terminal** preservando a fila.
- **Contratos de erro** (400/422/409) e `correlation_id` em API, banco e evento.
- **ISO 8583**: MTI, bitmap primário/secundário, campos fixos e LLVAR, campo 39 e 70.
- **Android**: login, validação, carrinho, background/foreground e atualização de APK.

## Arquitetura

```mermaid
flowchart LR
    R[Robot Framework] --> A[PaymentApi.py]
    R --> T[Terminal.py]
    R --> I[Iso8583.py]
    R --> D[Database.py]
    T --> API[FastAPI - simulado]
    A --> API
    API --> DB[(SQLite)]
    R --> ISO[iso8583_lab]
    R --> DEV[AppiumLibrary]
    DEV --> APP[Sauce Labs My Demo App]
```

- `src/api`: API FastAPI, regras de pagamento, idempotência, eventos e refunds.
- `src/terminal`: simulador de terminal com fila offline persistida em SQLite.
- `libraries`: bibliotecas Robot que isolam HTTP, banco, estado e parsing.
- `robot/suites`: suítes de negócio, resiliência, contratos e ISO 8583.
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

Testes unitários:

```bash
pytest
```

Rodar apenas um grupo:

```bash
python scripts/run_suite.py --include resilience
python scripts/run_suite.py --include iso8583
python scripts/run_suite.py --include contract
```

## Device suite

Pré-requisitos: Android SDK/`adb`, emulador ou dispositivo, Appium 2 e `UiAutomator2`.

```bash
pip install -r requirements-device.txt
python scripts/download_demo_app.py
appium --address 127.0.0.1 --port 4723
```

Windows PowerShell:

```powershell
$env:RUN_DEVICE_TESTS="1"
python scripts/run_suite.py --device --no-api
```

Atualização de APK (evidência de install/update):

```bash
python scripts/device_upgrade_check.py --old device/apps/<antigo>.apk --new device/apps/<novo>.apk
```

O script instala a versão antiga, abre o app, instala a nova com `adb install -r`, verifica se o processo
continua vivo e salva `reports/device/upgrade-check.txt` e o `logcat`.

## Estrutura

```text
pos-qa-lab/
  docs/                 # escopo, plano, casos, matriz, execução, defeitos, limitações
  src/api/              # FastAPI + SQLite
  src/terminal/         # simulador com fila offline
  iso8583_lab/          # parser/construtor didático
  libraries/            # bibliotecas Robot
  robot/suites/         # 13 casos de núcleo + 5 de ISO
  robot/device/         # 5 casos de dispositivo
  tests/                # 25 testes unitários
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

## Licença

MIT. Veja [LICENSE](LICENSE).
