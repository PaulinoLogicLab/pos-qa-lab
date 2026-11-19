# 10 — Hardware e periféricos simulados

**Projeto:** POS QA Lab
**Versão:** 1.0.0
**Data:** 19/11/2026

## 1. Por que simular

O laboratório não tem POS, pinpad ou impressora térmica reais. Para exercitar o comportamento que
importa em campo — papel acabou, impressora desconectou, pinpad deu timeout, terminal reiniciou — foi
criado um modelo determinístico em Python. Ele **não** é driver de hardware e não substitui teste em
equipamento real.

## 2. Modelos

### Impressora

`src/terminal/peripherals.py::Printer`

| Estado | Comportamento |
|---|---|
| `OK` | imprime e incrementa `printed` |
| `PAPER_OUT` | mantém recibo em `pending` |
| `OFFLINE` | mantém recibo em `pending` |

Operações: `set_status`, `print_receipt`, `refill`, `reconnect`, `reprint_pending`,
`pending_count`, `printed_count`.

### Pinpad

`Pinpad`

| Modo/estado | Resultado |
|---|---|
| `CONNECTED` + `OK` | `APPROVED` |
| `TIMEOUT` | `TIMEOUT` |
| `CANCELLED` | `CANCELLED` |
| `DISCONNECTED` | `DISCONNECTED` (prioridade sobre o modo) |

### Ciclo do terminal

`TerminalLifecycle`

- `reboot()` incrementa `boot_count`;
- `update_firmware(version)` altera a versão;
- `update_config(key, value)` altera a configuração;
- a fila offline do `TerminalSimulator` sobrevive ao reboot e à atualização.

## 3. Workflow

`libraries/Hardware.py::Hardware` compõe terminal + impressora + pinpad + ciclo de vida:

1. solicita PIN ao pinpad;
2. se não aprovado, encerra sem chamar a API;
3. se aprovado, executa a venda online ou enfileira offline;
4. monta o recibo e imprime;
5. devolve status da venda, status da impressão, `payment_id` e chave de idempotência.

## 4. Casos

| ID | Cenário | Resultado |
|---|---|---|
| CT-HW-01 | Pinpad OK + impressora OK | venda capturada e recibo impresso |
| CT-HW-02 | Papel acabou | venda capturada, recibo pendente, reimpressão após recarga |
| CT-HW-03 | Impressora offline | recibo pendente, reimpressão após reconexão |
| CT-HW-04 | Timeout do pinpad | sem chamada à API e sem pagamento |
| CT-HW-05 | Cancelamento no pinpad | sem chamada à API e sem pagamento |
| CT-HW-06 | Reboot no meio | fila offline preservada e sync conclui |
| CT-HW-07 | Firmware/config | fila preservada e versão/config atualizadas |

## 5. Limitações

- Não há impressora térmica, pinpad ou firmware reais.
- Não há teste de comunicação serial, USB, Bluetooth ou protocolo proprietário.
- Não há certificação de hardware ou de bandeira.
- O modelo não cobre papel enroscado, cabeçote queimado, bateria, temperatura ou falha elétrica.
- A fila offline é SQLite local; não é a fila de um POS real.

## 6. Evolução possível

1. Rodar os mesmos cenários em um POS de laboratório, se houver hardware.
2. Adicionar protocolo de impressão ESC/POS simulado.
3. Adicionar injeção de falha de energia e corrupção de fila.
4. Adicionar matriz de modelos/firmwares.
