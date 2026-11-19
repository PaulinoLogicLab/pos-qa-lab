*** Settings ***
Documentation     Laboratorio de formato ISO 8583 com mensagens sinteticas.
...               Nao ha conexao com adquirente, BCD, MAC ou certificacao EMV/PCI.
Resource          ../resources/common.resource
Test Tags         lab    iso8583

*** Test Cases ***
CT-ISO-01 Parse de mensagem 0100
    [Documentation]    MTI, bitmap primario e campos fixos/LLVAR.
    &{fields}=    Create Dictionary
    ...    2=4111111111111111
    ...    3=000000
    ...    4=000000012590
    ...    7=1119183000
    ...    11=000123
    ...    12=183000
    ...    13=1119
    ...    41=TERM0001
    ...    42=MERCH0000000001
    ...    49=986
    ${message}=    Build Message    0100    ${fields}
    ${parsed}=    Parse Message    ${message}
    Should Be Equal    ${parsed}[mti]    0100
    Should Be Equal    ${parsed}[secondary_bitmap]    ${FALSE}
    ${parsed_fields}=    Set Variable    ${parsed}[fields]
    Should Be Equal    ${parsed_fields}[2]    4111111111111111
    Should Be Equal    ${parsed_fields}[4]    000000012590
    Should Be Equal    ${parsed_fields}[11]    000123
    Should Be Equal    ${parsed}[pan_masked]    411111******1111

CT-ISO-02 Parse de resposta 0110 com codigo 39
    [Documentation]    Mensagem de resposta com campo 39 = 00.
    &{fields}=    Create Dictionary
    ...    2=4111111111111111
    ...    3=000000
    ...    4=000000012590
    ...    7=1119183000
    ...    11=000123
    ...    39=00
    ...    41=TERM0001
    ...    42=MERCH0000000001
    ...    49=986
    ${message}=    Build Message    0110    ${fields}
    ${parsed}=    Parse Message    ${message}
    Should Be Equal    ${parsed}[mti]    0110
    ${parsed_fields}=    Set Variable    ${parsed}[fields]
    Should Be Equal    ${parsed_fields}[39]    00

CT-ISO-03 Bitmap secundario e campo 70
    [Documentation]    O bit 1 sinaliza bitmap secundario; o campo 70 deve ser lido.
    &{fields}=    Create Dictionary
    ...    2=4111111111111111
    ...    3=000000
    ...    4=000000000100
    ...    11=000124
    ...    70=301
    ${message}=    Build Message    0100    ${fields}
    ${parsed}=    Parse Message    ${message}
    Should Be Equal    ${parsed}[secondary_bitmap]    ${TRUE}
    ${parsed_fields}=    Set Variable    ${parsed}[fields]
    Should Be Equal    ${parsed_fields}[70]    301

CT-ISO-04 Mensagens invalidas sao rejeitadas
    [Documentation]    Bitmap incompleto e campo truncado devem gerar erro controlado.
    Run Keyword And Expect Error    *    Parse Message    0100
    &{fields}=    Create Dictionary
    ...    2=4111111111111111
    ...    3=000000
    ...    4=000000012590
    ...    11=000125
    ${message}=    Build Message    0100    ${fields}
    ${truncated}=    Get Substring    ${message}    0    -1
    Run Keyword And Expect Error    *    Parse Message    ${truncated}

CT-ISO-05 Round-trip build e parse
    [Documentation]    Construir e ler a mesma mensagem preserva todos os campos.
    &{fields}=    Create Dictionary
    ...    2=4111111111111111
    ...    3=000000
    ...    4=000000000100
    ...    7=1119183000
    ...    11=000126
    ...    12=183000
    ...    13=1119
    ...    41=TERM0001
    ...    42=MERCH0000000001
    ...    49=986
    ${message}=    Build Message    0100    ${fields}
    ${parsed}=    Parse Message    ${message}
    ${parsed_fields}=    Set Variable    ${parsed}[fields]
    Dictionaries Should Be Equal    ${parsed_fields}    ${fields}
