# 01 — Escopo e riscos

**Projeto:** POS QA Lab — Robot Framework + Python
**Responsável:** Emanuelle Gonçalves Paulino
**Data:** 19/11/2026
**Versão:** 0.4.0

## 1. Contexto

A vaga de QA Pleno para POS e Meios de Pagamento pede testes em terminais, periféricos, atualizações de
software, APIs REST, Linux/CLI, logs, automação com Robot Framework e Python, homologação e evidência.
Este laboratório foi criado para exercitar essas competências em um ambiente controlado e público, sem
usar dados internos ou alegar experiência que não existe.

## 2. Objetivo

Demonstrar, com código e evidência:

1. Automação com **Robot Framework + Python**, separando keywords de negócio de bibliotecas de integração.
2. Cobertura das **jornadas críticas de pagamento**: venda, recusa, cancelamento, estorno, parcelamento,
   timeout, offline e idempotência.
3. **Investigação e evidência**: banco, logs, `correlation_id`, relatório por caso e relatório de defeitos.
4. **Dispositivo Android**: instalação, atualização, login, carrinho e `logcat`.
5. **ISO 8583**: leitura de MTI, bitmap e campos, como laboratório de formato.

## 3. Escopo incluído

- API de adquirente simulada em FastAPI + SQLite.
- Terminal simulator com máquina de estados e fila offline.
- 37 casos de núcleo/ISO em Robot, incluindo 5 data-driven e 6 de fluxo ISO 8583.
- 5 casos de dispositivo implementados e executados em emulador Android.
- 39 testes unitários Python.
- Execução paralela com Pabot e listener de evidência JSONL.
- Dockerfile, Docker Compose, Makefile e scripts shell para execução em Linux.
- Runbook Linux com healthcheck, logs, troubleshooting e coleta de evidências.
- Runner que sobe e derruba a API automaticamente.
- Relatórios Robot (`output.xml`, `log.html`, `report.html`) e resumo em JSON.
- Documentação de escopo, plano, casos, matriz, execução, defeitos e limitações.

## 4. Fora de escopo

- POS físico, pinpad, impressora térmica e periféricos reais.
- EMV, certificação de bandeira, PCI PTS e ISO 8583 de produção.
- Conexão com adquirente, bandeira ou emissor.
- Teste de carga, segurança ofensiva ou acessibilidade.
- Dados reais de cartão, cliente ou empresa.

## 5. Premissas

- O ambiente de execução tem Python 3.11+ e acesso local à porta 8000.
- O device suite depende de Android SDK, emulador/dispositivo, Appium 2 e `UiAutomator2`.
- O app público usado é o **Sauce Labs My Demo App**; não há afiliação com a Stone.
- O repositório é público; nenhum APK, segredo ou dado interno é versionado.

## 6. Riscos

| Risco | Probabilidade | Impacto | Mitigação |
|---|---|---|---|
| Mock e testes se validarem sozinhos | Média | Alto | Casos negativos, banco, eventos e contract tests; mutation testing como evolução |
| Device suite não reproduzir offline/impressão de POS | Alta | Médio | Offline e reinício ficam no simulador; device cobre o que o app público permite |
| ISO 8583 superficial | Média | Médio | Documentar limite ASCII/BCD e usar apenas dados sintéticos |
| Ambiente sem emulador | Alta | Médio | Device suite fica separada e documentada; núcleo e ISO rodam em CI |
| Vazamento de dado interno | Baixa | Alto | Repositório público sem APK/dados da TIVIC; PAN sintético e mascarado |
| Escopo crescer | Média | Médio | Núcleo primeiro; device e ISO como extensões |

## 7. Critérios de sucesso

- 100% dos casos de núcleo e ISO verdes.
- Relatórios legíveis e reproduzíveis por uma pessoa externa.
- Matriz de rastreabilidade completa.
- Pelo menos um achado real de qualidade (defeito de infraestrutura ou produto) documentado com evidência.
- Limitações declaradas sem ambiguidade.
- Nenhum segredo ou dado sensível no repositório.

## 8. Decisões do projeto

- **2 semanas** de escopo, com núcleo executável primeiro.
- **App público** Sauce Labs My Demo App para device.
- **Repositório público** para portfólio.
- **ISO 8583** incluído como laboratório de formato.
- **Documentação em português**; código, keywords e nomes técnicos em inglês.
