import pandas as pd
from src.ai.dataset import prepare_features
from src.experiments.features import compute_features

def _model_row(feats, feature_names):
    """Turn a compute_features dict into a 1-row DataFrame matching the
    surrogate's training columns exactly."""
    X = prepare_features(pd.DataFrame([feats]))      # same transform as training
    return X.reindex(columns=feature_names, fill_value=0)

def greedy_optimize(candidate_sites, scenario, surrogate, objective,
                    feature_names, city_graph, demand, budget, min_gain=0.0):
    candidate_nodes = [c["node_id"] for c in candidate_sites]

    def score_layout(layout):
        feats = compute_features(city_graph, demand, layout, scenario)
        X = _model_row(feats, feature_names)
        pred = surrogate.predict(X).iloc[0]      # a Series of predicted targets
        return objective.score(pred)

    chosen = []
    current = score_layout(chosen)               # empty-layout baseline
    history = [{"n_lockers": 0, "score": current, "layout": []}]

    while len(chosen) < budget:
        best_node, best_score = None, current
        for node in candidate_nodes:
            if node in chosen:
                continue
            s = score_layout(chosen + [node])
            if s > best_score:
                best_node, best_score = node, s

        if best_node is None or best_score - current <= min_gain:
            break                                # adding nothing helps -> stop

        chosen.append(best_node)
        current = best_score
        history.append({"n_lockers": len(chosen),
                        "score": current, "layout": list(chosen)})

    return chosen, history