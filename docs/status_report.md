# Status Report — E-Bike Battery-Swap Network Simulation

_Last updated: 2026-06-07_

## Summary

The simulation engine is **complete, validated, and tested**, with an AI
surrogate + greedy placement optimiser on top. The system has since been
extended (branch `v1-overhaul`) into a **decision-evaluation and
risk-assessment tool**: a proposed decision is run across seeds and weather
conditions to produce an outcome *distribution*, translated into euros
(profit), giving a leading, risk-aware measure (e.g. probability of loss,
worst-case service level) to complement a lagging P&L. All parameters remain
documented best-estimates pending real operator data.

### v1-overhaul additions (decision-tool)
- **Risk layer** (`experiments/risk.py`) — `evaluate_decision` across
  seeds/weathers; `risk_profile`, `probability_exceeds/below`, `value_at_risk`.
- **Economic layer** (`experiments/economics.py`) — outcomes → revenue, costs,
  profit; combined with risk = a financial risk profile.
- **Robust service KPI** — `delivery_success_rate` (non-degenerate).
- **Performance** — parallel sweeps reuse a per-worker graph in place
  (no per-run 78k-edge copy); idempotent ferry insertion.
- **`scripts/evaluate_decision.py`** — end-to-end: expected profit, P(loss),
  worst-case strandings, profit-distribution plot.

---

## What has been done

### Simulation engine
- **Graph-based** on real OpenStreetMap data (Amsterdam bike network).
- **Time/speed/distance model** — steps are real seconds; riders move at a set
  speed; battery drains per distance.
- **Physical-unit battery model** — watt-hours (≈500 Wh, 12 Wh/km → ~42 km
  range), so values are checkable against real specs.
- **Real locker locations** loaded from CSV, snapped to the graph, with a
  snap-distance warning for bad coordinates.
- **Demand model** — weighted hotspot zones (Gaussian falloff) drive both rider
  spawn and delivery destinations.
- **Route constraints** — generalised travel-time routing (fastest path) plus
  the Centraal–Noord ferry (zero battery, crossing + wait time).
- **Weather** — rain/wind/snow/heat scale speed and battery drain via presets.
- **Realistic locker economy** — finite capacity (7/8/10 slots), time-based
  charging (~3.5 h).

### Tooling & quality
- **Experiment framework** — seeded, reproducible runs; parameter sweeps;
  graph loaded once and reused; ML-ready CSV/JSON export.
- **Sensitivity analysis** — one-at-a-time sweeps with response curves and a
  parameter-impact (tornado) ranking.
- **65 automated tests** (fast synthetic-graph unit tests + slow real-graph
  integration tests).
- **Visualisation** — Folium map (routes, lockers, demand heatmap) and
  Matplotlib metric plots.

### Documentation
- `calibration.md` — every parameter's value, basis, confidence, and role.
- `company_pitch.md` — proposal + prioritised data request for the operator.

---

## Challenges encountered (and resolved)

- **Grid → graph migration.** The project began as a 2D grid; migrating to a
  real graph left substantial dead code, since removed (archived to a branch).
- **Directed-graph connectivity.** The bike network has dead-end nodes; riders
  could reach a node with no onward path, crashing routing. Fixed by
  restricting to the largest strongly connected component.
- **Abstract units.** Battery/consumption were unitless and uncalibratable;
  re-expressed in watt-hours so they can be checked against real specs.
- **Unrealistic charging.** Charging was measured in steps (~100 s per battery);
  made time-based and realistic, which exposed genuine locker contention.
- **Dependency issues** — broken `pyproj`/`scikit-learn` in one environment;
  worked around by reimplementing node snapping without them.
- **Map coverage gap.** Bijlmer ArenA has no coverage in the pulled graph; the
  snap-distance warning flags this rather than silently misplacing lockers.

---

## Key finding

Sensitivity analysis confirms the model is **directionally correct**: more
lockers reduce strandings; higher demand raises throughput but stresses the
network; worse weather lowers throughput. Impact on service failures ranks
**demand ≫ lockers > speed > weather** — the business levers dominate, as they
should. Weather is a comparatively minor factor.

---

## Current limitation

All parameters are **documented best-estimates**, not measured values. The model
is therefore trustworthy for **relative** comparisons but not yet for
**absolute**, city-specific predictions. Closing this requires operator data.

---

## What is next

1. **Secure real data** (immediate focus) — pitch the operator using the
   validated engine + sensitivity results; request battery specs, charge times,
   fleet/demand figures, and service-level targets (`company_pitch.md`).
2. **Calibrate & validate** — plug in real values; validate simulated KPIs
   against the operator's real KPIs.
3. **AI phase** (after calibration) — supervised surrogate (gradient boosting)
   over candidate-site layouts, then an optimiser for placement → count →
   capacity mix. Long-term: spatial CNN producing a city suitability heatmap.

### Small engineering item to enable later AI targets
- Record **per-locker swap counts** (currently only global) — needed before
  per-locker utilisation/ROI can be a prediction target.
