*** Settings ***
Documentation     Concorrencia de idempotencia e timeout com retry.
Resource          ../resources/common.resource
Resource          ../resources/payment_keywords.resource
Suite Setup       Check Api Health
Test Tags         resilience    concurrency    regression

*** Test Cases ***
CT-RES-05 Dez requisicoes simultaneas geram uma unica cobranca
    [Documentation]    A mesma Idempotency-Key disparada em paralelo deve retornar um unico payment_id.
    [Tags]    critical
    ${key}=    Generate Idempotency Key
    ${results}=    Create Payments Concurrently    10.00    ${key}    10
    ${ids}=    Create List
    FOR    ${result}    IN    @{results}
        Assert Http Status    ${result}    201
        ${payment_id}=    Set Variable    ${result}[body][payment_id]
        Append To List    ${ids}    ${payment_id}
    END
    ${unique}=    Remove Duplicates    ${ids}
    Length Should Be    ${unique}    1
    Assert No Duplicate Payment    ${key}

CT-RES-06 Timeout no cliente seguido de retry nao duplica
    [Documentation]    A API demora 1,5 s; o cliente desiste em 0,5 s; o retry recupera a mesma transacao.
    [Tags]    critical
    ${key}=    Generate Idempotency Key
    ${timeout}=    Create Payment
    ...    amount=25.00
    ...    terminal_id=TERM-SLOW-01
    ...    idempotency_key=${key}
    ...    simulate_delay_ms=1500
    ...    request_timeout=0.5
    Should Be True    ${timeout}[timeout]
    Sleep    2s
    ${retry}=    Create Payment
    ...    amount=25.00
    ...    terminal_id=TERM-SLOW-01
    ...    idempotency_key=${key}
    ...    simulate_delay_ms=1500
    Assert Http Status    ${retry}    201
    Assert Payment Status    ${retry}    CAPTURED
    Assert No Duplicate Payment    ${key}
