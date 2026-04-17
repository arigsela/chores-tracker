# Implementation Plan — OpenTelemetry Tracing for `chores-tracker-backend` → Coroot

**Ticket / Initiative:** Add OTLP tracing to chores-tracker-backend and ship spans to Coroot
**Owner:** Ari Sela
**Created:** 2026-04-17
**Last Updated:** 2026-04-17
**Current Status:** Phase 2 code changes complete — image build/push pending (user-handled)

---

## 1. Overview

Add OpenTelemetry instrumentation to the FastAPI-based `chores-tracker-backend` app so distributed traces (function-level spans, DB calls, HTTP requests) are exported via OTLP to the in-cluster Coroot instance. This complements the existing:

- Coroot eBPF tracer (network-level, automatic)
- Waypoint Envoy L7 metrics (edge-level)
- `/metrics` Prometheus endpoint (app-level counters)

…by adding **app-level spans with function names, attributes, and exception context** that eBPF cannot infer.

### Success criteria

1. `chores-tracker-backend` pods emit OTLP spans on startup, visible in Coroot's trace view.
2. Traces show FastAPI request spans **and** SQLAlchemy child spans for DB calls.
3. No regression in existing Prometheus scraping or health checks.
4. Config is environment-variable-driven (no code changes gated to a commit).
5. Zero secrets added; OTLP endpoint is cluster-internal plaintext.

### Out of scope

- Frontend (React/HTMX) tracing — separate effort.
- Log correlation (trace_id injection into logs) — follow-up phase.
- Sentry integration — separate evaluation.
- Sampling tuning beyond defaults.

---

## 2. Technical Approach (LEVER applied)

- **Leverage existing patterns**: the app already runs as a FastAPI service with `/metrics`. We reuse the same env-var config pattern (`configmaps.yaml`) for OTel settings.
- **Extend before creating**: no new Deployment, no new Service, no new secret. Only config + a container image rebuild with OTel SDK added.
- **Verify through reactivity**: Argo Rollouts canary already handles safe rollout; we'll ride that mechanism.
- **Eliminate duplication**: use OTel **auto-instrumentation** (`opentelemetry-instrument`) rather than manual `@tracer.start_as_current_span` sprinkling.
- **Reduce complexity**: send directly to Coroot's OTLP endpoint; no collector sidecar, no gateway.

### Target Coroot endpoint

Coroot's in-cluster Service exposes OTLP ingestion on a dedicated gRPC port. **Confirmed endpoint (Phase 1):**

```
coroot-coroot.coroot.svc.cluster.local:4317   # OTLP gRPC
```

**Note:** Coroot only exposes gRPC (4317). Port 4318 (HTTP/protobuf) is **not** exposed by this deployment — we must use gRPC. Port 8080 is the UI, not OTLP.

### East-west path to Coroot

chores-tracker pod → ztunnel (mTLS) → coroot namespace → Coroot pod. Works without extra policy since ambient mesh allows intra-cluster traffic by default. If AuthorizationPolicies are tightened later, add an `AuthorizationPolicy` permitting `chores-tracker` SA to call Coroot.

---

## 3. Phased Implementation

### Phase 1 — Discovery & Verification *(0.5 day)*

**Goal:** Confirm exact OTLP endpoint, protocol, and that Coroot will accept our spans.

- ✅ **1.1** `kubectl get svc -n coroot` — identified service `coroot-coroot` exposes ports `8080/http` (UI) and `4317/grpc` (OTLP)
- ✅ **1.2** Service port definitions confirmed via `kubectl get svc coroot-coroot -n coroot -o yaml` — port 4317 is named `grpc`, targetPort `grpc`
- ✅ **1.3** Protocol decision: **gRPC (4317)** — no choice, 4318 HTTP/protobuf is not exposed. Python SDK supports gRPC natively via `opentelemetry-exporter-otlp-proto-grpc`
- ✅ **1.4** Reachability verified from `chores-tracker` namespace:
  ```
  coroot-coroot.coroot.svc.cluster.local (10.43.1.250:4317) open
  ```
- ✅ **1.5** ClickHouse storage confirmed from Coroot CR: `tracesTTL: 7d`, ClickHouse PVC `data-coroot-clickhouse-shard-0-0` = 20Gi

**Exit criteria MET:** Final endpoint = `coroot-coroot.coroot.svc.cluster.local:4317` (gRPC, insecure/plaintext, cluster-internal).

---

### Phase 2 — Application Changes *(1 day)*

**Goal:** Rebuild the app container with OTel auto-instrumentation available.

> **Correction from original plan:** this repo is a monorepo — backend source (`backend/`) and infra (`base-apps/`, root `Dockerfile`) live together. Phase 2 changes were made in-place here.

- ✅ **2.1** Added to `backend/requirements.txt`:
  ```
  opentelemetry-distro>=0.48b0
  opentelemetry-exporter-otlp-proto-grpc>=1.27.0   # gRPC exporter (Coroot exposes 4317 only)
  opentelemetry-instrumentation-fastapi>=0.48b0
  opentelemetry-instrumentation-sqlalchemy>=0.48b0
  opentelemetry-instrumentation-asyncpg>=0.48b0    # swapped for httpx/asyncpg — app uses these, not `requests`
  opentelemetry-instrumentation-httpx>=0.48b0
  opentelemetry-instrumentation-logging>=0.48b0
  ```
  Deviation from original plan: replaced `opentelemetry-instrumentation-requests` with `httpx` + `asyncpg` since the app actually uses those libraries (httpx for outbound HTTP, asyncpg as the PG driver after the recent MySQL→PostgreSQL migration).
- ✅ **2.2** Updated root `Dockerfile` CMD:
  ```dockerfile
  CMD ["opentelemetry-instrument", "uvicorn", "backend.app.main:app", "--host", "0.0.0.0", "--port", "8000"]
  ```
  Note: the existing `ENTRYPOINT` script (`docker-entrypoint.sh`) ends in `exec "$@"`, so the OTel wrapper flows through after the DB-wait logic.
- ✅ **2.3** Added `RUN opentelemetry-bootstrap -a install` after pip install in the Dockerfile
- ⬜ **2.4** Local smoke test *(user to run)*: `docker compose up` then hit an endpoint — with `OTEL_TRACES_EXPORTER=console` spans print to stdout; with the prod env vars they go to Coroot
- ⬜ **2.5** Build and push new image tag to ECR *(user handles image builds per global CLAUDE.md)*

**Exit criteria:** New image tag in ECR, verified emitting spans. Tasks 2.1–2.3 done; 2.4–2.5 blocked on user.

---

### Phase 3 — Kubernetes Config Changes *(0.5 day)*

**Goal:** Configure the running workload to export OTLP to Coroot.

> All changes live in **`base-apps/chores-tracker-backend/`** in this repo.

- ⬜ **3.1** Update `configmaps.yaml` — add OTel env vars:
  ```yaml
  apiVersion: v1
  kind: ConfigMap
  metadata:
    name: chores-tracker-backend-config
    namespace: chores-tracker
  data:
    ENVIRONMENT: "production"
    DEBUG: "False"
    BACKEND_CORS_ORIGINS: "https://chores.arigsela.com"

    # OpenTelemetry configuration
    OTEL_SERVICE_NAME: "chores-tracker-backend"
    OTEL_RESOURCE_ATTRIBUTES: "service.namespace=chores-tracker,deployment.environment=production"
    OTEL_EXPORTER_OTLP_ENDPOINT: "http://coroot-coroot.coroot.svc.cluster.local:4317"   # confirmed Phase 1 — gRPC
    OTEL_EXPORTER_OTLP_PROTOCOL: "grpc"
    OTEL_EXPORTER_OTLP_INSECURE: "true"
    OTEL_TRACES_EXPORTER: "otlp"
    OTEL_METRICS_EXPORTER: "none"          # keep Prometheus for metrics
    OTEL_LOGS_EXPORTER: "none"             # logs stay on Loki
    OTEL_TRACES_SAMPLER: "parentbased_traceidratio"
    OTEL_TRACES_SAMPLER_ARG: "0.1"         # 10% sampling to start
    OTEL_PYTHON_LOG_CORRELATION: "true"
  ```
- ⬜ **3.2** Update `deployments.yaml` — bump image tag to the 2.5 build
- ⬜ **3.3** Commit and push — ArgoCD syncs, Argo Rollouts canaries 20% → 50% → 80% → 100%
- ⬜ **3.4** Watch rollout: `kubectl argo rollouts get rollout chores-tracker-backend -n chores-tracker -w`

**Exit criteria:** New ReplicaSet healthy, rollout promoted, /health still 200.

---

### Phase 4 — Validation *(0.5 day)*

- ⬜ **4.1** `kubectl logs -n chores-tracker -l app=chores-tracker-backend | grep -i otel` — verify no exporter errors
- ⬜ **4.2** Generate traffic: hit `https://chores.arigsela.com` with a few requests
- ⬜ **4.3** Open Coroot UI → chores-tracker-backend service → Traces tab — confirm spans appear with method + path
- ⬜ **4.4** Verify **SQL spans** appear as children of HTTP spans (proves SQLAlchemy instrumentation works)
- ⬜ **4.5** Trigger a 500 (hit an intentionally failing endpoint if any, or `kubectl exec` to kill DB connection briefly) — confirm exception attributes on spans
- ⬜ **4.6** Check Coroot node agent CPU usage — expect no material change (OTLP is cheap at 10% sampling)
- ⬜ **4.7** Confirm `/metrics` still scraped (check Prometheus targets page)

**Exit criteria:** Traces visible in Coroot, no regressions.

---

### Phase 5 — Hardening (Follow-up) *(optional, 0.5 day)*

- ⬜ **5.1** Tune sampling rate based on volume (if too sparse, raise to 25% or 50%)
- ⬜ **5.2** Add AuthorizationPolicy allowing `chores-tracker` SA → Coroot (only if cluster-wide default-deny is adopted later)
- ⬜ **5.3** Add trace_id to app log format for Loki correlation
- ⬜ **5.4** Repeat the pattern for `chores-tracker-frontend`, `weather-kitchen-backend`, `agent-ui-backend`, etc.
- ⬜ **5.5** Document the pattern in `docs/kubernetes-networking-and-service-mesh.md` or a new `docs/otel-instrumentation-pattern.md`

---

## 4. Technical Notes

### Why `opentelemetry-instrument` (auto) vs manual SDK setup

- **Auto**: one line change in Dockerfile, zero code changes, picks up FastAPI + SQLAlchemy + requests + logging automatically. Downside: less control, slightly higher startup cost.
- **Manual**: explicit `TracerProvider` + `FastAPIInstrumentor.instrument_app(app)` in `main.py`. Downside: code change required, must keep up with SDK version.

Recommendation: **start with auto**, drop to manual only if you need custom spans later.

### Sampling strategy

`parentbased_traceidratio=0.1` means:
- If request arrives with an existing trace context → honor it (full trace stays together).
- If request starts fresh → sample 10% randomly.

This is the safe default. Tune later from Coroot's trace volume.

### Why no Metrics/Logs over OTLP

- **Metrics**: Prometheus already scrapes `/metrics` — don't double up.
- **Logs**: Loki is the log sink. If trace_id correlation is needed later, inject into Loki log lines (Phase 5.3) rather than send logs through OTLP.

### Resource impact estimate

- Memory: +~30–50 MB per pod (OTel SDK + batch span processor)
- CPU: negligible at 10% sampling
- Network: ~few KB/s egress per pod
- Coroot/ClickHouse: traces go into existing 20Gi volume at `tracesTTL: 7d` — monitor disk usage after rollout

---

## 5. Rollback Plan

If traces break the app or flood Coroot:

1. Revert `configmaps.yaml` OTel env vars (comment out `OTEL_TRACES_EXPORTER` → SDK goes silent).
2. Or revert `deployments.yaml` image tag to the prior one (`7.0.2`).
3. Commit & push — ArgoCD re-syncs.

No stateful changes, no data migration, fully reversible via Git.

---

## 6. Progress Tracking

| Phase | Tasks | Status |
|---|---|---|
| 1 — Discovery | 5/5 | ✅ Complete |
| 2 — App changes | 3/5 | 🟡 Code done; smoke test + image build pending (user) |
| 3 — K8s config | 0/4 | ⬜ Not started |
| 4 — Validation | 0/7 | ⬜ Not started |
| 5 — Hardening | 0/5 | ⬜ Optional |

**Overall completion:** 8 / 21 core tasks (38%)

---

## 7. Open Questions

1. ~~**Does Coroot CE expose OTLP on 8080 or a dedicated 4317/4318?**~~ — **Resolved:** only 4317 (gRPC) is exposed.
2. **Is the FastAPI app startup already tolerant of the OTel SDK importing?** — resolve in Phase 2.4 local test.
3. **Will the canary rollout correctly surface OTel failures?** — yes, if SDK raises on startup the readiness probe fails and Argo Rollouts holds. No change needed.

---

## 8. References

- OpenTelemetry Python auto-instrumentation: https://opentelemetry.io/docs/languages/python/automatic/
- Coroot OTLP ingestion: https://docs.coroot.com/
- Repo conventions: `CLAUDE.md`, `docs/devops-maturity-implementation-plan.md`
- Related context: `docs/envoy-and-agentgateway-study-guide.md` (tracing comparison Coroot vs Sentry)
