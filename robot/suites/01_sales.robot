*** Settings ***
Documentation     Jornada de venda: aprovacao, recusa e parcelamento.
Resource          ../resources/common.resource
Resource          ../resources/payment_keywords.resource
Suite Setup       Check Api Health
Test Tags         smoke    payment

*** Test Cases ***
CT-PAY-01 Venda aprovada com chave de idempotencia
    [Documentation]    Cria uma venda aprovada, valida o contrato e confirma a persistencia.
    [Tags]    critical
    ${key}=    Generate Idempotency Key
    ${resp}=    Create Approved Payment    amount=125.90    idempotency_key=${key}
    Assert Http Status    ${resp}    201
    Assert Payment Status    ${resp}    CAPTURED
    Assert Response Code    ${resp}    00
    Should Be Equal As Strings    ${resp}[body][amount]    125.90
    ${row}=    Get Payment Row    ${resp}[body][payment_id]
    Should Be Equal    ${row}[status]    CAPTURED
    Should Be Equal As Strings    ${row}[amount_cents]    12590
    Assert No Duplicate Payment    ${key}

CT-PAY-02 Venda negada com codigo de resposta
    [Documentation]    A recusa nao deve capturar a transacao e deve retornar o codigo 05.
    [Tags]    negative
    ${key}=    Generate Idempotency Key
    ${resp}=    Create Declined Payment    amount=89.90    idempotency_key=${key}
    Assert Http Status    ${resp}    201
    Assert Payment Status    ${resp}    DECLINED
    Assert Response Code    ${resp}    05
    ${row}=    Get Payment Row    ${resp}[body][payment_id]
    Should Be Equal    ${row}[status]    DECLINED

CT-PAY-05 Parcelamento em tres vezes com arredondamento
    [Documentation]    O total deve ser preservado e a diferenca de centavos vai para as primeiras parcelas.
    ${key}=    Generate Idempotency Key
    ${resp}=    Create Approved Payment    amount=100.00    installments=3    idempotency_key=${key}
    Assert Http Status    ${resp}    201
    ${plan}=    Set Variable    ${resp}[body][installment_plan]
    Length Should Be    ${plan}    3
    ${first}=    Get From List    ${plan}    0
    ${second}=    Get From List    ${plan}    1
    ${third}=    Get From List    ${plan}    2
    Should Be Equal As Strings    ${first}[amount]    33.34
    Should Be Equal As Strings    ${second}[amount]    33.33
    Should Be Equal As Strings    ${third}[amount]    33.33
