# Day 08 Lab Report

## 1. Team / student

- Name: Duong Chi Thanh
- Repo/commit: main (working tree with local changes)
- Date: 2026-05-11

## 2. Architecture

Workflow uses one `StateGraph` with fixed nodes: `intake -> classify -> ... -> finalize`. The `classify` node routes into five behaviors: `simple` goes straight to `answer`, `tool` goes through `tool -> evaluate -> answer`, `missing_info` goes to `clarify`, `risky` goes to `risky_action -> approval -> tool`, and `error` goes into `retry -> tool -> evaluate` until success or `dead_letter`. All paths terminate at `finalize -> END`.

## 3. State schema

State stays lean and serializable. Scalar control fields are overwritten each step, while audit trails use append-only reducers.

| Field | Reducer | Why |
|---|---|---|
| `thread_id` | overwrite | stable checkpointer key per run |
| `scenario_id` | overwrite | metric correlation |
| `query` | overwrite | normalized user request |
| `route` | overwrite | current routing decision |
| `risk_level` | overwrite | approval context |
| `attempt` | overwrite | bounded retry counter |
| `max_attempts` | overwrite | retry limit per scenario |
| `final_answer` | overwrite | terminal response |
| `pending_question` | overwrite | clarification output |
| `proposed_action` | overwrite | risky action summary |
| `approval` | overwrite | reviewer decision |
| `evaluation_result` | overwrite | gate between retry and answer |
| `messages` | append | lightweight message trace |
| `tool_results` | append | tool execution history |
| `errors` | append | retry and dead-letter evidence |
| `events` | append | audit trail for metrics/debugging |

## 4. Scenario results

| Scenario | Expected route | Actual route | Success | Retries | Interrupts |
|---|---|---|---:|---:|---:|
| S01_simple | simple | simple | Yes | 0 | 0 |
| S02_tool | tool | tool | Yes | 0 | 0 |
| S03_missing | missing_info | missing_info | Yes | 0 | 0 |
| S04_risky | risky | risky | Yes | 0 | 1 |
| S05_error | error | error | Yes | 2 | 0 |
| S06_delete | risky | risky | Yes | 0 | 1 |
| S07_dead_letter | error | error | Yes | 1 | 0 |

### Metrics summary

- Total scenarios: 7
- Success rate: 100.00%
- Average nodes visited: 6.43
- Total retries: 3
- Total interrupts: 2

## 5. Failure analysis

1. Retry or tool failure: error scenarios intentionally emit `ERROR` tool results on early attempts. `evaluate_node` marks these as `needs_retry`, `retry_or_fallback_node` increments `attempt`, and `route_after_retry` stops once `attempt >= max_attempts` so the loop cannot run forever.
2. Risky action without approval: risky queries never go directly to `tool`. They must pass `risky_action -> approval`, and only `approved=True` continues to tool execution. Rejected approvals route to clarification instead of executing a destructive action.

## 6. Persistence / recovery evidence

Each scenario starts from `initial_state()` with a dedicated `thread_id` (`thread-<scenario_id>`), and CLI passes that same id into `graph.invoke(..., config={"configurable": {"thread_id": state["thread_id"]}})`. Current lab config uses `MemorySaver()` for runnable local grading. SQLite support was also implemented in the checkpointer adapter using `sqlite3.connect(...)`, WAL mode, and `SqliteSaver(conn=...)`, which matches the lab guidance for persistent checkpoints.

## 7. Extension work

Completed extension: SQLite checkpointer adapter. The code now supports `kind="sqlite"` with explicit SQLite connection management and WAL journaling instead of the older `from_conn_string()` shortcut. This prepares the repo for checkpoint persistence and crash-recovery demos when the optional SQLite package is installed.

## 8. Improvement plan

If given one more day, first improvement would be stronger answer generation and evaluation. Right now routing and retry behavior are reliable, but `tool_node`, `answer_node`, and `evaluate_node` still use deterministic mock logic. Next production step would be structured tool payloads plus richer evaluation criteria so answers stay grounded while retries remain bounded and observable.
