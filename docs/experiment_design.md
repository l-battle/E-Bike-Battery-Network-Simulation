# Experiment & AI Design

How simulation runs become a training dataset, and how that dataset feeds the
AI. This is the source of truth for the data pipeline; build against it.

---

## 1. The learning problem

Two separate jobs (do not conflate):

- **Surrogate** — a supervised model that learns
  `f(scenario, locker layout) → outcomes`. A fast stand-in for the simulator.
- **Optimizer** — a search procedure that uses the surrogate to find the best
  layout. Not ML; it *calls* the surrogate many times.

This document covers generating the data and training the **surrogate**. The
optimizer comes after.

**Phasing**
- **1a (now):** placement only, fixed capacity. Predict outcomes for a layout;
  optimize *where* lockers go.
- **1b:** add capacity (7/8/10) as a decision variable.
- **2:** spatial raster + CNN producing a city suitability heatmap.

---

## 2. Data pipeline

```
candidate sites ─┐
                 ├─► sampler draws (layout, scenario, seed) ─► N combos
scenario ranges ─┘
        │
        ├─► features(layout, scenario) ─────────────► X  ┐
        └─► run simulation (warmup → steady) ─► summarize ─► y ┘
                                                       │
                                           one row per run
                                                       ▼
                                    tabular dataset (CSV) ─► group-split ─► surrogate
```

Each simulation run produces exactly one row. Features are computed cheaply
**before** simulation from `(layout, demand, graph)`; the simulation produces the
targets.

---

## 3. Inputs / features (X)

### Scenario features (sampled conditions)
- `n_riders` (demand load)
- `weather` (categorical)
- `rider_speed_kmh`

### Layout features (engineered, transfer-invariant)
Computed from the locker set + demand zones + graph travel times. Designed to be
unitless / city-agnostic so the model generalizes across layouts and cities.

| Group | Features |
|---|---|
| Supply | `n_lockers`, `total_capacity`, `lockers_per_rider`, `capacity_per_rider` |
| Coverage | `coverage_3min`, `coverage_5min`, `coverage_10min` (% of demand within X min of a locker) |
| Demand-distance | `mean_demand_to_locker_min`, `p90_demand_to_locker_min`, `unmet_demand_frac` |
| Geometry | `locker_dispersion` (mean nearest-neighbor distance), `locker_density_vs_demand` |

**Principle:** prefer aggregate, geometry-aware features over a raw per-site
on/off vector. Aggregates transfer across cities; indicators do not. The raw
indicator vector may be added later as a minor supplement.

---

## 4. Outputs / targets (y)

All already produced by `summarize()` (plus per-locker utilization, pending one
small sim addition):

| Target | Meaning | Business angle |
|---|---|---|
| `stranded_per_hour` | riders stuck per hour | service failure |
| `failed_swaps_per_hour` | empty-locker hits per hour | service failure |
| `swap_success_rate` | swaps / attempts | service quality |
| `trips_per_hour` | throughput | capacity served |
| `locker_utilization` | swaps per locker per hour | ROI / over-provisioning |
| `mean_battery_wh` | fleet battery headroom | system stress |

Multi-output: one model per target.

---

## 5. Row schema

```
metadata:  layout_id, scenario_id, seed        # for group-splitting, NOT features
features:  <scenario features> + <layout features>   (Section 3)
targets:   <targets>                                  (Section 4)
```

The full table of these rows is the training dataset.

---

## 6. Experiment structure (sampling)

**Random / Latin-hypercube sampling over the joint input space — not a full
factorial grid** (which explodes and wastes runs). Each experiment draws:

- **A layout:** random number of lockers (e.g. 3–20) and a random subset of
  candidate sites. Include some *structured* layouts (clustered vs spread,
  demand-aligned vs random) so the geometry features are well covered.
- **A scenario:** `n_riders` from a range (e.g. 5–60), `weather` from the
  presets, `rider_speed_kmh` from a small range.
- **A seed:** for replicates.

Random sampling gives broad, dense coverage of the feature space efficiently.

---

## 7. Data volume

- **Unique `(layout, scenario)` points** matter more than total rows; seeds only
  denoise. Target **~2,000–5,000 unique combos**, optionally ×2–3 seeds.
- A GBM with ~15–25 features is solid at a few thousand rows (1k works, 5k
  comfortable, 10k plenty).
- **Compute:** ~seconds per run (graph reused) → a few thousand runs ≈ a few
  hours; run in background.
- **Run a ~300-run pilot first** to validate the pipeline, check target noise,
  and confirm run length before the full sweep.

---

## 8. Steady-state / run length (data-quality caveat)

Batteries recharge in ~3.5 h ≈ **1,080 steps**. If `warmup_steps` is shorter,
runs are measured while lockers are still draining from their initially-full
state, so targets look artificially good and miss real contention. Therefore:

- `warmup_steps` must **exceed** the recharge time (so the locker economy
  equilibrates).
- `n_steps` must leave a stable measurement window after warmup.
- The pilot confirms metrics have plateaued.

---

## 9. Train / test split

- **Group-split by layout (and scenario), never random rows** — seed replicates
  of the same point would otherwise leak across train/test and inflate scores.
- Hold out **~20%** of unique points as test.
- For transfer claims, eventually hold out a **whole city**.

---

## 10. Model plan (surrogate)

- **Model:** `sklearn.HistGradientBoostingRegressor` (already installed), one per
  target. Random forest / ridge as baselines. No NN until the CNN phase.
- **Evaluate with rank-correlation (Spearman)** between predicted and true
  outcomes across held-out layouts — the optimizer needs correct *ranking* more
  than perfect absolute values — alongside R²/MAE.
- **Feature-importance loop:** train → inspect importances → confirm
  coverage/ratio features dominate → prune/refine.

---

## 11. Components to build (in order)

1. **Candidate-site generator** — produce the set of possible locker locations
   (auto from demand hotspots + high-traffic graph nodes), with a CSV override
   for real sites later. Defines the placement space.
2. **`features(layout, scenario)` module** — turn a locker set + scenario into
   the feature vector in Section 3, reusing `DemandModel` and `city_graph`. Used
   in both data generation and (later) the optimizer's inner loop.
3. **Layout + scenario sampler** — draw random/structured layouts and random
   scenarios from defined ranges (Section 6).
4. **Sampling driver** — loop over draws: compute features, run the sim to
   steady state, summarize, assemble rows, export the CSV. Extends the existing
   `run_sweep`.

Plus the supporting sim change: record **per-locker swap counts** to enable the
per-locker utilization target.

---

## 12. Readiness

The simulator and experiment runner already emit tabular, normalized, seeded
output and reuse one loaded graph. The four components above add layout
variation and feature description on top — after which the dataset exists and
the surrogate/optimizer can be built.
