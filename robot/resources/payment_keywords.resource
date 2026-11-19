*** Settings ***
Resource    common.resource

*** Keywords ***
Resolve Idempotency Key
    [Arguments]    ${idempotency_key}
    IF    '${idempotency_key}' == ''
        ${key}=    Generate Idempotency Key
        RETURN    ${key}
    END
    RETURN    ${idempotency_key}

Create Approved Payment
    [Arguments]    ${amount}=100.00    ${idempotency_key}=${EMPTY}    ${installments}=1    ${capture}=${TRUE}
    ${key}=    Resolve Idempotency Key    ${idempotency_key}
    ${resp}=    Create Payment
    ...    amount=${amount}
    ...    card_token=tok_approved
    ...    installments=${installments}
    ...    capture=${capture}
    ...    idempotency_key=${key}
    RETURN    ${resp}

Create Declined Payment
    [Arguments]    ${amount}=100.00    ${idempotency_key}=${EMPTY}
    ${key}=    Resolve Idempotency Key    ${idempotency_key}
    ${resp}=    Create Payment
    ...    amount=${amount}
    ...    card_token=tok_declined
    ...    idempotency_key=${key}
    RETURN    ${resp}

Create Timeout Payment
    [Arguments]    ${amount}=100.00    ${idempotency_key}=${EMPTY}
    ${key}=    Resolve Idempotency Key    ${idempotency_key}
    ${resp}=    Create Payment
    ...    amount=${amount}
    ...    card_token=tok_timeout
    ...    idempotency_key=${key}
    RETURN    ${resp}

Create Authorized Payment
    [Arguments]    ${amount}=100.00    ${idempotency_key}=${EMPTY}
    ${key}=    Resolve Idempotency Key    ${idempotency_key}
    ${resp}=    Create Payment
    ...    amount=${amount}
    ...    card_token=tok_approved
    ...    capture=${FALSE}
    ...    idempotency_key=${key}
    RETURN    ${resp}

Capture Authorized Payment
    [Arguments]    ${payment_id}    ${amount}=${EMPTY}
    IF    '${amount}' == ''
        ${resp}=    PaymentApi.Capture Payment    ${payment_id}
    ELSE
        ${resp}=    PaymentApi.Capture Payment    ${payment_id}    ${amount}
    END
    RETURN    ${resp}

Settle Terminal Batch
    [Arguments]    ${terminal_id}    ${idempotency_key}=${EMPTY}
    ${key}=    Resolve Idempotency Key    ${idempotency_key}
    ${resp}=    PaymentApi.Settle Terminal    ${terminal_id}    ${key}
    RETURN    ${resp}

Assert Captured Amount
    [Arguments]    ${resp}    ${expected}
    Should Be Equal As Strings    ${resp}[body][captured_amount]    ${expected}

Assert Settlement Net
    [Arguments]    ${resp}    ${expected}
    Should Be Equal As Strings    ${resp}[body][net_amount]    ${expected}
