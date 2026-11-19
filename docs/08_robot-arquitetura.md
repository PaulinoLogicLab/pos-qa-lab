# 08 — Arquitetura Robot de produção

**Projeto:** POS QA Lab
**Versão:** 0.5.0
**Data:** 19/11/2026

## 1. Camadas

```text
Suites .robot
  └── resources/            keywords de negócio em Robot
        └── libraries/      Python: HTTP, banco, estado, parsing, workflow
              └── src/      API FastAPI, terminal simulator
              └── iso8583_lab/
```

- **Suites** descrevem o cenário e as expectativas de negócio.
- **Resources** compõem keywords reutilizáveis (`Create Authorized Payment`, `Settle Terminal Batch`).
- **Libraries** concentram integração e regras de asserção; nenhuma suite abre HTTP ou SQL direto.
- **src** e **iso8583_lab** são o sistema sob teste; os testes não importam detalhes internos além do necessário.

## 2. Library de negócio

`libraries/SalesWorkflow.py` expõe keywords de alto nível:

- `Create Sale`
- `Create And Assert Sale`
- `Create Authorized And Capture`
- `Settle And Assert`

A library valida HTTP, status, código de resposta e quantidade de parcelas. As suítes ficam curtas e
legíveis; a lógica de negócio não se espalha por dezenas de linhas de `.robot`.

## 3. Data-driven

`robot/suites/09_data_driven_sales.robot` usa `Test Template` e a keyword `Create And Assert Sale`.
Cada linha é um caso:

| Caso | Valor | Parcelas | Token | Status | Código |
|---|---:|---:|---|---|---|
| CT-DD-01 | 10,00 | 1 | aprovado | CAPTURED | 00 |
| CT-DD-02 | 100,00 | 3 | aprovado | CAPTURED | 00 |
| CT-DD-03 | 89,90 | 1 | negado | DECLINED | 05 |
| CT-DD-04 | 0,01 | 1 | aprovado | CAPTURED | 00 |
| CT-DD-05 | 999.999,99 | 12 | aprovado | CAPTURED | 00 |

Adicionar um novo valor é adicionar uma linha, não duplicar um caso inteiro.

## 4. Pabot

`scripts/run_parallel.py` sobe a API e executa:

```bash
python scripts/run_parallel.py --processes 4
```

- 44 casos em 4 processos.
- `PABOTQUEUEINDEX` fica disponível para isolar massa, se necessário.
- Suítes que compartilham estado devem ser marcadas `serial`; a suíte de liquidação já usa terminais
  únicos por caso.
- O tempo de parede foi 8,00 s; a soma dos casos foi 4,13 s. Em suítes curtas, o overhead do Pabot
  supera o ganho — o valor aqui é a capacidade de escalar.

## 5. Listener de evidência

`libraries/RobotListener.py` implementa o listener API v3 e grava um JSONL por processo:

```json
{"event":"end_test","name":"CT-PAY-01 ...","tags":["critical","payment","smoke"],"status":"PASS","elapsed_ms":57}
```

Arquivos: `reports/robot/evidence/events-<pid>.jsonl` e `reports/pabot/evidence/events-<pid>.jsonl`.
O runner limpa evidências antigas antes de cada execução.

## 6. Hardware simulado

A suíte `10_hardware_peripherals.robot` usa a library `Hardware.py`, que compõe `TerminalSimulator`,
`Printer`, `Pinpad` e `TerminalLifecycle`. São modelos determinísticos, não drivers reais. Detalhes em
[10_hardware-perifericos.md](10_hardware-perifericos.md).

## 7. Tags

| Tag | Uso |
|---|---|
| `smoke` | subconjunto rápido |
| `critical` | risco alto |
| `negative` | fluxo de erro |
| `resilience` | timeout, retry, offline |
| `concurrency` | concorrência |
| `settlement` | captura/liquidação |
| `contract` | contratos e observabilidade |
| `iso8583` | parser e fluxo ISO |
| `data_driven` | template de vendas |
| `device` | Appium, executado à parte |

## 8. CI matrix

O workflow `robot-core` roda em Python 3.11, 3.12 e 3.13:

1. `ruff check .`
2. `python -m pytest`
3. `python scripts/run_suite.py --exclude device`
4. `python scripts/run_parallel.py --processes 4` (somente 3.12)
5. resumo e artifact dos relatórios

## 9. Decisões

- **Library Python para negócio:** evita suites gigantes e mantém asserções testáveis.
- **Template nativo do Robot:** sem dependência extra para data-driven.
- **Pabot:** mostra escala, mas não é usado para mascarar flakiness; falhas continuam visíveis.
- **Listener JSONL:** evidência leve e legível por máquina, sem duplicar o `output.xml`.
- **API compartilhada no Pabot:** chaves e terminais únicos por caso; liquidação e cenários de estado
  devem permanecer serializados.

## 10. Limitações

- O Pabot não isola banco por worker; a massa é isolada por chave/terminal.
- O listener registra ciclo de vida e status, não request/response HTTP completos.
- O device suite não roda no CI por exigir emulador/Appium.
- A execução paralela é de suites, não de casos individuais dentro da mesma suite.
