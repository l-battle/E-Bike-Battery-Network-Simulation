import random

# module level defaults
DEFAULT_RANGES ={
    "n_lockers": (3, 20),
    "n_riders": (5, 60),
    "rider_speed_kmh": (15, 22),
    "weathers": ["clear", "rain", "wind", "snow", "heat"],
}

def sample_layout(candidate_node_ids, rng, k_min, k_max) -> list:
    k = rng.randint(k_min, min(k_max, len(candidate_node_ids)))
    
    return rng.sample(candidate_node_ids, k)

def sample_scenario(rng, ranges) -> dict:
    n_riders = rng.randint(*ranges["n_riders"])
    rider_speed_kmh = rng.randint(*ranges["rider_speed_kmh"])
    weather = rng.choice(ranges["weathers"])
    
    return {
        "n_riders": n_riders,
        "rider_speed_kmh": rider_speed_kmh,
        "weather": weather
    }

def sample_experiments(candidate_sites, n_samples, seeds=(0,),
                       ranges=DEFAULT_RANGES, rng_seed=0) -> list[dict]:
    rng = random.Random(rng_seed)
    candidate_node_ids = [s["node_id"] for s in candidate_sites]

    draws = []
    for combo_id in range(n_samples):
        layout = sample_layout(
            candidate_node_ids, rng,
            ranges["n_lockers"][0], ranges["n_lockers"][1],
        )
        scenario = sample_scenario(rng, ranges)

        for seed in seeds:
            draws.append({
                "combo_id": combo_id,   # same across seed replicates -> group key
                "seed": seed,
                "layout": layout,        # list of node_ids
                "scenario": scenario,    # dict
            })

    return draws