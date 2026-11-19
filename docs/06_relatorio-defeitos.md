# 06 — Relatório de defeitos e achados

**Projeto:** POS QA Lab
**Ciclo:** 1
**Data:** 19/11/2026
**Responsável:** Emanuelle Gonçalves Paulino

> Este laboratório não representa um produto real. Os defeitos abaixo são do mock, do runner ou da
> arquitetura de testes; não são achados de produção da Stone ou de qualquer adquirente.

## Resumo

| ID | Título | Severidade | Status |
|---|---|---|---|
| DEF-LAB-001 | Runner bloqueava a API por não drenar o `stdout` | Média | Corrigido |
| DEF-LAB-002 | Sync aceitava transação de outro terminal | Média | Corrigido |
| FIND-LAB-003 | Nome de keyword ambíguo em três libraries | Baixa | Corrigido |

- Defeitos de produto/mock: **1** (DEF-LAB-002).
- Defeitos de infraestrutura de teste: **1** (DEF-LAB-001).
- Achado de automação: **1** (FIND-LAB-003).

## DEF-LAB-001 — Runner bloqueava a API

| Campo | Conteúdo |
|---|---|
| Severidade | Média |
| Status | Corrigido |
| Ambiente | Windows, Python 3.13.14, Uvicorn 0.54.0 |
| Evidência | Primeira execução: 9 falhas por `ReadTimeout`; `reports/robot/output.xml` |

**Passos para reproduzir:**

1. Iniciar a API pelo runner com `stdout=subprocess.PIPE`.
2. Executar a suíte de resiliência e contratos.
3. Observar que, após alguns casos, as requisições passam a estourar `ReadTimeout`.

**Esperado:** API respondendo durante toda a execução.
**Observado:** o processo da API parava de responder e os casos falhavam por timeout.

**Causa raiz:** o runner não consumia o `stdout` do Uvicorn. O buffer do pipe enchia e o processo ficava
bloqueado ao tentar escrever log.

**Correção:** redirecionar `stdout`/`stderr` para `reports/robot/api.log` e fechar o arquivo no `finally`.

**Reteste:** 18/18 casos aprovados; `api.log` com as requisições e `correlation_id`.

## DEF-LAB-002 — Sync aceitava transação de outro terminal

| Campo | Conteúdo |
|---|---|
| Severidade | Média |
| Status | Corrigido |
| Ambiente | API local + SQLite |
| Evidência | CT-CON-02 e `tests/test_api.py::test_sync_rejects_transaction_from_another_terminal` |

**Passos para reproduzir:**

1. Enviar `POST /api/v1/terminals/TERM0001/sync`.
2. No corpo, informar uma transação com `terminal_id=TERM9999`.
3. Consultar o banco.

**Esperado:** rejeitar a transação com 422 e não criar pagamento.
**Observado:** a transação era criada para `TERM9999`, ignorando o terminal da rota.

**Causa raiz:** o serviço de sync não comparava `transaction.terminal_id` com o `terminal_id` do path.

**Correção:** validação no `sync_transactions`, retornando `TERMINAL_MISMATCH` e nenhum registro.

**Reteste:** CT-CON-02 aprovado; teste unitário confirma `count=0` para a chave enviada.

## FIND-LAB-003 — Keyword `Get Payment` ambígua

| Campo | Conteúdo |
|---|---|
| Severidade | Baixa |
| Status | Corrigido |
| Tipo | Arquitetura de automação, não defeito de produto |

**Sintoma:** Robot falhou com “Multiple keywords with name 'Get Payment' found” porque `Database`,
`PaymentApi` e `Terminal` expõem o mesmo nome.

**Correção:** chamadas qualificadas (`Database.Get Payment`, `Database.Get Refunds`,
`Database.Get Events`) e keyword de negócio `Get Payment Row`.

**Reteste:** 18/18 aprovados.

## Lições

- O runner precisa tratar `stdout` de processo filho; `PIPE` sem leitura é uma armadilha clássica.
- Nomes de keywords devem ser únicos por responsabilidade ou qualificados no uso.
- Um caso de contrato no sync encontrou um comportamento que os casos felizes não pegariam.
- O device suite só entra no relatório como aprovado depois de executado em Android/Appium.
