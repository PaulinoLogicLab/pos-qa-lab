*** Settings ***
Documentation     Simulacao de perifericos e ciclo do terminal: impressora, pinpad, reboot e firmware.
...               Sao modelos deterministicos de laboratorio, nao drivers de hardware real.
Library           ../../libraries/Hardware.py
Resource          ../resources/common.resource
Suite Setup       Check Api Health
Test Tags         hardware    peripherals    regression

*** Keywords ***
New Hardware Device
    [Arguments]    ${terminal_id}    ${suffix}
    ${db}=    Join Path    ${TEMPDIR}    hardware_${suffix}.db
    Use Device    ${terminal_id}    ${db}

Assert Payment Count
    [Arguments]    ${idempotency_key}    ${expected}
    ${count}=    Database.Count Payments By Idempotency    ${idempotency_key}
    Should Be Equal As Integers    ${count}    ${expected}

*** Test Cases ***
CT-HW-01 Venda com pinpad e impressora OK
    [Documentation]    Pinpad aprova, venda e capturada e recibo e impresso.
    [Tags]    critical
    ${key}=    Generate Idempotency Key
    New Hardware Device    TERM-HW-01    ${key}
    ${sale}=    Sale With Pinpad    25.00
    Should Be True    ${sale}[authorized]
    Should Be Equal    ${sale}[status]    CAPTURED
    Should Be Equal    ${sale}[print_status]    PRINTED
    ${printed}=    Printer Printed Count
    Should Be Equal As Integers    ${printed}    1
    Assert Payment Count    ${sale}[idempotency_key]    1

CT-HW-02 Impressora sem papel deixa recibo pendente
    [Documentation]    A venda conclui, o recibo fica pendente e a reimpressao ocorre apos a recarga.
    [Tags]    critical
    ${key}=    Generate Idempotency Key
    New Hardware Device    TERM-HW-02    ${key}
    Set Printer Status    PAPER_OUT
    ${sale}=    Sale With Pinpad    30.00
    Should Be Equal    ${sale}[status]    CAPTURED
    Should Be Equal    ${sale}[print_status]    PAPER_OUT
    ${pending}=    Printer Pending Count
    Should Be Equal As Integers    ${pending}    1
    Refill Printer
    ${reprint}=    Reprint Pending
    Should Be Equal As Integers    ${reprint}[reprinted]    1
    ${printed}=    Printer Printed Count
    Should Be Equal As Integers    ${printed}    1
    Assert Payment Count    ${sale}[idempotency_key]    1

CT-HW-03 Impressora offline e reconectada
    [Documentation]    Sem conexao, o recibo fica pendente; a reconexao permite reimprimir.
    [Tags]    negative
    ${key}=    Generate Idempotency Key
    New Hardware Device    TERM-HW-03    ${key}
    Set Printer Status    OFFLINE
    ${sale}=    Sale With Pinpad    35.00
    Should Be Equal    ${sale}[print_status]    OFFLINE
    ${pending}=    Printer Pending Count
    Should Be Equal As Integers    ${pending}    1
    Reconnect Printer
    ${reprint}=    Reprint Pending
    Should Be Equal As Integers    ${reprint}[reprinted]    1
    Assert Payment Count    ${sale}[idempotency_key]    1

CT-HW-04 Timeout do pinpad nao autoriza venda
    [Documentation]    O timeout impede a chamada a API e nao cria pagamento.
    [Tags]    critical
    ${key}=    Generate Idempotency Key
    New Hardware Device    TERM-HW-04    ${key}
    ${sale}=    Sale With Pinpad    40.00    pinpad_mode=TIMEOUT
    Should Be Equal    ${sale}[authorized]    ${FALSE}
    Should Be Equal    ${sale}[status]    PINPAD_TIMEOUT
    Should Be Equal    ${sale}[payment]    ${None}
    Assert Payment Count    ${sale}[idempotency_key]    0

CT-HW-05 Cancelamento do pinpad nao autoriza venda
    [Documentation]    O cancelamento no pinpad encerra a tentativa sem criar pagamento.
    [Tags]    negative
    ${key}=    Generate Idempotency Key
    New Hardware Device    TERM-HW-05    ${key}
    ${sale}=    Sale With Pinpad    45.00    pinpad_mode=CANCELLED
    Should Be Equal    ${sale}[authorized]    ${FALSE}
    Should Be Equal    ${sale}[status]    PINPAD_CANCELLED
    Assert Payment Count    ${sale}[idempotency_key]    0

CT-HW-06 Reboot no meio da transacao preserva a fila
    [Documentation]    Uma venda offline fica na fila; o reboot preserva e o sync conclui.
    [Tags]    critical
    ${key}=    Generate Idempotency Key
    New Hardware Device    TERM-HW-06    ${key}
    ${sale}=    Sale With Pinpad    50.00    online=${FALSE}
    Should Be Equal    ${sale}[status]    QUEUED_OFFLINE
    ${queued}=    Hardware Queue Size
    Should Be Equal As Integers    ${queued}    1
    ${reboot}=    Reboot Terminal
    Should Be Equal As Integers    ${reboot}[queue_size]    1
    Hardware Go Online
    ${sync}=    Hardware Sync
    Should Be Equal As Integers    ${sync}[synced]    1
    Assert Payment Count    ${sale}[idempotency_key]    1

CT-HW-07 Atualizacao de firmware e configuracao preserva a fila
    [Documentation]    Firmware e configuracao mudam sem perder a venda pendente.
    [Tags]    critical
    ${key}=    Generate Idempotency Key
    New Hardware Device    TERM-HW-07    ${key}
    ${sale}=    Sale With Pinpad    60.00    online=${FALSE}
    Should Be Equal    ${sale}[status]    QUEUED_OFFLINE
    Update Firmware    1.1.0
    Update Config    display_language    en-US
    ${version}=    Firmware Version
    Should Be Equal    ${version}    1.1.0
    ${language}=    Config Value    display_language
    Should Be Equal    ${language}    en-US
    ${queued}=    Hardware Queue Size
    Should Be Equal As Integers    ${queued}    1
    Hardware Go Online
    ${sync}=    Hardware Sync
    Should Be Equal As Integers    ${sync}[synced]    1
    Assert Payment Count    ${sale}[idempotency_key]    1
