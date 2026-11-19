*** Settings ***
Documentation     Contratos de erro, validacao de entrada e correlacao.
Resource          ../resources/common.resource
Resource          ../resources/payment_keywords.resource
Suite Setup       Check Api Health
Test Tags         contract    regression

*** Test Cases ***
CT-CON-01 Contrato rejeita payload e cabecalhos invalidos
    [Documentation]    Sem Idempotency-Key, valor negativo, moeda invalida e parcelas invalidas devem retornar 422.
    [Tags]    negative
    ${payload}=    Create Dictionary
    ...    amount=10.00
    ...    terminal_id=TERM0001
    ...    merchant_id=MERCH0001
    ${without_key}=    Create Payment Without Key    ${payload}
    Assert Http Status    ${without_key}    422
    Assert Error Code    ${without_key}    VALIDATION_ERROR

    ${negative}=    Create Payment    amount=-1.00
    Assert Http Status    ${negative}    422
    Assert Error Code    ${negative}    VALIDATION_ERROR

    ${currency}=    Create Payment    amount=10.00    currency=USD
    Assert Http Status    ${currency}    422
    Assert Error Code    ${currency}    UNSUPPORTED_CURRENCY

    ${installments}=    Create Payment    amount=10.00    installments=0
    Assert Http Status    ${installments}    422
    Assert Error Code    ${installments}    VALIDATION_ERROR

CT-OBS-01 Correlation ID aparece na resposta, no banco e no evento
    [Documentation]    O mesmo correlation_id deve atravessar API, persistencia e trilha de evento.
    ${key}=    Generate Idempotency Key
    ${correlation}=    Set Variable    corr-lab-${key}
    ${resp}=    Create Payment
    ...    amount=12.00
    ...    idempotency_key=${key}
    ...    correlation_id=${correlation}
    Assert Http Status    ${resp}    201
    Should Be Equal    ${resp}[correlation_id]    ${correlation}
    ${row}=    Get Payment Row    ${resp}[body][payment_id]
    Should Be Equal    ${row}[correlation_id]    ${correlation}
    ${events}=    Database.Get Events    ${resp}[body][payment_id]
    ${first_event}=    Get From List    ${events}    0
    Should Be Equal    ${first_event}[correlation_id]    ${correlation}

CT-CON-02 Sync rejeita transacao de outro terminal
    [Documentation]    O terminal do payload deve coincidir com o terminal da rota; nao pode criar pagamento.
    [Tags]    negative
    ${key}=    Generate Idempotency Key
    &{transaction}=    Create Dictionary
    ...    amount=10.00
    ...    terminal_id=TERM9999
    ...    merchant_id=MERCH0001
    ...    idempotency_key=${key}
    @{transactions}=    Create List    ${transaction}
    ${resp}=    Sync Terminal    TERM0001    ${transactions}
    Assert Http Status    ${resp}    200
    ${result}=    Get From List    ${resp}[body][results]    0
    Should Be Equal As Integers    ${result}[status_code]    422
    Should Be Equal    ${result}[error][code]    TERMINAL_MISMATCH
    Assert No Payment With Key    ${key}

*** Keywords ***
Assert No Payment With Key
    [Arguments]    ${idempotency_key}
    ${count}=    Database.Count Payments By Idempotency    ${idempotency_key}
    Should Be Equal As Integers    ${count}    0
