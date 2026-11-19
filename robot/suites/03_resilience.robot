*** Settings ***
Documentation     Idempotencia, timeout, fila offline e recuperacao apos reinicio.
Resource          ../resources/common.resource
Resource          ../resources/payment_keywords.resource
Suite Setup       Check Api Health
Test Tags         resilience    regression

*** Test Cases ***
CT-RES-01 Repeticao com a mesma chave nao cobra duas vezes
    [Documentation]    A segunda chamada deve devolver o mesmo payment_id e manter uma unica linha no banco.
    [Tags]    critical
    ${key}=    Generate Idempotency Key
    ${first}=    Create Approved Payment    amount=10.00    idempotency_key=${key}
    ${second}=    Create Approved Payment    amount=10.00    idempotency_key=${key}
    Assert Http Status    ${first}    201
    Assert Http Status    ${second}    201
    Should Be Equal    ${first}[body][payment_id]    ${second}[body][payment_id]
    Assert No Duplicate Payment    ${key}

CT-RES-02 Timeout seguido de retry nao duplica a transacao
    [Documentation]    O timeout e persistido com codigo 91; o retry com a mesma chave devolve o mesmo pagamento.
    [Tags]    critical
    ${key}=    Generate Idempotency Key
    ${first}=    Create Timeout Payment    amount=15.00    idempotency_key=${key}
    Assert Http Status    ${first}    504
    Assert Payment Status    ${first}    FAILED
    Assert Response Code    ${first}    91
    ${second}=    Create Timeout Payment    amount=15.00    idempotency_key=${key}
    Assert Http Status    ${second}    504
    Should Be Equal    ${first}[body][payment_id]    ${second}[body][payment_id]
    Assert No Duplicate Payment    ${key}

CT-RES-03 Fila offline sincroniza quando a conexao volta
    [Documentation]    A venda fica na fila local; o sync cria a transacao e uma segunda sincronizacao nao duplica.
    [Tags]    critical
    ${key}=    Generate Idempotency Key
    ${db}=    Join Path    ${TEMPDIR}    terminal_${key}.db
    Use Terminal    TERM9101    ${db}
    Go Offline
    ${sale}=    Start Sale    25.00    idempotency_key=${key}
    Should Be Equal    ${sale}[status]    QUEUED_OFFLINE
    ${queued}=    Queue Size
    Should Be Equal As Integers    ${queued}    1

    Go Online
    ${sync}=    Sync
    Should Be Equal As Integers    ${sync}[synced]    1
    Should Be Equal As Integers    ${sync}[queue_size]    0
    ${result}=    Get From List    ${sync}[results]    0
    Assert Http Status    ${result}    201
    Assert Payment Status    ${result}    CAPTURED
    Assert No Duplicate Payment    ${key}

    ${sync_again}=    Sync
    Should Be Equal As Integers    ${sync_again}[synced]    0

CT-RES-04 Reinicio do terminal preserva a fila offline
    [Documentation]    A fila sobrevive ao reinicio do simulador; o sync seguinte conclui a venda.
    [Tags]    critical
    ${key}=    Generate Idempotency Key
    ${db}=    Join Path    ${TEMPDIR}    terminal_${key}.db
    Use Terminal    TERM9102    ${db}
    Go Offline
    ${sale}=    Start Sale    30.00    idempotency_key=${key}
    Should Be Equal    ${sale}[status]    QUEUED_OFFLINE
    ${state}=    Restart
    Should Be Equal As Integers    ${state}[queue_size]    1
    ${sync}=    Sync
    Should Be Equal As Integers    ${sync}[synced]    1
    ${result}=    Get From List    ${sync}[results]    0
    Assert Payment Status    ${result}    CAPTURED
    Assert No Duplicate Payment    ${key}
