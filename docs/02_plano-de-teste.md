# 02 — Plano de teste

**Projeto:** POS QA Lab
**Versão:** 0.1.0
**Data:** 19/11/2026

## 1. Estratégia

Teste baseado em risco, com foco nas falhas que mais impactam uma jornada de pagamento:

1. **Transação financeira**: venda, recusa, cancelamento, estorno e parcelamento.
2. **Resiliência**: timeout, retry, idempotência, offline, sincronização e reinício.
3. **Contrato e observabilidade**: validação de entrada, códigos de erro, `correlation_id` e eventos.
4. **Formato**: parsing ISO 8583 com dados sintéticos.
5. **Dispositivo**: instalação, atualização, login e navegação no app público.

## 2. Níveis e tipos

| Nível | Ferramenta | Escopo |
|---|---|---|
| Unitário | pytest | regras da API, parser ISO, fila do terminal |
| Integração | Robot + API + SQLite | jornada completa via HTTP e banco |
| Contrato | Robot | payloads inválidos, headers, códigos de erro |
| Dispositivo | Robot + AppiumLibrary | app público Android |
| Regressão | Robot tags | `smoke`, `regression`, `resilience`, `contract`, `iso8583` |

## 3. Ambiente

| Item | Versão / configuração |
|---|---|
| Python | 3.13.14 |
| Robot Framework | 7.5.1 |
| FastAPI | 0.165.0 |
| Uvicorn | 0.54.0 |
| Banco | SQLite local (`data/pos_qa.db`) |
| API | `http://127.0.0.1:8000` |
| Device | Android + Appium 2 + UiAutomator2 + My Demo App |

## 4. Dados de teste

- Valores: `10.00`, `12.00`, `15.00`, `25.00`, `30.00`, `45.00`, `80.00`, `89.90`, `100.00`, `125.90`.
- Parcelamento: `100.00` em 3x → `33.34 + 33.33 + 33.33`.
- Tokens de decisão: `tok_approved`, `tok_declined`, `tok_timeout`, `tok_error`.
- Chaves de idempotência: UUID v4 por caso; chaves fixas apenas em testes unitários.
- PAN sintético: `4111111111111111`, sempre mascarado em log/relatório.
- Massa isolada por `tmp_path` nos testes unitários e por `TEMPDIR` nos casos de fila offline.

## 5. Critérios de entrada

- Dependências instaladas.
- API sobe e `/health` responde 200.
- Banco inicializado.
- Para device: `adb devices` com um dispositivo e Appium ativo.

## 6. Critérios de saída

- 100% dos casos do núcleo e ISO executados.
- Nenhuma falha aberta no núcleo.
- Relatório e resumo gerados.
- Defeitos encontrados com evidência e status.
- Limitações registradas.

## 7. Execução

```bash
python scripts/run_suite.py --exclude device
python scripts/summarize_results.py
pytest
```

O runner:

1. inicia a API em segundo plano;
2. espera `/health`;
3. executa o Robot;
4. encerra a API;
5. grava `reports/robot/api.log`.

## 8. Evidência por caso

- `output.xml`, `log.html` e `report.html` do Robot.
- `summary.json` com totais e tempo.
- Consultas ao SQLite para status, eventos e refunds.
- `api.log` com `correlation_id` e transições.
- Para device: screenshot em falha e `logcat` em `reports/logcat/`.

## 9. Rastreabilidade

Cada requisito funcional (RF) e não funcional (RNF) é mapeado para casos na
[matriz de rastreabilidade](04_matriz-rastreabilidade.md). Casos sem requisito são evitados; requisitos sem
caso são registrados como lacuna.

## 10. Cronograma

| Fase | Entrega |
|---|---|
| 1 | Escopo, riscos, plano e estrutura |
| 2 | API, banco e Docker/local |
| 3 | Terminal simulator e testes unitários |
| 4 | Suítes de venda, cancelamento e estorno |
| 5 | Resiliência, contratos e observabilidade |
| 6 | ISO 8583 |
| 7 | Device suite e script de upgrade |
| 8 | Relatórios, matriz, limitações e README |

O núcleo e o ISO foram executados em 19/11/2026. O device suite foi implementado, mas não executado
neste ambiente por ausência de emulador/Appium.
