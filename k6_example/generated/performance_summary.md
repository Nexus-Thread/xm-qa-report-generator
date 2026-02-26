# Summary

| Service | Scenario | Target load (rps) | Duration | Target threshold(s) | Achieved (steady-state) | Latency (med / p95 / p99 / max) | Error rate | Outcome | Comment |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| THD | thdGetCandles | 500 | 15m | p95 < 200ms, p99 < 300ms, http_req_failed < 10% | ~500 rps (449,905 iters / 900s) | 89ms / 157ms / 197ms / 1793ms | 0.0% | ✅ Passed | Throughput sustained; latency gates pass; no HTTP failures observed. |
| THD | thdGetOrders | 175 | 15m | p95 < 200ms, p99 < 300ms, http_req_failed < 10% | 175 rps (157,500 iters / 900s) | 90ms / 171ms / 211ms / 2745ms | 0.0% | ✅ Passed | Throughput sustained; latency gates pass; no HTTP failures observed. |
| THD | thdGetTradingHistory | 40 | 15m | p95 < 100ms, p99 < 200ms, http_req_failed < 10% | ~40 rps (36,001 iters / 900s) | 106ms / 199ms / 257ms / 2222ms | 0.0% | ❌ Failed | Throughput sustained and reliable, but tail latency breaches p95/p99 thresholds. |
