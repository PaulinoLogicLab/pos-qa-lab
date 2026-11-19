import http from 'k6/http';
import { check, sleep } from 'k6';

export const options = {
  stages: [
    { duration: '2s', target: 5 },
    { duration: '5s', target: 10 },
    { duration: '2s', target: 0 },
  ],
  thresholds: {
    http_req_failed: ['rate<0.01'],
    http_req_duration: ['p(95)<500'],
  },
};

const BASE_URL = __ENV.BASE_URL || 'http://127.0.0.1:8000';

export default function () {
  const key = `perf-${__VU}-${__ITER}-${Date.now()}`;
  const amount = (10 + (__ITER % 90)).toFixed(2);
  const payload = JSON.stringify({
    amount: amount,
    currency: 'BRL',
    method: 'credit',
    installments: 1,
    entry_mode: 'chip',
    terminal_id: 'TERM-PERF-01',
    merchant_id: 'MERCH0001',
    card_token: 'tok_approved',
    capture: true,
  });
  const response = http.post(`${BASE_URL}/api/v1/payments`, payload, {
    headers: {
      'Content-Type': 'application/json',
      'Idempotency-Key': key,
    },
  });
  check(response, {
    'status is 201': (res) => res.status === 201,
    'payment captured': (res) => res.json('status') === 'CAPTURED',
  });
  sleep(0.1);
}

export function handleSummary(data) {
  const metrics = data.metrics;
  const failedRate = metrics.http_req_failed.values.rate;
  const p95 = metrics.http_req_duration.values['p(95)'];
  const summary = {
    requests: metrics.http_reqs.values.count,
    http_failed_rate: failedRate,
    p95_ms: p95,
    checks_passed: metrics.checks.values.passes,
    checks_failed: metrics.checks.values.fails,
    thresholds_passed: failedRate < 0.01 && p95 < 500,
  };
  return {
    '/reports/k6-summary.json': JSON.stringify(summary, null, 2) + '\n',
  };
}
