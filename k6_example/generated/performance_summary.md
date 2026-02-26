# Summary

| Service | Scenario | Target load (rps) | Duration | Target threshold(s) | Achieved (steady-state) | Latency metrics (ms) | Error rate | Outcome | Comment |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| THD | thdGetCandles | 500 | 15m | http_req_duration: p95 < 200ms, p99 < 300ms; http_req_failed: rate < 10% | ~500 rps (449,905 iters / 900s) | avg=96.6ms, max=1792.8ms, med=89.3ms, min=46.8ms, p(95)=156.8ms, p(99)=196.8ms | 0.0% | ✅ Passed | Throughput sustained; latency gates pass; no HTTP failures observed. |
| THD | thdGetOrders | 175 | 15m | http_req_duration: p95 < 200ms, p99 < 300ms; http_req_failed: rate < 10% | 175 rps (157,500 iters / 900s) | avg=101.6ms, max=2744.7ms, med=90.1ms, min=46.8ms, p(95)=170.8ms, p(99)=211.0ms | 0.0% | ✅ Passed | Throughput sustained; latency gates pass; no HTTP failures observed. |
| THD | thdGetTradingHistory | 40 | 15m | http_req_duration: p95 < 100ms, p99 < 200ms; http_req_failed: rate < 10% | ~40 rps (36,001 iters / 900s) | avg=120.9ms, max=2221.6ms, med=106.1ms, min=72.8ms, p(95)=199.0ms, p(99)=257.3ms | 0.0% | ❌ Failed | Throughput sustained and reliable, but tail latency breaches p95/p99 thresholds. |
