# 03 — Casos de teste

**Projeto:** POS QA Lab
**Data de execução:** 19/11/2026
**Total:** 23 casos (23 executados)

## Dados de teste

| Item | Valor |
|---|---|
| Valores | `10.00`, `12.00`, `15.00`, `25.00`, `30.00`, `45.00`, `80.00`, `89.90`, `100.00`, `125.90` |
| Parcelamento | `100.00` em 3x → `33.34 + 33.33 + 33.33` |
| Tokens | `tok_approved`, `tok_declined`, `tok_timeout`, `tok_error` |
| PAN sintético | `4111111111111111` (mascarado em log) |
| Terminal | `TERM0001`, `TERM9101`, `TERM9102` |
| Merchant | `MERCH0001` |

## 1. Venda

| ID | Objetivo | Prioridade | Status |
|---|---|---|---|
| CT-PAY-01 | Venda aprovada com chave de idempotência, persistência e evento | P0 | Aprovado |
| CT-PAY-02 | Venda negada com código `05`, sem captura | P0 | Aprovado |
| CT-PAY-05 | Parcelamento em 3x com arredondamento e total preservado | P1 | Aprovado |

**CT-PAY-01 — passos:** enviar `POST /api/v1/payments` com `amount=125.90`, `tok_approved` e
`Idempotency-Key`; consultar o pagamento no banco; verificar evento.
**Esperado:** HTTP 201, status `CAPTURED`, código `00`, `amount_cents=12590`, uma única linha e um
evento `PAYMENT_CREATED`.

**CT-PAY-02 — passos:** enviar venda com `tok_declined`.
**Esperado:** HTTP 201, status `DECLINED`, código `05`, sem captura.

**CT-PAY-05 — passos:** enviar `amount=100.00` e `installments=3`.
**Esperado:** três parcelas `33.34`, `33.33` e `33.33`.

## 2. Cancelamento e estorno

| ID | Objetivo | Prioridade | Status |
|---|---|---|---|
| CT-PAY-03 | Cancelar transação autorizada antes da captura | P0 | Aprovado |
| CT-PAY-04 | Estorno parcial de 50,00 e total do restante | P0 | Aprovado |
| CT-PAY-06 | Rejeitar estorno antes da captura e cancelamento após captura | P0 | Aprovado |

**CT-PAY-03:** criar com `capture=false`, chamar `/cancel`; esperado `CANCELLED`.
**CT-PAY-04:** criar `125.90`, estornar `50.00`, depois estornar o restante; esperado
`PARTIALLY_REFUNDED` → `REFUNDED`, `refunded_amount=125.90` e dois registros de refund.
**CT-PAY-06:** estorno de autorizada e cancelamento de capturada devem retornar HTTP 409 com
`INVALID_TRANSITION`.

## 3. Resiliência

| ID | Objetivo | Prioridade | Status |
|---|---|---|---|
| CT-RES-01 | Mesma chave de idempotência não cobra duas vezes | P0 | Aprovado |
| CT-RES-02 | Timeout seguido de retry não duplica a transação | P0 | Aprovado |
| CT-RES-03 | Fila offline sincroniza quando a conexão volta | P0 | Aprovado |
| CT-RES-04 | Reinício do terminal preserva a fila offline | P1 | Aprovado |

**CT-RES-01:** duas chamadas com a mesma chave e o mesmo payload; esperado mesmo `payment_id` e uma
linha no banco.
**CT-RES-02:** `tok_timeout` retorna HTTP 504, status `FAILED` e código `91`; retry devolve o mesmo
pagamento e não cria duplicata.
**CT-RES-03:** `go_offline`, venda de `25.00`, `queue_size=1`, `go_online`, `sync`; esperado
`CAPTURED`, fila zerada e segundo sync sem transações.
**CT-RES-04:** venda offline de `30.00`, `restart`, `queue_size=1`, `sync`; esperado `CAPTURED`.

## 4. Contratos e observabilidade

| ID | Objetivo | Prioridade | Status |
|---|---|---|---|
| CT-CON-01 | Rejeitar payload/header inválido com 422 | P1 | Aprovado |
| CT-OBS-01 | `correlation_id` consistente em resposta, banco e evento | P1 | Aprovado |
| CT-CON-02 | Sync rejeita transação de outro terminal | P1 | Aprovado |

**CT-CON-01:** sem `Idempotency-Key`, valor negativo, moeda `USD` e parcelas `0`; esperado HTTP 422
com `VALIDATION_ERROR` ou `UNSUPPORTED_CURRENCY`.
**CT-OBS-01:** enviar `X-Correlation-Id`; esperado o mesmo valor no header de resposta, na linha do
pagamento e no primeiro evento.
**CT-CON-02:** enviar transação `TERM9999` para `/terminals/TERM0001/sync`; esperado resultado 422
`TERMINAL_MISMATCH` e nenhum pagamento criado.

## 5. ISO 8583 — laboratório

| ID | Objetivo | Prioridade | Status |
|---|---|---|---|
| CT-ISO-01 | Parse de `0100` com MTI, bitmap e campos 2, 3, 4, 7, 11, 12, 13, 41, 42, 49 | P2 | Aprovado |
| CT-ISO-02 | Parse de resposta `0110` com campo 39 = `00` | P2 | Aprovado |
| CT-ISO-03 | Bitmap secundário e campo 70 | P2 | Aprovado |
| CT-ISO-04 | Bitmap incompleto e campo truncado geram erro controlado | P2 | Aprovado |
| CT-ISO-05 | Round-trip build → parse preserva os campos | P2 | Aprovado |

**Limite:** ASCII, sem BCD, MAC, rede ou certificação. PAN sintético e mascarado.

## 6. Dispositivo — My Demo App

| ID | Objetivo | Prioridade | Status |
|---|---|---|---|
| CT-DEV-01 | Login válido com `bod@example.com` | P1 | Aprovado |
| CT-DEV-02 | Login sem credenciais exibe “Username is required” | P2 | Aprovado |
| CT-DEV-03 | Usuário bloqueado exibe mensagem de bloqueio | P2 | Aprovado |
| CT-DEV-04 | Adicionar produto ao carrinho e abrir a tela do carrinho | P1 | Aprovado |
| CT-DEV-05 | Background/foreground preserva a sessão | P2 | Aprovado |

**Pré-requisitos:** Android SDK, emulador/dispositivo, Appium 2+, UiAutomator2 e APK do demo.
**Execução:** 5/5 aprovados em 19/11/2026 no emulador `Pixel_8_Pro` (Android 16 / API 36), com
My Demo App 2.3.0, Appium 3.5.0 e UiAutomator2 7.0.0.
**Observação:** o script `scripts/device_upgrade_check.py` cobre a evidência de instalação/atualização,
mas ainda não foi executado.

## 7. Casos não aplicáveis

- Impressão térmica, pinpad, EMV, PCI PTS e certificação de bandeira: fora do escopo do laboratório.
- Teste de carga e segurança ofensiva: evolução futura, não parte desta entrega.
