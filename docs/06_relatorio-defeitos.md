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
| DEF-LAB-004 | Fila offline falhava no Linux por caminho sem separador | Média | Corrigido |
| FIND-LAB-003 | Nome de keyword ambíguo em três libraries | Baixa | Corrigido |
| FIND-LAB-005 | Activity relativa e falta de `udid` impediam a sessão Appium | Baixa | Corrigido |
| FIND-LAB-006 | CT-DEV-04 usava container não clicável e o botão errado para abrir o carrinho | Baixa | Corrigido |
| FIND-LAB-007 | `Reset Acquirer` não era exposto porque o método se chamava `reset` | Baixa | Corrigido |
| FIND-LAB-008 | `Acquirer` não tinha `transaction_count` para o teste de duplicidade | Baixa | Corrigido |
| FIND-LAB-009 | Pabot não encontrava o executável `robot` no PATH do venv | Baixa | Corrigido |
| FIND-LAB-010 | Listener usava `data.starttime`, inexistente no Robot 7 | Baixa | Corrigido |
| FIND-LAB-011 | Runner local podia usar a API do Docker e ler banco diferente | Média | Corrigido |
| FIND-LAB-012 | Workflow de hardware sobrescrevia o status da impressora para OK | Baixa | Corrigido |
| FIND-LAB-013 | Bind mount de relatórios sem permissão no CI | Média | Corrigido |
| FIND-LAB-014 | Scripts shell com CRLF quebravam no Git Bash | Baixa | Corrigido |

- Defeitos de produto/mock: **1** (DEF-LAB-002).
- Defeitos de infraestrutura de teste: **2** (DEF-LAB-001 e DEF-LAB-004).
- Achados de automação/implementação: **11** (FIND-LAB-003, 005, 006, 007, 008, 009, 010, 011, 012, 013 e 014).

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

**Reteste:** 18/18 na versão 0.1.0; `api.log` com as requisições e `correlation_id`.

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

## DEF-LAB-004 — Fila offline falhava no Linux

| Campo | Conteúdo |
|---|---|
| Severidade | Média |
| Status | Corrigido |
| Ambiente | GitHub Actions, Ubuntu, Python 3.12 |
| Evidência | Run 44535925803: CT-RES-03 e CT-RES-04 com `OperationalError: unable to open database file` |

**Passos para reproduzir:**

1. Executar `CT-RES-03` ou `CT-RES-04` no Linux.
2. Observar a criação do caminho da fila offline.
3. Tentar abrir o SQLite.

**Esperado:** arquivo criado em `${TEMPDIR}/terminal_<key>.db`.
**Observado:** o caminho era montado como `${TEMPDIR}terminal_<key>.db`; no Windows `${TEMPDIR}` termina com
barra, no Linux não, gerando `/tmpterminal_<key>.db` e falha ao abrir o banco.

**Correção:** usar `Join Path    ${TEMPDIR}    terminal_${key}.db`.

**Reteste:** 18/18 na versão 0.1.0 no Windows e reexecução do CI no Linux.

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

**Reteste:** 18/18 na versão 0.1.0.

## FIND-LAB-005 — Sessão Appium não abria o app

| Campo | Conteúdo |
|---|---|
| Severidade | Baixa |
| Status | Corrigido |
| Tipo | Configuração de automação |
| Evidência | Primeira execução do device suite: 5 falhas de setup |

**Sintoma:** Appium não iniciava `com.saucelabs.mydemoapp.android` com a activity relativa
`.view.activities.SplashActivity` e sem `udid`.

**Correção:** usar a activity completa
`com.saucelabs.mydemoapp.android.view.activities.SplashActivity`, informar `udid=emulator-5554`,
`appWaitActivity` e `noReset=false`.

**Reteste:** CT-DEV-01 passou isolado; depois 5/5 no emulador.

## FIND-LAB-006 — CT-DEV-04 clicava no elemento errado

| Campo | Conteúdo |
|---|---|
| Severidade | Baixa |
| Status | Corrigido |
| Tipo | Script de teste |
| Evidência | Falha `totalPriceTV did not appear in 10 seconds` |

**Causa:** o teste clicava no container `addToCartLL` (não clicável) e no botão `cartBt`, que é
“Add to cart”, não o ícone do carrinho. A tela do carrinho nunca era aberta.

**Correção:** clicar em `cartBt` para adicionar e em `cartRL` para abrir o carrinho; validar
`totalPriceTV`.

**Reteste:** CT-DEV-04 passou isolado e na suíte completa 5/5.

## FIND-LAB-007 — `Reset Acquirer` não existia

| Campo | Conteúdo |
|---|---|
| Severidade | Baixa |
| Status | Corrigido |
| Tipo | Nome de keyword |
| Evidência | 6 casos da suíte ISO Flow falharam no setup |

**Sintoma:** Robot não encontrava `Reset Acquirer`; o método Python se chamava `reset`, gerando a
keyword genérica `Reset`, que não foi resolvida no contexto.

**Correção:** renomear o método para `reset_acquirer`.

**Reteste:** 6/6 casos da suíte ISO Flow aprovados.

## FIND-LAB-008 — `Acquirer` sem `transaction_count`

| Campo | Conteúdo |
|---|---|
| Severidade | Baixa |
| Status | Corrigido |
| Tipo | Lacuna de implementação detectada por teste unitário |
| Evidência | `tests/test_iso8583_acquirer.py::test_duplicate_authorization_is_idempotent` |

**Sintoma:** o teste de duplicidade não conseguia confirmar que apenas uma transação foi criada.

**Correção:** adicionar `Acquirer.transaction_count()` e expor `Transaction Count` na library Robot.

**Reteste:** teste unitário e CT-ISO-08 aprovados.

## FIND-LAB-009 — Pabot não encontrava o `robot`

| Campo | Conteúdo |
|---|---|
| Severidade | Baixa |
| Status | Corrigido |
| Tipo | Configuração de ambiente |
| Evidência | `FileNotFoundError: [WinError 2]` nos subprocessos do Pabot |

**Sintoma:** o Pabot iniciava, mas todos os workers falhavam antes de executar a suíte.

**Causa:** o `PATH` herdado não incluía `\.venv\Scripts`, então o Pabot não encontrava o comando
`robot` usado internamente.

**Correção:** prepender `Path(sys.executable).parent` ao `PATH` em `scripts/run_parallel.py`.

**Reteste:** 37/37 em 4 processos, tempo de parede 7,84 s.

## FIND-LAB-010 — Listener usava atributo inexistente

| Campo | Conteúdo |
|---|---|
| Severidade | Baixa |
| Status | Corrigido |
| Tipo | API do listener |
| Evidência | 36 erros `'TestCase' object has no attribute 'starttime'` no log |

**Sintoma:** cada início de teste gerava erro do listener, embora os testes passassem.

**Correção:** remover `data.starttime`; o JSONL já registra `timestamp` no evento.

**Reteste:** listener gerou JSONL sem erros para os 37 casos.

## FIND-LAB-011 — Runner local usava a API do Docker

| Campo | Conteúdo |
|---|---|
| Severidade | Média |
| Status | Corrigido |
| Tipo | Isolamento de ambiente |
| Evidência | 13 falhas locais `None == None` após subir a API em Docker na porta 8000 |

**Sintoma:** o runner local não conseguia subir a própria API porque a porta 8000 já estava ocupada
pelo container. Ele então executava os testes contra a API do Docker, mas as asserções liam o banco
local — resultados inconsistentes.

**Correção:** preflight em `run_suite.py` e `run_parallel.py`; se `/health` já responde na porta, o
runner falha com orientação para parar o container ou usar `--no-api`.

**Reteste:** após `docker compose down -v`, 37/37 local; Docker Compose 37/37.

## FIND-LAB-012 — Workflow sobrescrevia status da impressora

| Campo | Conteúdo |
|---|---|
| Severidade | Baixa |
| Status | Corrigido |
| Tipo | Lógica de simulação |
| Evidência | CT-HW-02 e CT-HW-03 retornavam `PRINTED` em vez de `PAPER_OUT`/`OFFLINE` |

**Sintoma:** o teste configurava a impressora antes da venda, mas o workflow aplicava o status
padrão `OK` durante a operação.

**Correção:** `printer_status` passou a ser opcional; o workflow só altera o status quando o parâmetro
é informado. O teste controla o estado pelo keyword `Set Printer Status`.

**Reteste:** CT-HW-02 e CT-HW-03 aprovados; 7/7 de hardware e 44/44 de núcleo.

## FIND-LAB-013 — Relatórios sem permissão no Docker CI

| Campo | Conteúdo |
|---|---|
| Severidade | Média |
| Status | Corrigido |
| Tipo | Permissão de bind mount |
| Evidência | `PermissionError: '/app/reports/robot'` no job Docker |

**Sintoma:** no runner Linux, o diretório `./reports` era criado pelo usuário do host e o container
rodava como `app`, sem permissão de escrita.

**Correção:** `mkdir -p reports && chmod 777 reports` no job Docker e no `make docker-test`; o runbook
documenta o requisito e a alternativa com volume nomeado.

**Reteste:** job Docker verde; 44/44 no container.

## FIND-LAB-014 — Scripts shell com CRLF

| Campo | Conteúdo |
|---|---|
| Severidade | Baixa |
| Status | Corrigido |
| Tipo | Line endings |
| Evidência | `set: pipefail: invalid option name` no Git Bash |

**Sintoma:** os scripts `.sh` eram checkoutados com CRLF no Windows e falhavam no `bash`.

**Correção:** `.gitattributes` com `*.sh text eol=lf` e normalização dos arquivos.

**Reteste:** `bash -n` nos três scripts e `collect_logs.sh` gerando o pacote de evidências.

## Lições

- O runner precisa tratar `stdout` de processo filho; `PIPE` sem leitura é uma armadilha clássica.
- Nomes de keywords devem ser únicos por responsabilidade ou qualificados no uso.
- Um caso de contrato no sync encontrou um comportamento que os casos felizes não pegariam.
- O device suite só entra no relatório como aprovado depois de executado em Android/Appium.
- Status de periférico deve ser controlado pelo teste, não sobrescrito pelo workflow.
- Ambientes local e Docker precisam de isolamento explícito de porta e banco.
