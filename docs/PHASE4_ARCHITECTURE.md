# Phase 4 Portfolio-Risk Architecture

## Connected research boundary

The Phase 4 application service accepts an authenticated Phase 3 publication identifier. It authenticates that publication, authenticates the exact Phase 2 parent named by Phase 3, and verifies the parent-manifest hash connection. Portfolio returns, benchmark returns, and the aligned risk-free series are then read from checksum-bound Phase 2 artifacts. The service does not accept caller-injected return frames.

```text
connected authenticated Phase 2 + Phase 3 evidence
  -> exact return/benchmark/risk-free alignment
  -> past-only estimation window
  -> covariance + constraints + allocation/optimizer
  -> execution costs + self-financing weight drift
  -> gross/net/benchmark accounting and risk analytics
  -> immutable tables/reports
  -> manifest + publication pointer + authenticated reads
```

## Packages

| Package | Responsibility |
|---|---|
| `portfolio` | Configuration, transparent allocations, connected orchestration |
| `optimization` | Covariance, Black-Litterman/Bayesian inputs, HRP and constrained optimizers |
| `constraints` | Approved-baseline feasibility and post-solution verification |
| `risk` | Volatility, beta/alpha, drawdown, relative, tail, and contribution metrics |
| `scenarios` | Explicit instantaneous non-forecasting shock propagation |
| `backtest` | Past-only rolling/expanding scheduling, trades, costs, weight drift |
| `performance` | Reconciled gross/net/benchmark summaries |
| `research_outputs` | Exact artifact inventory, schemas, checksums, lineage, read authentication |

Optimization, risk, and scenario primitives are independently testable. Only the application service creates institutional Phase 4 publications. Machine learning, API, dashboard, deployment, and forecasting remain absent.

## Failure and recovery

Invalid covariance, infeasible bounds, convergence failure, misaligned assets, missing risk-free data, benchmark conflicts, unavailable constraint metadata, unspecified cost decisions, accounting mismatch, path escape, schema substitution, content mutation, and lineage mismatch fail explicitly. Sector/exposure constraints cannot be configured through the service until authenticated metadata is supplied. Artifact bytes may exist after an interrupted pre-activation run, but they remain unlisted and unreadable through the supported repository until atomic evidence activation. Same-identity content conflicts are refused.
