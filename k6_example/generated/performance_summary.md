# Summary

| Service | Scenario | Executor | Time unit | VUs (pre/max) | Observed VUs (cur/peak) | Duration | Load expected (rps) | Load actual (rps) | Error rate expected (%) | Error rate actual (%) | p95 expected (ms) | p95 actual (ms) | p99 expected (ms) | p99 actual (ms) | Outcome | Comment |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| THD | thdGetCandles | constant-arrival-rate | 1s | 100/1000 | 46/136 | 15m | 500 | 499.89 | 10.0 | 0.0 | 200 | 156.8 | 300 | 196.8 | ✅ Passed | Throughput sustained; latency gates pass; no HTTP failures observed. |
| THD | thdGetOrders | constant-arrival-rate | 1s | 100/1000 | 16/29 | 15m | 175 | 175.00 | 10.0 | 0.0 | 200 | 170.8 | 300 | 211.0 | ✅ Passed | Throughput sustained; latency gates pass; no HTTP failures observed. |
| THD | thdGetTradingHistory | constant-arrival-rate | 1s | 100/1000 | 6/11 | 15m | 40 | 40.00 | 10.0 | 0.0 | 100 | 199.0 | 200 | 257.3 | ❌ Failed | Throughput sustained and reliable, but tail latency breaches p95/p99 thresholds. |

## Scenario & Load Model

| Scenario | Executor | Time unit | VUs (pre/max) | Observed VUs (cur/peak) | Duration | Target load (rps) |
| --- | --- | --- | --- | --- | --- | --- |
| thdGetCandles | constant-arrival-rate | 1s | 100/1000 | 46/136 | 15m | 500 |
| thdGetOrders | constant-arrival-rate | 1s | 100/1000 | 16/29 | 15m | 175 |
| thdGetTradingHistory | constant-arrival-rate | 1s | 100/1000 | 6/11 | 15m | 40 |

## Performance Results

### thdGetCandles

#### 4.1 Throughput & stability
- Total requests: 450005
- Achieved rate: ~499.89 rps
- Dropped iterations: 96
- Interpretation: *[LLM placeholder — to be generated later]*

#### 4.2 Errors
- HTTP failure rate: 0.0%
- Checks: 450005 passes, 0 fails
- Interpretation: *[LLM placeholder — to be generated later]*

#### 4.3 Latency
- thdGetCandles (http_req_duration{test_name:thdGetCandles})
  - min 46.8ms
  - med 89.3ms
  - avg 96.6ms
  - p95 156.8ms → PASSED (threshold 200ms)
  - p99 196.8ms → PASSED (threshold 300ms)
  - max 1792.8ms

- Where time is spent:
  - http_req_waiting med 89.0ms, p95 156.6ms, p99 197.2ms, max 1792.1ms
  - Connect/TLS med 0/0ms, p95 0/0ms, p99 0/0ms
- Interpretation: *[LLM placeholder — to be generated later]*

### thdGetOrders

#### 4.1 Throughput & stability
- Total requests: 157600
- Achieved rate: ~175.00 rps
- Dropped iterations: N/A
- Interpretation: *[LLM placeholder — to be generated later]*

#### 4.2 Errors
- HTTP failure rate: 0.0%
- Checks: 157600 passes, 0 fails
- Interpretation: *[LLM placeholder — to be generated later]*

#### 4.3 Latency
- thdGetOrders (http_req_duration{test_name:thdGetOrders})
  - min 46.8ms
  - med 90.1ms
  - avg 101.6ms
  - p95 170.8ms → PASSED (threshold 200ms)
  - p99 211.0ms → PASSED (threshold 300ms)
  - max 2744.7ms

- Where time is spent:
  - http_req_waiting med 89.9ms, p95 170.8ms, p99 212.9ms, max 2744.5ms
  - Connect/TLS med 0/0ms, p95 0/0ms, p99 0/0ms
- Interpretation: *[LLM placeholder — to be generated later]*

### thdGetTradingHistory

#### 4.1 Throughput & stability
- Total requests: 36101
- Achieved rate: ~40.00 rps
- Dropped iterations: N/A
- Interpretation: *[LLM placeholder — to be generated later]*

#### 4.2 Errors
- HTTP failure rate: 0.0%
- Checks: 36101 passes, 0 fails
- Interpretation: *[LLM placeholder — to be generated later]*

#### 4.3 Latency
- thdGetTradingHistory (http_req_duration{test_name:thdGetTradingHistory})
  - min 72.8ms
  - med 106.1ms
  - avg 120.9ms
  - p95 199.0ms → FAILED (threshold 100ms)
  - p99 257.3ms → FAILED (threshold 200ms)
  - max 2221.6ms

- Where time is spent:
  - http_req_waiting med 104.7ms, p95 192.4ms, p99 254.0ms, max 2209.4ms
  - Connect/TLS med 0/0ms, p95 0/0ms, p99 0/0ms
- Interpretation: *[LLM placeholder — to be generated later]*
