# 07 — Limitações

**Projeto:** POS QA Lab
**Data:** 19/11/2026

Este documento existe para evitar que o laboratório seja lido como algo que ele não é.

## 1. O que é simulado

- **Adquirente:** a API FastAPI é local e simulada. Não há conexão com Stone, Cielo, Rede, Getnet ou
  qualquer adquirente real.
- **Terminal:** o `TerminalSimulator` é uma máquina de estados em Python + SQLite; não é firmware de POS.
- **Pagamento:** tokens (`tok_approved`, `tok_declined`, `tok_timeout`) substituem um gateway real.
- **ISO 8583:** parser/construtor didático em ASCII, com um subconjunto de campos. Não há BCD, MAC,
  rede, TLS ou certificação.

## 2. O que não foi testado

- Pinpad, chip, aproximação, tarja e certificação EMV.
- PCI PTS, certificação de bandeira ou homologação de adquirente.
- Impressora térmica, câmera, GPS e periféricos de POS.
- Atualização de firmware do terminal.
- Carga, estabilidade prolongada, segurança ofensiva e acessibilidade.
- A suíte de dispositivo **não foi executada** neste ambiente; ela está implementada e depende de
  Android/Appium.

## 3. O que o device suite cobre

O app público Sauce Labs My Demo App permite:

- instalação e atualização de APK;
- login válido, validação e usuário bloqueado;
- carrinho;
- background/foreground;
- coleta de `logcat`.

Ele **não** permite testar impressão térmica, offline de POS ou periféricos. Esses temas ficam no
simulador de terminal e na experiência profissional da autora, não neste repositório.

## 4. O que o ISO 8583 cobre

- MTI;
- bitmap primário e secundário;
- campos 2, 3, 4, 7, 11, 12, 13, 39, 41, 42, 49 e 70;
- mensagens sintéticas e PAN mascarado.

**Não cobre:** BCD, MAC, PIN block, TLS, conexão com adquirente, certificação ou mensagens reais.

## 5. O que não pode ser afirmado

- “Testei POS real.”
- “Implementei ISO 8583 de produção.”
- “Fiz certificação EMV/PCI PTS.”
- “Validei impressão térmica neste projeto.”
- “O device suite passou” — ele ainda não foi executado.

## 6. Evoluções possíveis

1. Rodar o device suite em emulador e anexar evidências.
2. Adicionar mutation testing no mock para medir a efetividade dos casos.
3. Adicionar property-based testing no parser ISO.
4. Adicionar k6 para carga e estabilidade.
5. Adicionar uma suíte de contrato com OpenAPI.
6. Adicionar impressão térmica apenas se houver hardware e app que permitam.
