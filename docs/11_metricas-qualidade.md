# 11 — Métricas de qualidade

**Projeto:** POS QA Lab
**Versão:** 1.0.0
**Data:** 19/11/2026

## 1. Resultado atual

| Métrica | Valor |
|---|---:|
| Casos Robot | 49 |
| Núcleo/ISO/hardware | 44/44 |
| Device | 5/5 |
| Testes unitários | 52/52 |
| Cobertura de linhas | **88,9%** |
| Contrato OpenAPI | 4/4 |
| Property-based tests | 3/3 |
| k6 — requisições | 436 |
| k6 — falha HTTP | **0,00%** |
| k6 — p95 | **77,50 ms** |
| Pabot | 44/44 em 4 processos |
| Docker Compose | 44/44 |
| Release check | 9/9 |

## 2. Cobertura por módulo

| Módulo | Cobertura |
|---|---:|
| `src/api/models.py` | 100% |
| `src/api/db.py` | 94% |
| `src/api/main.py` | 93% |
| `src/terminal/peripherals.py` | 92% |
| `src/api/service.py` | 90% |
| `iso8583_lab/acquirer.py` | 89% |
| `iso8583_lab/parser.py` | 85% |
| `src/terminal/simulator.py` | 71% |
| **Total** | **88,9%** |

O gate do CI exige **85%**. O ponto mais baixo é o simulador de terminal, que tem caminhos de
fila/sync cobertos por Robot e não por teste unitário.

## 3. Contrato

`tests/test_openapi_contract.py` valida respostas reais contra os schemas do `/openapi.json`:

- `PaymentResponse` — criação, captura;
- `SettlementResponse` — liquidação;
- `ErrorResponse` — transição inválida.

Os refs locais (`#/components/schemas/...`) são resolvidos no próprio teste; não há schema duplicado
mantido à mão.

## 4. Property-based

`tests/test_properties.py` usa Hypothesis para:

- soma das parcelas igual ao total, para qualquer valor e número de parcelas;
- round-trip de centavos (`cents_to_str` → `to_cents`);
- round-trip do campo 4 do ISO 8583.

## 5. Performance — k6

`performance/payment_load.js`:

| Item | Valor |
|---|---:|
| Estágios | 2 s subida, 5 s em 10 VUs, 2 s descida |
| Requisições | 436 |
| Checks | 872/872 |
| Falha HTTP | 0,00% |
| p95 | 77,50 ms |
| Threshold | p95 < 500 ms e falha < 1% |

Execução:

```bash
docker compose up -d api
docker compose --profile perf run --rm k6
```

Resumo: `reports/k6-summary.json`.

## 6. O que não foi medido

- Mutation testing não foi executado nesta versão.
- Carga acima de 10 VUs, soak test e teste de estresse não fazem parte do smoke.
- Latência de rede real, adquirente e banco gerenciado não estão no caminho.
- Flakiness histórica não é calculada; o Pabot não repete falhas automaticamente.

## 7. Gate de qualidade

O CI falha se:

1. `ruff check .` encontrar erro;
2. `pytest` falhar;
3. cobertura ficar abaixo de 85%;
4. Robot núcleo/ISO/hardware falhar;
5. Docker Compose falhar;
6. k6 violar os thresholds.

O device suite permanece fora do CI por exigir emulador/Appium.
