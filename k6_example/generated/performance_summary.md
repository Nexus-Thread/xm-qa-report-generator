# Summary

| Service | Scenario | Duration | Load expected (rps) | Load actual (rps) | Error rate expected (%) | Error rate actual (%) | p95 expected (ms) | p95 actual (ms) | p99 expected (ms) | p99 actual (ms) | Outcome | Comment |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| THD | thdGetCandles | 15m | 500 | 499.89 | 10.0 | 0.0 | 200 | 156.8 | 300 | 196.8 | ✅ Passed | Throughput sustained; latency gates pass; no HTTP failures observed. |
| THD | thdGetOrders | 15m | 175 | 175.00 | 10.0 | 0.0 | 200 | 170.8 | 300 | 211.0 | ✅ Passed | Throughput sustained; latency gates pass; no HTTP failures observed. |
| THD | thdGetTradingHistory | 15m | 40 | 40.00 | 10.0 | 0.0 | 100 | 199.0 | 200 | 257.3 | ❌ Failed | Throughput sustained and reliable, but tail latency breaches p95/p99 thresholds. |
