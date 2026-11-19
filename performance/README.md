# Performance lab

`payment_load.js` roda um smoke de carga com k6 contra a API simulada.

```bash
docker compose up -d api
docker compose --profile perf run --rm k6
```

Ou:

```bash
make perf
```

Thresholds atuais:

- `http_req_failed < 1%`
- `http_req_duration p(95) < 500 ms`

O cenário sobe de 0 para 10 VUs, mantém por 5 s e desce. O resumo é salvo em
`reports/k6-summary.json`. Os thresholds são um smoke de laboratório, não um SLA de produção.
