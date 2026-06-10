import pandas as pd
from src.ai.dataset import prepare_features
from src.experiments.features import compute_features

def _model_row(feats, feature_names):
    """Turn a compute_features dict into a 1-row DataFrame matching the
    surrogate's training columns exactly."""
    X = prepare_features(pd.DataFrame([feats]))      # same transform as training
    return X.reindex(columns=feature_names, fill_value=0)

def greedy_optimize(candidate_sites, scenario, surrogate, objective,
                    feature_names, city_graph, demand, budget):
    """Forward-greedy placement.

    At each step adds the candidate that scores highest, building the full
    budget-vs-score curve, then returns the best-scoring layout found (not
    necessarily the full budget). Running to budget rather than stopping at the
    first plateau is robust to a noisy surrogate and yields the diminishing-
    returns curve in `history`.
    """
    candidate_nodes = [c["node_id"] for c in candidate_sites]

    def score_layout(layout):
        feats = compute_features(city_graph, demand, layout, scenario)
        X = _model_row(feats, feature_names)
        pred = surrogate.predict(X).iloc[0]      # a Series of predicted targets
        return objective.score(pred)

    chosen = []
    baseline = score_layout(chosen)              # empty-layout baseline
    history = [{"n_lockers": 0, "score": baseline, "layout": []}]
    best_layout, best_score = list(chosen), baseline

    while len(chosen) < budget and len(chosen) < len(candidate_nodes):
        step_node, step_score = None, float("-inf")
        for node in candidate_nodes:
            if node in chosen:
                continue
            s = score_layout(chosen + [node])
            if s > step_score:
                step_node, step_score = node, s

        if step_node is None:
            break
        chosen.append(step_node)
        history.append({"n_lockers": len(chosen),
                        "score": step_score, "layout": list(chosen)})

        if step_score > best_score:
            best_score = step_score
            best_layout = list(chosen)

    return best_layout, history