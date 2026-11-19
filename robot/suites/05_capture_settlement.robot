*** Settings ***
Documentation     Pre-autorizacao, captura total/parcial e liquidacao por terminal.
Resource          ../resources/common.resource
Resource          ../resources/payment_keywords.resource
Suite Setup       Check Api Health
Test Tags         payment    settlement    regression

*** Test Cases ***
CT-CAP-01 Captura total de transacao autorizada
    [Documentation]    Autoriza 100,00 e captura o valor integral.
    [Tags]    critical
    ${key}=    Generate Idempotency Key
    ${auth}=    Create Payment
    ...    amount=100.00
    ...    capture=${FALSE}
    ...    idempotency_key=${key}
    Assert Http Status    ${auth}    201
    Assert Payment Status    ${auth}    AUTHORIZED
    ${capture}=    Capture Authorized Payment    ${auth}[body][payment_id]
    Assert Http Status    ${capture}    200
    Assert Payment Status    ${capture}    CAPTURED
    Assert Captured Amount    ${capture}    100.00

CT-CAP-02 Captura parcial e estorno do valor capturado
    [Documentation]    Captura 40,00 de 100,00; estorna 40,00; novo estorno deve falhar.
    [Tags]    critical
    ${key}=    Generate Idempotency Key
    ${auth}=    Create Payment
    ...    amount=100.00
    ...    capture=${FALSE}
    ...    idempotency_key=${key}
    ${payment_id}=    Set Variable    ${auth}[body][payment_id]
    ${capture}=    Capture Authorized Payment    ${payment_id}    40.00
    Assert Http Status    ${capture}    200
    Assert Payment Status    ${capture}    PARTIALLY_CAPTURED
    Assert Captured Amount    ${capture}    40.00
    ${refund}=    Refund Payment    ${payment_id}    40.00
    Assert Http Status    ${refund}    200
    Assert Payment Status    ${refund}    REFUNDED
    ${again}=    Refund Payment    ${payment_id}    10.00
    Assert Http Status    ${again}    409

CT-CAP-03 Captura duplicada e captura apos cancelamento
    [Documentation]    Mesmo valor e idempotente; valor diferente ou captura apos cancelamento retorna 409.
    [Tags]    negative
    ${key}=    Generate Idempotency Key
    ${auth}=    Create Payment
    ...    amount=80.00
    ...    capture=${FALSE}
    ...    idempotency_key=${key}
    ${payment_id}=    Set Variable    ${auth}[body][payment_id]
    ${first}=    Capture Authorized Payment    ${payment_id}
    ${second}=    Capture Authorized Payment    ${payment_id}
    Assert Http Status    ${first}    200
    Assert Http Status    ${second}    200
    ${different}=    Capture Authorized Payment    ${payment_id}    10.00
    Assert Http Status    ${different}    409

    ${cancel_key}=    Generate Idempotency Key
    ${cancelled}=    Create Payment
    ...    amount=30.00
    ...    capture=${FALSE}
    ...    idempotency_key=${cancel_key}
    Cancel Payment    ${cancelled}[body][payment_id]
    ${after_cancel}=    Capture Authorized Payment    ${cancelled}[body][payment_id]
    Assert Http Status    ${after_cancel}    409
    Assert Error Code    ${after_cancel}    INVALID_TRANSITION

CT-SET-01 Liquidacao calcula bruto, estorno e liquido
    [Documentation]    Duas vendas capturadas e um estorno de 20,00 geram bruto 150,00 e liquido 130,00.
    [Tags]    critical
    ${suffix}=    Evaluate    str(__import__('uuid').uuid4())[:8]
    ${terminal}=    Set Variable    TERM-SET-${suffix}
    ${first}=    Create Payment    amount=100.00    terminal_id=${terminal}
    ${second}=    Create Payment    amount=50.00    terminal_id=${terminal}
    Assert Http Status    ${first}    201
    Assert Http Status    ${second}    201
    ${refund}=    Refund Payment    ${second}[body][payment_id]    20.00
    Assert Http Status    ${refund}    200

    ${key}=    Generate Idempotency Key
    ${settle}=    Settle Terminal Batch    ${terminal}    ${key}
    Assert Http Status    ${settle}    201
    Should Be Equal    ${settle}[body][status]    SETTLED
    Should Be Equal As Integers    ${settle}[body][transaction_count]    2
    Should Be Equal As Strings    ${settle}[body][gross_amount]    150.00
    Should Be Equal As Strings    ${settle}[body][refunded_amount]    20.00
    Assert Settlement Net    ${settle}    130.00

    ${row}=    Database.Get Settlement    ${settle}[body][settlement_id]
    Should Not Be Equal    ${row}    ${None}
    ${items}=    Database.Get Settlement Items    ${settle}[body][settlement_id]
    Length Should Be    ${items}    2
    ${count}=    Database.Count Settlements By Idempotency    ${key}
    Should Be Equal As Integers    ${count}    1

CT-SET-02 Liquidacao e idempotente e lote vazio e controlado
    [Documentation]    Mesma chave devolve o mesmo fechamento; terminal sem transacoes gera lote EMPTY.
    [Tags]    critical
    ${suffix}=    Evaluate    str(__import__('uuid').uuid4())[:8]
    ${terminal}=    Set Variable    TERM-SET-${suffix}
    ${payment}=    Create Payment    amount=40.00    terminal_id=${terminal}
    ${key}=    Generate Idempotency Key
    ${first}=    Settle Terminal Batch    ${terminal}    ${key}
    ${second}=    Settle Terminal Batch    ${terminal}    ${key}
    Assert Http Status    ${first}    201
    Assert Http Status    ${second}    201
    Should Be Equal    ${first}[body][settlement_id]    ${second}[body][settlement_id]
    ${count}=    Database.Count Settlements By Idempotency    ${key}
    Should Be Equal As Integers    ${count}    1

    ${empty_key}=    Generate Idempotency Key
    ${empty}=    Settle Terminal Batch    ${terminal}    ${empty_key}
    Assert Http Status    ${empty}    201
    Should Be Equal    ${empty}[body][status]    EMPTY
    Should Be Equal As Integers    ${empty}[body][transaction_count]    0
    Assert Settlement Net    ${empty}    0.00

CT-SET-03 Chave de liquidacao nao pode ser usada em outro terminal
    [Documentation]    A mesma Idempotency-Key em terminal diferente retorna 409.
    [Tags]    negative
    ${suffix}=    Evaluate    str(__import__('uuid').uuid4())[:8]
    ${terminal_a}=    Set Variable    TERM-SETA-${suffix}
    ${terminal_b}=    Set Variable    TERM-SETB-${suffix}
    Create Payment    amount=15.00    terminal_id=${terminal_a}
    ${key}=    Generate Idempotency Key
    ${first}=    Settle Terminal Batch    ${terminal_a}    ${key}
    Assert Http Status    ${first}    201
    ${second}=    Settle Terminal Batch    ${terminal_b}    ${key}
    Assert Http Status    ${second}    409
    Assert Error Code    ${second}    IDEMPOTENCY_CONFLICT
