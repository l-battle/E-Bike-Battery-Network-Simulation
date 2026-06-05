# Calibration Reference

The values that make this simulation realistic, where they come from, and how
confident we are in each. This is the source of truth for config parameters;
update `src/utils/config.py` (and the CSVs) to match the **Recommended** column,
and update this doc when a value changes.

---

## 1. Methodology

### Two kinds of parameter
- **Physical** — has real-world ground truth (speeds, battery specs, charge
  times, ferry schedule, weather physics). Made realistic *by construction*:
  cite a source and use it.
- **Behavioral / scenario** — no spec sheet (rider count, demand intensity,
  battery threshold policy). Made realistic by *output matching*: tune until
  aggregate sim metrics match observed real-world KPIs. These are also the
  variables we **sweep** in experiments, not fix.

### Relative vs absolute realism
For the optimization/AI goal, the simulation must respond *correctly to change*
(more lockers → fewer strandings, sensible magnitudes) more than it must hit an
exact absolute number. So **sensitivity analysis** (does each parameter move
outputs in the right direction and scale?) is part of calibration, not an
afterthought.

### Confidence scale
- **High** — well-established spec or published figure.
- **Medium** — defensible estimate from domain knowledge; worth verifying.
- **Low** — placeholder; needs real data or literature before trusting outputs.

---

## 2. Recommended change: put the battery model in physical units

Today the battery is abstract (`level` 0–100, `consumption` 0.005 per metre),
which **cannot be checked against any spec**. Implied range = (100−20)/0.005 =
16 km usable. Re-expressing in **watt-hours (Wh)** makes every related parameter
verifiable against reality.

| Quantity | Abstract (now) | Physical (recommended) | Basis | Conf. |
|---|---|---|---|---|
| Battery capacity | `level = 100` | **500 Wh** | Typical e-bike battery (350–700 Wh); cargo/delivery toward the top | High |
| Energy use (clear) | `0.005 /m` | **12 Wh/km** (0.012 Wh/m) | Pedal-assist e-bike 5–15 Wh/km; delivery load + frequent stops toward the high end; Amsterdam is flat | Medium |
| Reserve threshold | `20` (20%) | **20% = 100 Wh** | Operator/rider reserve policy (behavioral) | Medium |
| Resulting full range | 20 km | **~42 km** | 500 / 12 | — |
| Resulting usable range | 16 km | **~33 km** | (500−100) / 12 | — |

> Action: rename to `BATTERY_CAPACITY_WH`, `CONSUMPTION_WH_PER_KM`,
> `BATTERY_THRESHOLD_FRACTION`. `annotate_travel_costs` already computes
> `battery_cost = length × consumption`; it just needs Wh/km units. Weather and
> ferry logic are unaffected (they already scale `battery_cost`).

---

## 3. Parameter table

### Physical parameters

| Parameter | Current | Recommended | Unit | Basis | Conf. |
|---|---|---|---|---|---|
| `DEFAULT_SPEED_KMH` | 18 | **18** (moving speed) | km/h | E-bike cruising 18–20; EU pedelec assist cutoff 25; this is *moving* speed (no separate light/stop penalty modelled yet) | Medium |
| `DEFAULT_CHARGE_SECONDS` | 10800 (3 h) | **12600 (3.5 h)** | s | 500 Wh ÷ ~140 W charger ≈ 3.6 h; swap stations often charge slowly to preserve cells | Medium |
| Ferry crossing | 240 | **180–240** | s | GVB IJ-ferry crossing ~3–4 min — **verify against GVB schedule** | Medium |
| Ferry wait | 150 | **180** | s | ≈ half the headway; daytime headway ~6 min → avg wait ~3 min — **verify** | Medium |
| Battery capacity | — | **500** | Wh | See §2 | High |
| Consumption (clear) | 0.005/m | **12** | Wh/km | See §2 | Medium |

### Weather multipliers
`travel_time_factor` (slower riding) and `battery_factor` (more drain). Cold's
real effect is reduced *capacity*; we proxy it as higher consumption.

| Condition | Current (tt / batt) | Recommended (tt / batt) | Basis | Conf. |
|---|---|---|---|---|
| clear | 1.00 / 1.00 | 1.00 / 1.00 | baseline | High |
| rain | 1.25 / 1.15 | **1.12 / 1.08** | Rain cuts cycling speed ~10–15%; modest energy effect | Medium |
| wind | 1.10 / 1.25 | **1.05 / 1.20** | Amsterdam windy; headwind raises power a lot on into-wind legs, partly offset by tailwind → net drain up, small net time effect | Medium |
| snow | 1.60 / 1.35 | **1.45 / 1.30** | Rare here but large: slippery → much slower; cold cuts capacity 20–30% | Low |
| heat | 1.05 / 1.10 | **1.03 / 1.05** | Minor speed effect; Li-ion fine in moderate heat | Low |

> Current rain/wind values are probably a bit aggressive. Recommended values are
> more defensible; confirm via sensitivity analysis (§5).

### Behavioral / scenario parameters (tune or sweep, don't hardcode as "true")

| Parameter | Current | Notes | Conf. |
|---|---|---|---|
| `n_riders` | 10 | Sweep variable. Real fleets are large; pick a scale where lockers are meaningfully stressed | Low |
| `n_lockers` / layout | CSV (10) | Sweep variable — this is what optimization will move | Low |
| `DEFAULT_CHARGED_BATTERIES` | 5 | Initial stock per locker; sweep | Low |
| `DEFAULT_LOCKER_CAPACITY` | 10 | Slots per locker; sweep | Low |
| `BATTERY_THRESHOLD_FRACTION` | 0.20 | Reserve policy; tune to observed swap timing | Medium |
| Hotspot weights / radii | CSV | Could be grounded in OSM restaurant density + population; radii 500–1000 m ≈ neighborhood scale | Low |

### Numerical (not physical — resolution/accuracy knobs)

| Parameter | Current | Notes |
|---|---|---|
| `TIME_STEP_SECONDS` | 10 | At 18 km/h = 50 m/step, fine vs ~50–100 m edges. Smaller = more accurate but slower. Keep 10 |
| `MAX_LOCKER_SNAP_METERS` | 200 | Validation threshold only |

---

## 3a. Parameter roles (the bridge to experiments + AI)

Every parameter plays one of four roles. The role decides whether it gets a
single calibrated **value** or a **range/distribution**, and where it shows up
in the AI pipeline. This table defines the experiment sweeps and the surrogate
model's feature/target schema.

| Role | Treatment before learning | In the AI pipeline | Our parameters |
|---|---|---|---|
| **Physical** | One calibrated value (look up) | Fixed constant | speed, battery capacity, Wh/km, charge time, ferry times |
| **Behavior-calibrate** | One calibrated value (output-match to real behavior), then frozen | Fixed constant | battery threshold fraction; locker-choice rule (nearest by travel time) |
| **Scenario condition** | Realistic **range/distribution** — *sampled*, never pinned | Input **feature** | fleet size (n_riders), weather, demand intensity / hotspot variant |
| **Decision variable** | Realistic **range / candidate set** (the search space) | Optimized **after** training; also a feature | **locker placement** |

### Key consequences
- **Do not pre-optimize scenario or decision params to a single value.** The
  surrogate must see them *vary* to learn their effect. Pinning them blinds the
  AI. They get realistic *ranges*, not calibrated points.
- **"Tuned during learning"** refers to the ML model's own hyperparameters
  (tree depth, learning rate) via cross-validation — separate from every
  simulation parameter above.
- **Capacity, battery stock, charger speed** are held constant for now but are
  natural *future* decision variables; keep them as clean single knobs so they
  can be promoted to levers later without refactoring.

### Optimization framing (chosen)
- **Fleet size** = scenario condition (sampled), not a lever.
- **Number of lockers** = budget constraint (sweep a few budgets).
- **Locker placement** = the decision variable: *given a budget of N lockers
  under sampled conditions, where do they go to minimise failed swaps /
  strandings?*

### Resulting AI schema (target)
- **Features** = scenario conditions (fleet size, weather, demand) + decision
  encoding (locker layout / coverage features) + budget N.
- **Targets** = failed-swap rate, stranding rate, delivery success, locker
  utilisation (all normalised per time — see §4).
- **Training rows** = one per `(sampled scenario, sampled layout, seed)` run,
  produced by the experiment framework.

## 4. Calibration targets (output matching)

To validate the *system*, compare these emergent metrics to real KPIs. Mark
which you can source ("a bit of both"):

| Metric | What real value to find | Likely source |
|---|---|---|
| Trips per rider per hour | Courier deliveries/hour in a dense city | Operator data / gig-work studies |
| Distance per delivery | Avg delivery trip length in Amsterdam | OSM analysis / operator data |
| Swaps per rider per day | How often a courier swaps | Battery-swap operator (Swobbee etc.) |
| % shifts hitting empty locker | Service-failure rate | Operator KPI (likely hard to get) |
| Locker utilization | Swaps/locker/day | Operator data |

Where a target is unavailable, rely on physical grounding + sensitivity rather
than pretending to a number.

---

## 5. Sensitivity analysis plan

Before trusting any calibration, vary each parameter ±20–30% (one at a time)
and record how the key outputs (trips/hour, stranding rate, failed-swap rate,
locker utilization) respond. Purpose:
1. **Direction check** — do more lockers/capacity reduce strandings? Does worse
   weather reduce throughput? (Sanity of the model.)
2. **Impact ranking** — which parameters move outputs most? Spend calibration
   effort on those; low-impact params can stay rough estimates.

This is the first thing the experiment framework should produce.

---

## 6. Open questions / data to gather

- [ ] GVB IJ-ferry actual crossing time and daytime headway (→ ferry CSV)
- [ ] Representative delivery e-bike battery capacity & Wh/km (→ §2)
- [ ] Any real Amsterdam courier KPI for output matching (§4)
- [ ] Charger power at swap stations (→ charge time)
- [ ] Restaurant/order density per district (→ hotspot weights)
