# 12 — Pacote de homologação

**Projeto:** POS QA Lab
**Versão:** 1.0.0
**Data:** 19/11/2026
**Responsável:** Emanuelle Gonçalves Paulino

## 1. Objetivo e escopo

Este pacote registra a decisão de prontidão do laboratório. Ele **não** declara homologação de POS,
adquirente, bandeira ou certificação EMV/PCI. O escopo é o laboratório público:

- API simulada de pagamento;
- terminal e periféricos simulados;
- fluxo ISO 8583 em memória;
- device suite em app público;
- Docker, CI, contrato, cobertura e k6.

## 2. Checklist de prontidão

| Área | Critério | Evidência | Status |
|---|---|---|---|
| Código | API, terminal, periféricos e ISO implementados | `src/`, `iso8583_lab/` | Pronto |
| Robot | 44 casos de núcleo/ISO/hardware | `reports/robot/report.html` | Pronto |
| Device | 5 casos no emulador Android 16 | `reports/device_run/report.html` | Pronto |
| Unitários | 52 testes | `pytest` | Pronto |
| Cobertura | ≥85% | 88,9% | Pronto |
| Contrato | 4 schemas OpenAPI | `tests/test_openapi_contract.py` | Pronto |
| Performance | k6 com thresholds | 436 req, 0% falha, p95 77,50 ms | Pronto |
| CI | matrix + Docker + k6 | GitHub Actions | Pronto |
| Documentação | escopo, plano, casos, matriz, execução, defeitos, limitações, arquitetura, runbook, métricas | `docs/01` a `docs/11` | Pronto |
| Segurança | sem APK, `.env` ou segredo óbvio versionado | `scripts/release_check.py` | Pronto |
| Limitações | declaradas | `docs/07_limitacoes.md` | Pronto |

## 3. Matriz de evidências

| Requisito | Evidência principal | Status |
|---|---|---|
| Venda, cancelamento, estorno, parcelamento | `docs/03`, `docs/05`, `reports/robot` | Coberto |
| Captura e liquidação | `docs/03`, `docs/05`, `tests/test_capture_settlement.py` | Coberto |
| Idempotência e concorrência | `docs/03`, `tests/test_concurrency.py` | Coberto |
| Offline e reinício | `docs/03`, `robot/suites/03_resilience.robot` | Coberto |
| ISO 8583 formato e fluxo | `docs/03`, `iso8583_lab/`, `tests/test_iso8583*` | Coberto |
| Hardware simulado | `docs/10`, `robot/suites/10_hardware_peripherals.robot` | Coberto |
| Device Android | `reports/device_run/` | Coberto |
| Contrato e cobertura | `tests/test_openapi_contract.py`, `docs/11` | Coberto |
| Performance | `reports/k6-summary.json`, `docs/11` | Coberto |

## 4. Critérios de go/no-go

### Go para o laboratório

- [x] 44/44 de núcleo/ISO/hardware
- [x] 5/5 de device em emulador
- [x] 52/52 unitários
- [x] cobertura ≥85% (88,9%)
- [x] contrato OpenAPI 4/4
- [x] k6 com thresholds verdes
- [x] CI matrix e Docker verdes
- [x] limitações e riscos residuais documentados
- [x] release check sem falhas

### No-go para produção

- [ ] POS, pinpad ou impressora reais
- [ ] EMV, certificação de bandeira e PCI PTS
- [ ] conexão com adquirente, bandeira ou emissor
- [ ] liquidação/clearing real
- [ ] hardware de campo, firmware e matriz de modelos
- [ ] SLA de performance em rede real

**Decisão:** **GO** para portfólio e laboratório; **NO-GO** para produção e certificação.

## 5. Checklist de aceite de fornecedor de hardware

Use este roteiro quando houver equipamento real:

- [ ] modelo, versão de hardware e firmware identificados;
- [ ] documentação de interface e protocolo (ex.: ESC/POS, serial, USB, Bluetooth) recebida;
- [ ] amostra para teste e critério de aceite acordados;
- [ ] matriz de compatibilidade (modelos, versões, regiões);
- [ ] plano de atualização e rollback;
- [ ] tratamento de falha: papel, conexão, energia, firmware corrompido;
- [ ] evidência de calibração/ certificação aplicável;
- [ ] contato técnico e SLA de suporte;
- [ ] critério de aprovação e responsável pela decisão.

## 6. Checklist de release

- [ ] `ruff check .`
- [ ] `pytest --cov ... --cov-fail-under=85`
- [ ] `python scripts/run_suite.py --exclude device`
- [ ] `python scripts/run_parallel.py --processes 4`
- [x] Docker Compose 44/44
- [x] k6 thresholds verdes
- [x] device suite 5/5
- [x] `python scripts/release_check.py`
- [x] `CHANGELOG.md` e versão `1.0.0`
- [ ] tag `v1.0.0`
- [ ] GitHub Release
- [ ] evidências publicadas ou anexadas

## 7. Riscos residuais

| Risco | Impacto | Mitigação |
|---|---|---|
| Simulação não representa hardware real | Alto | declarado; próximo passo é bancada/POS real |
| ISO 8583 sem BCD/MAC/rede | Médio | laboratório de formato; não é produção |
| Device apenas em emulador | Médio | executar em dispositivo físico antes de declarar compatibilidade |
| Pabot compartilha SQLite | Baixo | massa por chave/terminal; suítes de estado serializadas |
| Cobertura não mede qualidade das asserções | Médio | mutation testing como evolução |
| k6 é smoke de 10 VUs | Médio | não é SLA; ampliar carga/soak antes de produção |

## 8. Aprovação

| Papel | Nome | Decisão | Data |
|---|---|---|---|
| QA responsável | Emanuelle Gonçalves Paulino | GO (laboratório) | 19/11/2026 |
| Revisão técnica | — | pendente para produção | — |
| Aceite de negócio | — | não aplicável ao laboratório | — |

## 9. Referências

- [Relatório de execução](05_relatorio-execucao.md)
- [Relatório de defeitos](06_relatorio-defeitos.md)
- [Limitações](07_limitacoes.md)
- [Arquitetura Robot](08_robot-arquitetura.md)
- [Runbook Linux](09_runbook-linux.md)
- [Métricas de qualidade](11_metricas-qualidade.md)
