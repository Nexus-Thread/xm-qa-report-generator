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
