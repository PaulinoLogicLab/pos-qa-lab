# 09 — Runbook Linux

**Projeto:** POS QA Lab
**Versão:** 0.4.0
**Data:** 19/11/2026

## 1. Pré-requisitos

- Python 3.11+ (recomendado 3.12)
- Docker 24+ com Compose v2
- `make` e `bash` para os alvos de conveniência
- Para device: Android SDK, `adb`, Appium 2+ e emulador/dispositivo

## 2. Ambiente local

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

Rodar lint, testes unitários e Robot:

```bash
make lint
make unit
make robot
```

Ou diretamente:

```bash
python scripts/run_suite.py --exclude device
```

## 3. Docker

```bash
docker build -t pos-qa-lab:local .
docker compose up -d api
curl http://127.0.0.1:8000/health
mkdir -p reports && chmod 777 reports
docker compose up --abort-on-container-exit --exit-code-from tests tests
docker compose down -v
```

Em Linux, o bind mount `./reports` precisa ser gravável pelo usuário `app` do container. O `chmod 777`
é aceitável no laboratório; em produção use volume nomeado ou UID/GID alinhados.

- A API usa o volume `pos_qa_data`.
- O serviço `tests` compartilha o mesmo volume para validar o banco.
- Os relatórios aparecem em `./reports/robot/`.
- O serviço `parallel` está no profile `parallel`:

```bash
docker compose --profile parallel run --rm parallel
```

## 4. Makefile

| Alvo | Ação |
|---|---|
| `make install` | instala dependências |
| `make lint` | `ruff check .` |
| `make unit` | `pytest` |
| `make robot` | Robot núcleo/ISO |
| `make parallel` | Pabot com 4 processos |
| `make device` | device suite |
| `make test` | lint + unit + robot |
| `make up` | sobe a API em Docker |
| `make down` | derruba containers |
| `make logs` | logs da API |
| `make docker-test` | sobe API + tests e derruba |
| `make clean` | remove relatórios gerados |

## 5. Scripts

```bash
./scripts/run_core.sh
./scripts/run_device.sh
./scripts/collect_logs.sh
```

`collect_logs.sh` empacota `reports/robot`, `reports/pabot`, `reports/device_run` e `reports/logcat`
em `reports/pos-qa-evidence-<timestamp>.tar.gz`.

## 6. Healthcheck e portas

- API local: `http://127.0.0.1:8000`
- API no Compose: `http://api:8000`
- Health: `GET /health`
- Swagger: `http://127.0.0.1:8000/docs`

O runner **falha de propósito** se já houver uma API respondendo na porta 8000. Isso evita o cenário
em que o teste local lê o banco local enquanto a API em Docker escreve no volume — foi o que aconteceu
na validação da alavanca 3 e virou o achado `FIND-LAB-011`.

## 7. Troubleshooting

| Sintoma | Causa provável | Ação |
|---|---|---|
| `Ja existe uma API respondendo` | container ou processo antigo na 8000 | `docker compose down` ou use `--no-api`/`--port` |
| `database is locked` | concorrência no SQLite | WAL e `busy_timeout` já configurados; evite rodar duas suítes contra o mesmo banco |
| `No keyword with name 'Use Terminal'` | library `Terminal` falhou ao inicializar | confira `API_URL` e o traceback do import |
| Pabot não encontra `robot` | `PATH` sem o venv | use `scripts/run_parallel.py`; ele prepende o venv |
| `adb: device not found` | emulador desligado | `adb devices`, inicie o AVD e rode `RUN_DEVICE_TESTS=1` |
| Relatório vazio no CI | step anterior falhou | baixe o artifact `robot-reports-*` e leia `api.log` |

## 8. Evidências

- `reports/robot/report.html`
- `reports/robot/log.html`
- `reports/robot/output.xml`
- `reports/robot/evidence/events-*.jsonl`
- `reports/pabot/report.html`
- `reports/pabot/evidence/events-*.jsonl`
- `docs/evidencias/`

## 9. Segurança e dados

- Nenhum segredo no repositório; use `.env` local e não versione.
- PANs são sintéticos e mascarados.
- O app de device é público e as credenciais são do demo.
- Não use dados de cliente, adquirente ou produção neste laboratório.
