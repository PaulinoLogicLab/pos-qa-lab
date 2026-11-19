*** Settings ***
Documentation     Smoke de dispositivo no Sauce Labs My Demo App.
...               Requer Appium 2 em 127.0.0.1:4723, emulador/dispositivo e RUN_DEVICE_TESTS=1.
Library           AppiumLibrary    run_on_failure=Capture Page Screenshot
Library           ../../libraries/Logcat.py    reports/logcat
Resource          ../resources/common.resource
Suite Setup       Require Device Environment
Test Setup        Open Test Application
Test Teardown     Handle Test Teardown
Test Tags         device

*** Variables ***
${APPIUM_URL}       http://127.0.0.1:4723
${APP_PACKAGE}      com.saucelabs.mydemoapp.android
${APP_ACTIVITY}     com.saucelabs.mydemoapp.android.view.activities.SplashActivity
${DEVICE_NAME}      emulator-5554
${VALID_USER}       bod@example.com
${VALID_PASSWORD}   10203040

*** Keywords ***
Require Device Environment
    ${enabled}=    Get Environment Variable    RUN_DEVICE_TESTS    ${EMPTY}
    Skip If    '${enabled}' != '1'    Device tests require RUN_DEVICE_TESTS=1 and Appium on 127.0.0.1:4723

Open Test Application
    Open Application
    ...    ${APPIUM_URL}
    ...    platformName=Android
    ...    automationName=UiAutomator2
    ...    deviceName=${DEVICE_NAME}
    ...    udid=${DEVICE_NAME}
    ...    appPackage=${APP_PACKAGE}
    ...    appActivity=${APP_ACTIVITY}
    ...    appWaitActivity=${APP_ACTIVITY}
    ...    noReset=${FALSE}
    ...    newCommandTimeout=120
    Wait Until Page Contains Element    id=${APP_PACKAGE}:id/menuIV    20s

Open Menu And Login
    Click Element    id=${APP_PACKAGE}:id/menuIV
    Wait Until Page Contains Element    id=${APP_PACKAGE}:id/menuRV    10s
    Swipe    start_x=540    start_y=1600    end_x=540    end_y=500
    Click Element    xpath=//*[@text='Log In']
    Wait Until Page Contains Element    id=${APP_PACKAGE}:id/loginBtn    10s

Login With Valid User
    Open Menu And Login
    Input Text    id=${APP_PACKAGE}:id/nameET    ${VALID_USER}
    Input Text    id=${APP_PACKAGE}:id/passwordET    ${VALID_PASSWORD}
    Click Element    id=${APP_PACKAGE}:id/loginBtn
    Wait Until Page Contains Element    id=${APP_PACKAGE}:id/menuIV    15s

Capture Logcat Evidence
    ${path}=    Capture Logcat    500    ${APP_PACKAGE}
    Log    Logcat salvo em ${path}

Handle Test Teardown
    Run Keyword If Test Failed    Capture Logcat Evidence
    Close Application

*** Test Cases ***
CT-DEV-01 Login valido com usuario do demo
    [Documentation]    Abre o menu, autentica e confirma o retorno a tela principal.
    [Tags]    smoke    critical
    Login With Valid User
    Page Should Contain Element    id=${APP_PACKAGE}:id/menuIV

CT-DEV-02 Login sem credenciais exibe validacao
    [Documentation]    O botao de login sem usuario deve exibir "Username is required".
    [Tags]    negative
    Open Menu And Login
    Click Element    id=${APP_PACKAGE}:id/loginBtn
    Wait Until Page Contains    Username is required    10s

CT-DEV-03 Usuario bloqueado exibe mensagem
    [Documentation]    O usuario alice@example.com e tratado como bloqueado pelo demo.
    [Tags]    negative
    Open Menu And Login
    Input Text    id=${APP_PACKAGE}:id/nameET    alice@example.com
    Input Text    id=${APP_PACKAGE}:id/passwordET    ${VALID_PASSWORD}
    Click Element    id=${APP_PACKAGE}:id/loginBtn
    Wait Until Page Contains    locked out    10s

CT-DEV-04 Adicionar produto ao carrinho
    [Documentation]    Login, abertura do primeiro produto, adicao ao carrinho e conferencia da tela.
    [Tags]    smoke
    Login With Valid User
    Wait Until Page Contains Element    id=${APP_PACKAGE}:id/productRV    15s
    Click Element    xpath=(//*[@resource-id='${APP_PACKAGE}:id/productIV'])[1]
    Wait Until Page Contains Element    id=${APP_PACKAGE}:id/cartBt    10s
    Click Element    id=${APP_PACKAGE}:id/cartBt
    Wait Until Page Contains Element    id=${APP_PACKAGE}:id/cartRL    10s
    Click Element    id=${APP_PACKAGE}:id/cartRL
    Wait Until Page Contains Element    id=${APP_PACKAGE}:id/totalPriceTV    10s
    Page Should Contain Element    id=${APP_PACKAGE}:id/totalPriceTV

CT-DEV-05 Background e foreground preservam a sessao
    [Documentation]    Coloca o app em background e retorna; a tela principal deve continuar acessivel.
    [Tags]    regression
    Login With Valid User
    Background Application    5
    Activate Application    ${APP_PACKAGE}
    Wait Until Page Contains Element    id=${APP_PACKAGE}:id/menuIV    15s
