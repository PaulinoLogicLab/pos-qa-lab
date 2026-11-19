*** Settings ***
Documentation     Cancelamento, estorno total/parcial e transicoes invalidas.
Resource          ../resources/common.resource
Resource          ../resources/payment_keywords.resource
Suite Setup       Check Api Health
Test Tags         payment    regression

*** Test Cases ***
CT-PAY-03 Cancelamento antes da captura
    [Documentation]    Uma transacao autorizada pode ser cancelada; o status final deve ser CANCELLED.
    [Tags]    critical
    ${key}=    Generate Idempotency Key
    ${resp}=    Create Authorized Payment    amount=80.00    idempotency_key=${key}
    Assert Http Status    ${resp}    201
    Assert Payment Status    ${resp}    AUTHORIZED
    ${cancel}=    Cancel Payment    ${resp}[body][payment_id]
    Assert Http Status    ${cancel}    200
    Assert Payment Status    ${cancel}    CANCELLED
    ${row}=    Get Payment Row    ${resp}[body][payment_id]
    Should Be Equal    ${row}[status]    CANCELLED

CT-PAY-04 Estorno total e parcial apos captura
    [Documentation]    Estorna 50,00 e depois o restante; o valor estornado deve fechar o total.
    [Tags]    critical
    ${key}=    Generate Idempotency Key
    ${resp}=    Create Approved Payment    amount=125.90    idempotency_key=${key}
    Assert Http Status    ${resp}    201
    ${payment_id}=    Set Variable    ${resp}[body][payment_id]
    ${partial}=    Refund Payment    ${payment_id}    50.00
    Assert Http Status    ${partial}    200
    Assert Payment Status    ${partial}    PARTIALLY_REFUNDED
    Should Be Equal As Strings    ${partial}[body][refunded_amount]    50.00
    ${full}=    Refund Payment    ${payment_id}
    Assert Http Status    ${full}    200
    Assert Payment Status    ${full}    REFUNDED
    Should Be Equal As Strings    ${full}[body][refunded_amount]    125.90
    ${refunds}=    Database.Get Refunds    ${payment_id}
    Length Should Be    ${refunds}    2

CT-PAY-06 Transicoes invalidas sao rejeitadas
    [Documentation]    Estorno antes da captura e cancelamento depois da captura devem retornar 409.
    [Tags]    negative
    ${authorized}=    Create Authorized Payment    amount=45.00
    ${refund}=    Refund Payment    ${authorized}[body][payment_id]
    Assert Http Status    ${refund}    409
    Assert Error Code    ${refund}    INVALID_TRANSITION

    ${captured}=    Create Approved Payment    amount=45.00
    ${cancel}=    Cancel Payment    ${captured}[body][payment_id]
    Assert Http Status    ${cancel}    409
    Assert Error Code    ${cancel}    INVALID_TRANSITION
