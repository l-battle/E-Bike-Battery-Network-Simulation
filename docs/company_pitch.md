# Battery-Swap Network Planning — Proposal & Data Request

A decision-support tool for placing battery-swap lockers in cities: how many,
where, and (next) what size — validated in simulation, ready to be made
city-accurate with operator data.

---

## 1. Executive summary

We have built a working, agent-based simulation of a city-scale e-bike
battery-swap network on real street-map data. It models delivery riders,
battery drain, locker inventory and charging, demand hotspots, weather, and
real constraints (e.g. ferry crossings). It already answers questions like
*"if we change the number or placement of lockers, how do strandings, swap
success and utilisation change?"* — and it answers them in the right direction
and magnitude.

The next stage turns this into an **optimisation tool**: recommend where to
place lockers, how many, and what capacity, for any city and demand level — and
ultimately produce a **locker-suitability heatmap** for a new city before a
single unit is shipped.

To make those recommendations *city-accurate* rather than directionally
correct, we need a focused set of real-world values (Section 5). That is the
ask of this document.

---

## 2. The problem this solves

For a company that manufactures and deploys swap lockers, the hard questions are:

- **Where** to install lockers in a city.
- **How many** — the point of diminishing returns for the budget.
- **What size** (7 / 8 / 10 slots) each location needs.
- **Which lockers will be under-used** (avoid over-provisioning / poor ROI).
- **What a new city needs** before deployment (e.g. expanding to Berlin).

These are expensive decisions made today largely by intuition. The simulation
turns them into measurable, comparable scenarios.

---

## 3. What is already built

A modular, tested simulation engine:

- **Real city graph** (OpenStreetMap) — actual streets, distances, one-way and
  pedestrian constraints, ferry crossings.
- **Time- and physics-based** movement: rider speed, distance, battery drain in
  watt-hours, realistic charging times.
- **Demand model**: weighted hotspot zones (city centre, dining districts,
  stations) driving where deliveries go.
- **Locker network**: inventory, charging queue, finite capacity (7/8/10 slots).
- **Conditions**: weather effects (rain/wind/snow/heat) on speed and battery.
- **Experiment framework**: reproducible, seeded runs; parameter sweeps;
  structured, analysis-ready output.
- **65 automated tests** guarding correctness and stability.

---

## 4. Evidence it behaves correctly

A sensitivity analysis (varying one factor at a time, replicated) confirms the
model responds the way reality does:

| Change | Effect (as expected) |
|---|---|
| More lockers | Fewer strandings, higher swap success, higher battery levels |
| More riders (demand) | More deliveries, but more strandings and lower success |
| Faster riders | More deliveries per hour |
| Worse weather | Lower throughput |

Impact ranking on service failures: **demand load ≫ locker supply > speed >
weather** — i.e. the two business levers (how much demand, how many lockers) are
correctly the dominant factors. These *structural* relationships are robust and
do not depend on exact input values — which is why the tool is already useful
for **relative** comparisons today.

---

## 5. What we need from you (the data unlock)

We have built the engine on documented best-estimate values. They are
deliberately conservative and produce directionally-correct behaviour, but
**absolute, city-specific accuracy requires real values.** Prioritised:

### Tier 1 — Hardware & battery (highest impact)
| Data | Why it matters | Format |
|---|---|---|
| Battery capacity | Sets range between swaps → swap frequency | Wh |
| Energy consumption (or rated range) | Same | Wh/km or km range |
| Charge time per battery (and charger power) | Locker replenishment rate → contention | hours / W |
| Confirmed locker slot capacities | We assumed 7/8/10 — confirm/correct | slots |

### Tier 2 — Operations & demand
| Data | Why it matters | Format |
|---|---|---|
| Active fleet size / courier density in target city | Demand load (we sample a range — real range narrows it) | riders, or riders/km² |
| Deliveries per rider per hour | Validates simulated throughput | count/hr |
| Swaps per rider per shift | Validates swap frequency | count/shift |
| Candidate / existing locker sites | Real placement options + a validation benchmark | lat/lon CSV |
| Order/demand density by area (or partner locations) | Grounds demand hotspots | per district / lat-lon |

### Tier 3 — Targets & constraints
| Data | Why it matters | Format |
|---|---|---|
| Service-level target (max acceptable stranding rate, target swap time) | **Defines the optimisation objective** | % / minutes |
| Budget / units per city | Constrains the placement search | count / € |
| Target cities | Focus calibration & transfer | list |

> Note: we do **not** need your existing locker locations in order to
> *recommend* placement — the tool generates and evaluates candidate layouts.
> Your real locations are valuable as a **benchmark** to show the model agrees
> with your expert judgement.

---

## 6. What the data unlocks

| Today (estimates) | With your data |
|---|---|
| Directionally-correct, **relative** comparisons | **Absolute**, city-specific predictions |
| "Layout A beats layout B" | "City X needs N lockers, here, this size" |
| Validated structure | Validated against your real KPIs |
| Amsterdam reference | Any target city, incl. pre-deployment |

The pipeline is designed to absorb real values by re-running and re-training —
no rebuild required. Better inputs improve every output automatically.

---

## 7. Roadmap

1. **Done** — validated simulation engine + experiment framework.
2. **With your data** — calibrate to real values; validate against your KPIs.
3. **AI surrogate + optimiser** — recommend placement, count, then capacity mix.
4. **City transfer** — suitability heatmaps for new cities pre-deployment.

---

## 8. The ask

A short working session to share the Tier 1–2 values above (or point us to
where they live). Even partial data moves the tool from "directionally correct"
to "city-accurate" — and that is the difference between an interesting prototype
and an operational planning tool.
