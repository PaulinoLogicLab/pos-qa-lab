*** Settings ***
Documentation     Teste data-driven de vendas: valores, parcelas, recusa e limites.
...               As linhas chamam a keyword de negocio Create And Assert Sale.
Library           ../../libraries/SalesWorkflow.py
Resource          ../resources/common.resource
Suite Setup       Check Api Health
Test Template     Create And Assert Sale
Test Tags         data_driven    payment    regression

*** Test Cases ***
CT-DD-01 Venda aprovada de 10,00 em 1x
    CT-DD-01    10.00    1    tok_approved    CAPTURED    00    1

CT-DD-02 Venda aprovada de 100,00 em 3x
    CT-DD-02    100.00    3    tok_approved    CAPTURED    00    3

CT-DD-03 Venda negada de 89,90
    CT-DD-03    89.90    1    tok_declined    DECLINED    05    1

CT-DD-04 Venda aprovada no limite minimo de 0,01
    CT-DD-04    0.01    1    tok_approved    CAPTURED    00    1

CT-DD-05 Venda alta de 999.999,99 em 12x
    CT-DD-05    999999.99    12    tok_approved    CAPTURED    00    12
