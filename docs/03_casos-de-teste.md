# 03 — Casos de teste

**Projeto:** POS QA Lab
**Data de execução:** 19/11/2026
**Total:** 42 casos (37 de núcleo/ISO + 5 de dispositivo)

## Dados de teste

| Item | Valor |
|---|---|
| Valores | `10.00`, `12.00`, `15.00`, `25.00`, `30.00`, `40.00`, `45.00`, `50.00`, `80.00`, `89.90`, `100.00`, `125.90` |
| Parcelamento | `100.00` em 3x → `33.34 + 33.33 + 33.33` |
| Tokens | `tok_approved`, `tok_declined`, `tok_timeout`, `tok_error` |
| PAN sintético | `4111111111111111` (aprovado), `4000000000000002` (negado), `4000000000000003` (timeout) |
| Terminal | `TERM0001`, `TERM9101`, `TERM9102`, `TERM-SET-*`, `TERM-SLOW-01` |
| Merchant | `MERCH0001` |

## 1. Venda

| ID | Objetivo | Prioridade | Status |
|---|---|---|---|
| CT-PAY-01 | Venda aprovada com chave de idempotência, persistência e evento | P0 | Aprovado |
| CT-PAY-02 | Venda negada com código `05`, sem captura | P0 | Aprovado |
| CT-PAY-05 | Parcelamento em 3x com arredondamento e total preservado | P1 | Aprovado |

## 2. Cancelamento e estorno

| ID | Objetivo | Prioridade | Status |
|---|---|---|---|
| CT-PAY-03 | Cancelar transação autorizada antes da captura | P0 | Aprovado |
| CT-PAY-04 | Estorno parcial de 50,00 e total do restante | P0 | Aprovado |
| CT-PAY-06 | Rejeitar estorno antes da captura e cancelamento após captura | P0 | Aprovado |

## 3. Pré-autorização e captura

| ID | Objetivo | Prioridade | Status |
|---|---|---|---|
| CT-CAP-01 | Capturar integralmente uma transação autorizada | P0 | Aprovado |
| CT-CAP-02 | Captura parcial de 40,00 e estorno limitado ao capturado | P0 | Aprovado |
| CT-CAP-03 | Captura idempotente, valor divergente e captura após cancelamento | P0 | Aprovado |

**CT-CAP-01:** autorizar `100.00` com `capture=false`; capturar sem valor; esperado `CAPTURED` e
`captured_amount=100.00`.
**CT-CAP-02:** capturar `40.00` de `100.00`; estornar `40.00`; novo estorno deve retornar 409.
**CT-CAP-03:** capturar duas vezes o mesmo valor → 200; valor diferente → 409; captura após
cancelamento → 409.

## 4. Liquidação por terminal

| ID | Objetivo | Prioridade | Status |
|---|---|---|---|
| CT-SET-01 | Bruto, estorno e líquido de duas vendas capturadas | P0 | Aprovado |
| CT-SET-02 | Idempotência do fechamento e lote vazio | P0 | Aprovado |
| CT-SET-03 | Mesma chave de liquidação em terminal diferente | P1 | Aprovado |

**CT-SET-01:** vendas de `100.00` e `50.00`, estorno de `20.00`; esperado bruto `150.00`,
estorno `20.00`, líquido `130.00`, 2 itens e uma linha em `settlements`.
**CT-SET-02:** mesma chave devolve o mesmo `settlement_id`; nova chave sem transações retorna
`EMPTY`, 0 itens e líquido `0.00`.
**CT-SET-03:** chave já usada em outro terminal retorna 409 `IDEMPOTENCY_CONFLICT`.

## 5. Resiliência

| ID | Objetivo | Prioridade | Status |
|---|---|---|---|
| CT-RES-01 | Mesma chave de idempotência não cobra duas vezes | P0 | Aprovado |
| CT-RES-02 | Timeout seguido de retry não duplica a transação | P0 | Aprovado |
| CT-RES-03 | Fila offline sincroniza quando a conexão volta | P0 | Aprovado |
| CT-RES-04 | Reinício do terminal preserva a fila offline | P1 | Aprovado |

## 6. Concorrência e injeção de falhas

| ID | Objetivo | Prioridade | Status |
|---|---|---|---|
| CT-RES-05 | 10 requisições simultâneas com a mesma chave geram uma cobrança | P0 | Aprovado |
| CT-RES-06 | Latência de 1,5 s + timeout de 0,5 s + retry não duplica | P0 | Aprovado |

**CT-RES-05:** `ThreadPoolExecutor` com 10 chamadas e barreira; esperado um único `payment_id`,
uma linha no banco e todos os retornos 201.
**CT-RES-06:** `simulate_delay_ms=1500` e `request_timeout=0.5`; primeira chamada estoura timeout;
retry após 2 s recupera a mesma transação e mantém uma linha.

## 7. Contratos e observabilidade

| ID | Objetivo | Prioridade | Status |
|---|---|---|---|
| CT-CON-01 | Rejeitar payload/header inválido com 422 | P1 | Aprovado |
| CT-OBS-01 | `correlation_id` consistente em resposta, banco e evento | P1 | Aprovado |
| CT-CON-02 | Sync rejeita transação de outro terminal | P1 | Aprovado |

## 8. ISO 8583 — laboratório de formato

| ID | Objetivo | Prioridade | Status |
|---|---|---|---|
| CT-ISO-01 | Parse de `0100` com MTI, bitmap e campos 2, 3, 4, 7, 11, 12, 13, 41, 42, 49 | P2 | Aprovado |
| CT-ISO-02 | Parse de resposta `0110` com campo 39 = `00` | P2 | Aprovado |
| CT-ISO-03 | Bitmap secundário e campo 70 | P2 | Aprovado |
| CT-ISO-04 | Bitmap incompleto e campo truncado geram erro controlado | P2 | Aprovado |
| CT-ISO-05 | Round-trip build → parse preserva os campos | P2 | Aprovado |

## 9. ISO 8583 — fluxo de mensagens

| ID | Objetivo | Prioridade | Status |
|---|---|---|---|
| CT-ISO-06 | `0100` aprovado retorna `0110` com 39=`00` e approval code | P1 | Aprovado |
| CT-ISO-07 | `0100` negado retorna `0110` com 39=`05` | P1 | Aprovado |
| CT-ISO-08 | STAN duplicado devolve a mesma resposta e não cria segunda transação | P1 | Aprovado |
| CT-ISO-09 | `0400` retorna `0410` 00 e a segunda reversão é idempotente | P1 | Aprovado |
| CT-ISO-10 | `0800` retorna `0810` com 39=`00` | P2 | Aprovado |
| CT-ISO-11 | MTI não suportado gera erro controlado | P2 | Aprovado |

**Limite:** ASCII, sem BCD, MAC, rede real ou certificação EMV/PCI.

## 10. Data-driven de vendas

| ID | Objetivo | Prioridade | Status |
|---|---|---|---|
| CT-DD-01 | Venda aprovada de 10,00 em 1x | P1 | Aprovado |
| CT-DD-02 | Venda aprovada de 100,00 em 3x | P1 | Aprovado |
| CT-DD-03 | Venda negada de 89,90 | P1 | Aprovado |
| CT-DD-04 | Venda no limite mínimo de 0,01 | P2 | Aprovado |
| CT-DD-05 | Venda alta de 999.999,99 em 12x | P2 | Aprovado |

**Implementação:** `Test Template` do Robot chamando a keyword de negócio `Create And Assert Sale`,
da library `SalesWorkflow.py`. Cada linha é um caso; a library valida HTTP 201, status, código de
resposta e quantidade de parcelas.

## 11. Dispositivo — My Demo App

| ID | Objetivo | Prioridade | Status |
|---|---|---|---|
| CT-DEV-01 | Login válido com `bod@example.com` | P1 | Aprovado |
| CT-DEV-02 | Login sem credenciais exibe “Username is required” | P2 | Aprovado |
| CT-DEV-03 | Usuário bloqueado exibe mensagem de bloqueio | P2 | Aprovado |
| CT-DEV-04 | Adicionar produto ao carrinho e abrir a tela do carrinho | P1 | Aprovado |
| CT-DEV-05 | Background/foreground preserva a sessão | P2 | Aprovado |

**Execução:** 5/5 aprovados em 19/11/2026 no emulador `Pixel_8_Pro` (Android 16 / API 36), com
My Demo App 2.3.0, Appium 3.5.0 e UiAutomator2 7.0.0.
**Pendência:** o script `scripts/device_upgrade_check.py` ainda não foi executado.

## 12. Casos não aplicáveis

- Impressão térmica, pinpad, EMV, PCI PTS e certificação de bandeira: fora do escopo do laboratório.
- Teste de carga e segurança ofensiva: evolução futura, não parte desta entrega.
- Socket ISO 8583 real: o fluxo é processado em memória, sem rede.
