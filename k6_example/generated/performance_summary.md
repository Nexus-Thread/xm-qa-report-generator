# Summary

| Service | Scenario | Duration | Target load (rps) | Achieved (steady-state, rps) | Outcome | Error rate | Latency metrics (ms) | Target threshold(s) | Comment |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| THD | thdGetCandles | 15m | 500 | 499.89 | ✅ Passed | 0.0% | avg=96.6ms, max=1792.8ms, med=89.3ms, min=46.8ms, p(95)=156.8ms, p(99)=196.8ms | http_req_duration: p95 < 200ms, p99 < 300ms; http_req_failed: rate < 10% | Throughput sustained; latency gates pass; no HTTP failures observed. |
| THD | thdGetOrders | 15m | 175 | 175.00 | ✅ Passed | 0.0% | avg=101.6ms, max=2744.7ms, med=90.1ms, min=46.8ms, p(95)=170.8ms, p(99)=211.0ms | http_req_duration: p95 < 200ms, p99 < 300ms; http_req_failed: rate < 10% | Throughput sustained; latency gates pass; no HTTP failures observed. |
| THD | thdGetTradingHistory | 15m | 40 | 40.00 | ❌ Failed | 0.0% | avg=120.9ms, max=2221.6ms, med=106.1ms, min=72.8ms, p(95)=199.0ms, p(99)=257.3ms | http_req_duration: p95 < 100ms, p99 < 200ms; http_req_failed: rate < 10% | Throughput sustained and reliable, but tail latency breaches p95/p99 thresholds. |
