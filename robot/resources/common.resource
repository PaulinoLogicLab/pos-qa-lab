*** Settings ***
Library    ../../libraries/PaymentApi.py    http://127.0.0.1:8000
Library    ../../libraries/Database.py
Library    ../../libraries/Terminal.py    http://127.0.0.1:8000
Library    ../../libraries/Iso8583.py
Library    Collections
Library    String
Library    OperatingSystem
Library    Process

*** Variables ***
${API_URL}         http://127.0.0.1:8000
${TERMINAL_ID}     TERM0001
${MERCHANT_ID}     MERCH0001

*** Keywords ***
Check Api Health
    ${resp}=    Health
    Assert Http Status    ${resp}    200

Generate Idempotency Key
    ${key}=    Evaluate    str(__import__('uuid').uuid4())
    RETURN    ${key}

Assert Http Status
    [Arguments]    ${resp}    ${expected}
    Should Be Equal As Integers    ${resp}[status_code]    ${expected}

Assert Payment Status
    [Arguments]    ${resp}    ${expected}
    Should Be Equal    ${resp}[body][status]    ${expected}

Assert Response Code
    [Arguments]    ${resp}    ${expected}
    Should Be Equal As Strings    ${resp}[body][response_code]    ${expected}

Assert Error Code
    [Arguments]    ${resp}    ${expected}
    Should Be Equal    ${resp}[body][error][code]    ${expected}

Assert No Duplicate Payment
    [Arguments]    ${idempotency_key}
    ${count}=    Database.Count Payments By Idempotency    ${idempotency_key}
    Should Be Equal As Integers    ${count}    1

Get Payment Row
    [Arguments]    ${payment_id}
    ${row}=    Database.Get Payment    ${payment_id}
    Should Not Be Equal    ${row}    ${None}
    RETURN    ${row}
