# 07 — Limitações

**Projeto:** POS QA Lab
**Data:** 19/11/2026

Este documento existe para evitar que o laboratório seja lido como algo que ele não é.

## 1. O que é simulado

- **Adquirente:** a API FastAPI é local e simulada. Não há conexão com adquirente, bandeira ou emissor
  real.
- **Terminal:** o `TerminalSimulator` é uma máquina de estados em Python + SQLite; não é firmware de POS.
- **Periféricos:** impressora, pinpad e ciclo do terminal são modelos determinísticos; não são drivers
  de hardware, ESC/POS, USB, serial ou Bluetooth.
- **Pagamento:** tokens (`tok_approved`, `tok_declined`, `tok_timeout`) substituem um gateway real.
- **ISO 8583:** parser/construtor didático em ASCII, com um subconjunto de campos. Não há BCD, MAC,
  rede, TLS ou certificação.
- **Captura/liquidação:** pré-autorização, captura parcial e fechamento são simulados em SQLite; não há
  clearing, settlement real ou conciliação com adquirente.
- **Concorrência/timeout:** a injeção de falhas usa atraso no servidor e cliente com timeout; não é uma
  rede instável real.

## 2. O que não foi testado

- Pinpad, chip, aproximação, tarja e certificação EMV.
- PCI PTS, certificação de bandeira ou homologação de adquirente.
- Impressora térmica, câmera, GPS e periféricos de POS.
- Atualização de firmware do terminal.
- Carga, estabilidade prolongada, segurança ofensiva e acessibilidade.
- A suíte de dispositivo foi executada em **emulador Android**, não em dispositivo físico ou POS real.
- O script de atualização de APK está implementado, mas ainda não foi executado.
- Liquidação real, clearing, certificação de bandeira e conciliação com adquirente.
- A liquidação é um snapshot: um estorno feito depois do fechamento não recalcula o lote.
- A captura parcial não libera automaticamente o saldo restante da autorização.
- O Pabot compartilha o banco entre workers; a massa é isolada por chave/terminal.
- O listener registra ciclo de vida e status, não request/response HTTP completos.
- O Compose é de laboratório; não há hardening de produção, TLS ou gestão de segredos.
- O k6 é um smoke de 10 VUs, não um SLA de produção.
- Mutation testing não foi executado; a cobertura de 88,9% não mede a qualidade das asserções.

## 3. O que o device suite cobre

O app público Sauce Labs My Demo App permite:

- instalação e atualização de APK;
- login válido, validação e usuário bloqueado;
- carrinho;
- background/foreground;
- coleta de `logcat`.

A suíte foi executada em emulador `Pixel_8_Pro` (Android 16 / API 36) com 5/5 aprovados.
Ela **não** permite testar impressão térmica, offline de POS ou periféricos. Esses temas ficam no
simulador de terminal e na experiência profissional da autora, não neste repositório.

## 4. O que o ISO 8583 cobre

- MTI;
- bitmap primário e secundário;
- campos 2, 3, 4, 7, 11, 12, 13, 37, 38, 39, 41, 42, 49 e 70;
- mensagens sintéticas e PAN mascarado;
- fluxo `0100/0110`, `0400/0410` e `0800/0810` em memória.

**Não cobre:** BCD, MAC, PIN block, TLS, socket, conexão com adquirente, certificação ou mensagens reais.

## 5. O que não pode ser afirmado

- “Testei POS real.”
- “Implementei ISO 8583 de produção.”
- “Fiz certificação EMV/PCI PTS.”
- “Validei impressão térmica neste projeto.”
- “O device suite passou em POS físico” — ele passou em emulador Android, não em POS real.

## 6. Evoluções possíveis

1. Rodar o device suite em dispositivo físico e o script de upgrade de APK.
2. Adicionar mutation testing no mock para medir a efetividade dos casos.
3. Adicionar property-based testing no parser ISO.
4. Adicionar k6 para carga e estabilidade.
5. Adicionar uma suíte de contrato com OpenAPI.
6. Adicionar impressão térmica apenas se houver hardware e app que permitam.
