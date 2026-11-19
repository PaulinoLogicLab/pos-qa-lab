*** Settings ***
Documentation     Fluxo ISO 8583 simulado: autorizacao, negacao, reversao e network management.
...               ASCII, dados sinteticos, sem BCD, MAC, rede real ou certificacao EMV/PCI.
Resource          ../resources/common.resource
Suite Setup       Check Api Health
Test Setup        Reset Acquirer
Test Tags         lab    iso8583    payment

*** Test Cases ***
CT-ISO-06 Autorizacao aprovada retorna 0110 com codigo 00
    [Documentation]    PAN sintetico terminado em 1111 e aprovado; campo 38 traz o approval code.
    [Tags]    critical
    &{fields}=    Create Dictionary
    ...    2=4111111111111111
    ...    3=000000
    ...    4=000000010000
    ...    7=1119183000
    ...    11=000123
    ...    12=183000
    ...    13=1119
    ...    41=TERM0001
    ...    42=MERCH0000000001
    ...    49=986
    ${message}=    Build Message    0100    ${fields}
    ${result}=    Process Message    ${message}
    Should Be Equal    ${result}[status]    APPROVED
    Should Be Equal    ${result}[parsed][mti]    0110
    ${response}=    Set Variable    ${result}[parsed][fields]
    Should Be Equal    ${response}[39]    00
    Should Be Equal    ${response}[38]    A12345
    Dictionary Should Contain Key    ${response}    37

CT-ISO-07 Autorizacao negada retorna 05 sem approval code
    [Documentation]    PAN sintetico terminado em 0002 simula recusa.
    [Tags]    negative
    &{fields}=    Create Dictionary
    ...    2=4000000000000002
    ...    3=000000
    ...    4=000000010000
    ...    7=1119183000
    ...    11=000124
    ...    12=183000
    ...    13=1119
    ...    41=TERM0001
    ...    42=MERCH0000000001
    ...    49=986
    ${message}=    Build Message    0100    ${fields}
    ${result}=    Process Message    ${message}
    Should Be Equal    ${result}[status]    DECLINED
    ${response}=    Set Variable    ${result}[parsed][fields]
    Should Be Equal    ${response}[39]    05
    Dictionary Should Not Contain Key    ${response}    38

CT-ISO-08 Duplicidade de STAN nao cria segunda transacao
    [Documentation]    A mesma mensagem 0100 devolve a mesma 0110 e mantem uma transacao.
    [Tags]    critical
    &{fields}=    Create Dictionary
    ...    2=4111111111111111
    ...    3=000000
    ...    4=000000010000
    ...    7=1119183000
    ...    11=000125
    ...    12=183000
    ...    13=1119
    ...    41=TERM0001
    ...    42=MERCH0000000001
    ...    49=986
    ${message}=    Build Message    0100    ${fields}
    ${first}=    Process Message    ${message}
    ${second}=    Process Message    ${message}
    Should Be Equal    ${first}[response]    ${second}[response]
    Should Be Equal    ${second}[duplicate]    ${TRUE}
    ${count}=    Transaction Count
    Should Be Equal As Integers    ${count}    1

CT-ISO-09 Reversao 0400 retorna 0410 e e idempotente
    [Documentation]    A primeira reversao retorna 00; a segunda e marcada como ja revertida.
    [Tags]    critical
    &{auth_fields}=    Create Dictionary
    ...    2=4111111111111111
    ...    3=000000
    ...    4=000000010000
    ...    7=1119183000
    ...    11=000126
    ...    12=183000
    ...    13=1119
    ...    41=TERM0001
    ...    42=MERCH0000000001
    ...    49=986
    ${auth}=    Build Message    0100    ${auth_fields}
    Process Message    ${auth}
    ${reversal}=    Build Message    0400    ${auth_fields}
    ${first}=    Process Message    ${reversal}
    ${second}=    Process Message    ${reversal}
    Should Be Equal    ${first}[status]    REVERSED
    Should Be Equal    ${first}[parsed][mti]    0410
    Should Be Equal    ${first}[parsed][fields][39]    00
    Should Be Equal    ${second}[status]    ALREADY_REVERSED

CT-ISO-10 Network management 0800 retorna 0810
    [Documentation]    Eco de rede com campo 70 e codigo 00.
    [Tags]    smoke
    &{fields}=    Create Dictionary
    ...    7=1119183000
    ...    11=000900
    ...    70=301
    ${message}=    Build Message    0800    ${fields}
    ${result}=    Process Message    ${message}
    Should Be Equal    ${result}[status]    NETWORK_OK
    Should Be Equal    ${result}[parsed][mti]    0810
    Should Be Equal    ${result}[parsed][fields][39]    00

CT-ISO-11 MTI nao suportado gera erro controlado
    [Documentation]    Apenas 0100, 0400 e 0800 sao aceitos neste laboratorio.
    [Tags]    negative
    &{fields}=    Create Dictionary
    ...    11=000901
    ${message}=    Build Message    0200    ${fields}
    Run Keyword And Expect Error    *not supported*    Process Message    ${message}
