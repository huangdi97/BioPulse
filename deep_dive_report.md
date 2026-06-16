# DEEP-DIVE HIDDEN ISSUES REPORT
## BioPulse — one-cloud-four-ends

---

## ISSUE 1: UNTESTED SERVICE FILES (HIGHEST SEVERITY)

**Finding:** 187 out of 199 cloud service files (94%) have NO corresponding test file.

Only 12 services have dedicated test files:
| Service file | Test exists? |
|---|---|
| audit_service.py | ✅ test_audit_service.py |
| compliance_service.py | ✅ test_compliance_service.py / test_compliance.py |
| compliance_engine.py | ✅ test_compliance_engine.py |
| diversion_service.py | ✅ test_diversion_service.py |
| notification_service.py | ✅ test_notification_service.py |
| scheduling_service.py | ✅ test_scheduling_service.py |
| settings_service.py | ✅ test_settings_service.py |
| user_service.py | ✅ test_user_service.py |
| approval_service.py | ✅ test_approval_service.py |
| admission_service.py | ✅ test_admission_service.py |
| visit_service.py | ✅ test_visit_service.py |
| board_service.py | ✅ test_board_service.py |

All other 187 service files have no dedicated unit tests. The existing 55 test files in `cloud/app/tests/` cover integration/end-to-end scenarios or a small subset of services.

---

## ISSUE 2: TEST COVERAGE BY MICROSERVICE

| Microservice | Test files | Lines of production code | Coverage |
|---|---|---|---|
| cloud | 55 | ~60K | Partial (few services covered) |
| opportunity | 8 | ~2K | Thin |
| sales-assistant | 8 | ~3K | Thin |
| sales-coach | 8 | ~3K | Thin |
| assistant | 6 | ~4K | Thin |
| clinical-ops | 5 | ~2K | Thin |
| pharma_intel | 5 | ~2K | Thin |
| management | 4 | ~1K | Minimal |
| market-access | 4 | ~1K | Minimal |
| patient-engage | 4 | ~1K | Minimal |

No microservice has zero test files, but the thinnest (management, market-access, patient-engage) have only 4 test files each.

---

## ISSUE 3: DEAD MODULES — NEVER IMPORTED (HIGH SEVERITY)

### Dead Service Files (9 critical):
| File | Notes |
|---|---|
| `_flying_inspection_data.py` | Underscore-prefixed = meant to be private |
| `competitor_brief_service.py` | Contains `except Exception: pass` with logging, but actually never invoked |
| `compliance_rules.py` | Never imported — rules may be defined elsewhere |
| `decision_intel_inference.py` | Inference logic with no caller |
| `federated_node_aggregator.py` | Federated learning aggregator — never wired up |
| `federated_node_manager.py` | Node management — never wired up |
| `memory_episodic_consolidation.py` | Episodic memory consolidation — never called |
| `mrc_workflow_state.py` | MRC workflow state machine — orphaned |
| `training_coach_recommender.py` | Training recommendations — orphaned |

### Dead agent_runtime/ Files (16 critical):
| File | Notes |
|---|---|
| `agent_worker.py` | Worker implementation — no entry point |
| `agent_protocol.py` | Protocol definition — unused |
| `approval_router.py` | Routing logic — no importer |
| `compliance_trigger.py`, `suggestion_trigger.py`, `analysis_trigger.py` | Various trigger modules — all dead |
| `cost_router.py`, `secret_router.py`, `prompt_router.py`, `trace_router.py`, `pipeline.py` | Routing/pipeline modules — all orphans |
| `hot_reloader.py` | Hot reload — could be useful but dead |
| `scheduler.py` | Scheduler — dead |
| `storage.py` | Storage abstraction — dead |
| `trigger_registry.py`, `analysis_agent.py` | Registry and agent — dead |

### Dead Compliance Files (13 files):
`cloud/app/compliance/` contains a full compliance engine subdirectory with evaluation_service.py, audit_log_service.py, exclusion_gates.py, red_light/core.py, red_light/models.py, red_light/scoring.py, triangulation/* (6 files), audit.py, rules.py — all never imported.

### Dead Analysis Files (4 files):
`cloud/app/analysis/` — verifier.py, pattern_discovery.py, narrator.py, hypothesizer.py — all orphaned.

### Dead Suggestion Files (8 files):
`cloud/app/suggestion/` — brief.py, collector.py, collector_causal.py, collector_hcp.py, collector_intel.py, collector_visit.py, planner.py, recommender.py — entire suggestion subsystem is dead.

### Dead Crawler Files (2 critical):
`cloud/app/crawler/scheduler.py` — never imported.

### Dead Seed Files (18 files):
`cloud/app/seeds/` — all seed data scripts (seed_*.py) are standalone scripts never imported anywhere.

### Dead DDL Schema Files (21 files):
`cloud/app/schemas/ddl/` — all DDL schema definitions duplicated from `shared/columns/` but never imported.

**Total dead modules in cloud/app/: ~80 production files (excluding seeds and DDL schemas)**

---

## ISSUE 4: CIRCULAR IMPORTS (HIGH SEVERITY)

### Immediate circular pairs:
1. **`ai_gateway_service.py`** ⟷ **`semantic_cache_service.py`**: Both import from each other directly.
   - `ai_gateway_service.py` → `SemanticCache` (from semantic_cache_service)
   - `semantic_cache_service.py` → `get_embedding` (from ai_gateway_service)

2. **`api_providers.py`** ⟷ **`base_provider.py`**: Direct mutual import cycle.
   - `api_providers.py` → BaseProvider
   - `base_provider.py` → API provider classes

### Multi-hop cycle:
3. **`base_provider.py`** → **`api_providers.py`** → **`local_providers.py`** → **`base_provider.py`**: 3-hop cycle through the provider hierarchy.

These circular imports may cause `ImportError` at runtime depending on import order, or cause silently broken functionality when modules are partially loaded.

---

## ISSUE 5: SILENT EXCEPTION SWALLOWING (MEDIUM SEVERITY)

### Bare `except: pass` (no exception specified, no logging):
| File | Line | Pattern |
|---|---|---|
| `cloud/app/routers/event_bus_router.py` | 128 | `except Exception:` → silently drops |
| `cloud/app/services/tenant_isolation_service.py` | 13 | `except ModuleNotFoundError:` → graceful stub (acceptable) |
| `cloud/app/suggestion/collector.py` | 13 | `except ModuleNotFoundError:` → graceful stub |
| `cloud/app/suggestion/planner.py` | 11 | `except ModuleNotFoundError:` → graceful stub |
| `patient-engage/app/services/patient_compliance_service.py` | 67 | `except ValueError:` → no action |
| `pharma_intel/app/main.py` | 67 | `except RuntimeError:` → no action |
| `shared/base_service.py` | 27 | `except (NotImplementedError, ImportError):` → no action |
| `shared/conftest_base.py` | 120 | `except sqlite3.OperationalError:` → no action |

### Risky `except Exception: pass` with potential data loss:
| File | Line | Risk |
|---|---|---|
| `cloud/app/services/competitor_brief_service.py` | 158 | `except Exception: pass` — BUT logging exists before pass (acceptable-ish) |
| `cloud/app/crawler/analysis/utils.py` | 28 | `except Exception: pass` — no logging, silently drops errors |
| `cloud/app/crawler/analysis/utils.py` | 191 | `except Exception: pass` (in `load_public_opinions`) |
| `cloud/app/crawler/analysis/sentiment_analyzer.py` | 191 | `except Exception:` — no logging |

### Exception swallowing without logging in critical paths:
- `cloud/app/services/redis_event_backend.py:10` — `except ImportError:` — graceful fallback
- `cloud/app/services/redis_event_backend.py:135` — `except ResponseError:` — caught silently

---

## ISSUE 6: DUPLICATED UTILITY CLASSES (MEDIUM SEVERITY)

| Class | Defined in shared/ | Also defined in |
|---|---|---|
| `ComplianceCheckResult` | `shared/compliance.py:9` | `sales-coach/app/schemas/compliance_training.py:27` |
| `JSONFormatter` | `shared/json_formatter.py` | `cloud/app/middleware/json_formatter.py` |

These duplicates cause maintenance burden: changes to the shared definition won't propagate to local copies, leading to behavioral drift.

---

## ISSUE 7: AGENT_RUNTIME OVERCOMPLEXITY (MEDIUM SEVERITY)

| Metric | Value |
|---|---|
| Production files | **65 files** (57 top-level + 5 in runtime_llm/ + 3 in analyzer/) |
| Test files | Only 9 test files for 65 production files (14% coverage) |
| Total lines | **7,268 lines** |
| Dead files within | **16 production files never imported** (25% of module) |
| Complexity | Includes: circuit_breaker, bulkhead, rate_limiter, cost_governor, cost_router, secret_manager, secret_router, prompt_router, trace_router, hot_reloader, loop_detector, reflection_analyzer, scheduler, pipeline, storage — suggesting over-engineering. Many of these are standard concerns better handled by FastAPI middleware or existing libraries. |

---

## ISSUE 8: LONG METHODS (>50 LINES) (LOW-MEDIUM SEVERITY)

**118 long methods identified** across the codebase.

### Top 10 longest:
| File | Method | Lines |
|---|---|---|
| `cloud/app/seeds/seed_collaboration.py:6` | `seed_collaboration` | 240 |
| `cloud/app/seeds/seed_hcp_sandbox.py:6` | `seed_hcp_sandbox` | 207 |
| `cloud/app/seeds/seed_soap_decision.py:6` | `seed_soap_decision` | 161 |
| `cloud/app/seeds/seed_event_bus.py:6` | `seed_event_bus` | 158 |
| `cloud/app/seeds/seed_s5.py:6` | `seed_s5` | 153 |
| `cloud/app/seeds/seed_brain_memory.py:6` | `seed_brain_memory` | 134 |
| `cloud/app/agent_database.py:12` | `init_agent_db` | 133 |
| `cloud/app/seeds/seed_decision_intel.py:6` | `seed_decision_intel` | 133 |
| `cloud/app/seeds/seed_compliance_v2.py:6` | `seed_compliance_v2` | 127 |
| `cloud/app/services/rl_route_optimizer.py:52` | `pareto_route` | 121 |

### Notable production-critical long methods:
- `cloud/app/services/sage_engine_service.py:61` — `evolve` (120 lines) — complex logic
- `cloud/app/services/feature_classifier.py:6` — `causal_attribution` (114 lines)
- `cloud/app/services/pipeline_executor.py:21` — `run_pipeline` (98 lines)
- `cloud/app/services/utility_ranker.py:21` — `sleep_consolidate` (89 lines)
- `cloud/app/services/rule_evaluator.py:46` — `scan` (83 lines)
- `cloud/app/services/redis_event_backend.py:38` — `deliver` (83 lines)
- `cloud/app/services/ai_gateway_service.py:72` — `chat` (76 lines)

---

## SUMMARY TABLE

| # | Issue | Severity | Count | Key Example |
|---|---|---|---|---|
| 1 | Untested service files | **CRITICAL** | 187/199 (94%) | Zero test coverage for majority of services |
| 2 | Dead modules (orphaned) | **HIGH** | ~80 production files | 9 dead services, 16 dead agent_runtime, 13 dead compliance, 8 dead suggestion, 4 dead analysis, 2 dead crawler |
| 3 | Circular imports | **HIGH** | 3 cycles | ai_gateway ↔ semantic_cache, api_providers ↔ base_provider, 3-hop provider cycle |
| 4 | Silent exception swallowing | **MEDIUM** | 8 bare catches | event_bus_router.py, patient_compliance_service.py, shared/base_service.py |
| 5 | Duplicated utility classes | **MEDIUM** | 2 pairs | ComplianceCheckResult, JSONFormatter |
| 6 | agent_runtime overcomplexity | **MEDIUM** | 65 files / 7.3K LOC | 25% of files are dead; 14% test coverage |
| 7 | Long methods | **LOW-MED** | 118 methods | 240-line seed function; 120-line evolve() in sage_engine_service |
| 8 | Thin test microservices | **MEDIUM** | 5 services with ≤5 test files | management, market-access, patient-engage have 4 tests each |

---

## RECOMMENDED ACTIONS (Priority Order)

1. **Fix circular imports** — `ai_gateway_service.py` / `semantic_cache_service.py` and the provider cycle. Extract shared interface into a third module.

2. **Remove or rewire dead modules** — Audit and either delete or properly integrate the 9 orphaned service files, 16 dead agent_runtime files, and the entire compliance/analysis/suggestion subsystems.

3. **Write tests for untested services** — Prioritize services that have route handlers wired up but zero tests (e.g., memory_service, llm_service, agent_core, research_service, compliance_v2_service).

4. **Fix silent exception swallows** — Add proper logging or re-raises in the 8 bare-catch blocks.

5. **Consolidate duplicated classes** — Delete local `ComplianceCheckResult` and `JSONFormatter` copies, use shared versions.

6. **Refactor long methods** — Break down the 118 methods >50 lines, prioritizing the 50+ production-critical methods (not seeds).

7. **Reduce agent_runtime complexity** — Cut 16 dead files, consolidate middleware-like concerns (rate_limiter, circuit_breaker) into FastAPI middleware patterns.
