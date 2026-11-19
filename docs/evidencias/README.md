# Evidências de execução — 19/11/2026

## Núcleo + ISO 8583

- **Comando:** `python scripts/run_suite.py --exclude device`
- **Resultado:** 44/44 aprovados, 0 falhas, 3,89 s
- **Cobertura:** venda, cancelamento/estorno, captura, liquidação, resiliência, concorrência,
  contratos, data-driven, hardware simulado e ISO 8583 (parser e fluxo).
- **Paralelo:** 44/44 em 4 processos Pabot (tempo de parede 8,00 s).
- **Resumo:** [core-2026-11-19/summary.json](core-2026-11-19/summary.json)
- **Pabot:** [pabot-2026-11-19/summary.json](pabot-2026-11-19/summary.json)
- **Relatórios completos:** gerados localmente em `reports/robot/` e `reports/pabot/`, publicados
  como artifact no GitHub Actions (`robot-core`).

## Device — Sauce Labs My Demo App

- **Comando:** `RUN_DEVICE_TESTS=1 python scripts/run_suite.py --device --no-api --outputdir reports/device_run`
- **Resultado:** 5/5 aprovados, 0 falhas, 104,69 s
- **Ambiente:** emulador `Pixel_8_Pro` (`sdk_gphone64_x86_64`), Android 16 / API 36, x86_64,
  My Demo App 2.3.0, Appium 3.5.0 e UiAutomator2 7.0.0.
- **Resumo:** [device-2026-11-19/summary.json](device-2026-11-19/summary.json)
- **Relatórios completos:** gerados localmente em `reports/device_run/`.
  Não são versionados porque contêm o log detalhado da automação e credenciais públicas do app de
  demonstração; o `summary.json` preserva o resultado por caso.

## Observação

O device suite foi executado em emulador, não em POS físico. O script de atualização de APK
(`scripts/device_upgrade_check.py`) está implementado, mas ainda não foi executado.
