import numpy as np
import pandas as pd

from src.ai.surrogate import Surrogate, train_surrogate


def _learnable_data(n=400, seed=0):
    """Targets that are clear functions of the features, so a working model
    must score high."""
    rng = np.random.default_rng(seed)
    X = pd.DataFrame({
        "a": rng.uniform(0, 1, n),
        "b": rng.uniform(0, 1, n),
    })
    y = pd.DataFrame({
        "t1": 3 * X["a"] - 2 * X["b"] + rng.normal(0, 0.01, n),
        "t2": X["a"] ** 2 + rng.normal(0, 0.01, n),
    })
    return X, y


def _split(X, y, n_train=320):
    return (X.iloc[:n_train], X.iloc[n_train:],
            y.iloc[:n_train], y.iloc[n_train:])


def test_fit_sets_target_names():
    X, y = _learnable_data()
    s = Surrogate().fit(X, y)
    assert s.target_names == ["t1", "t2"]


def test_predict_shape_and_labels():
    X, y = _learnable_data()
    Xtr, Xte, ytr, yte = _split(X, y)
    preds = Surrogate().fit(Xtr, ytr).predict(Xte)
    assert list(preds.columns) == ["t1", "t2"]
    assert len(preds) == len(Xte)
    assert list(preds.index) == list(Xte.index)   # alignment preserved


def test_model_actually_learns():
    X, y = _learnable_data()
    Xtr, Xte, ytr, yte = _split(X, y)
    metrics = Surrogate().fit(Xtr, ytr).evaluate(Xte, yte)
    assert metrics["t1"]["r2"] > 0.8
    assert metrics["t2"]["r2"] > 0.8
    assert metrics["t1"]["spearman"] > 0.8


def test_evaluate_structure():
    X, y = _learnable_data()
    Xtr, Xte, ytr, yte = _split(X, y)
    metrics = Surrogate().fit(Xtr, ytr).evaluate(Xte, yte)
    assert set(metrics) == {"t1", "t2"}
    assert set(metrics["t1"]) == {"r2", "mae", "spearman"}


def test_save_load_round_trip(tmp_path):
    X, y = _learnable_data()
    Xtr, Xte, ytr, yte = _split(X, y)
    s = Surrogate().fit(Xtr, ytr)
    path = tmp_path / "surrogate.joblib"
    s.save(path)

    loaded = Surrogate.load(path)
    assert loaded.target_names == s.target_names
    np.testing.assert_allclose(
        loaded.predict(Xte).values, s.predict(Xte).values
    )


def test_train_surrogate_helper():
    X, y = _learnable_data()
    # fake a Dataset-like object with the four split attributes
    Xtr, Xte, ytr, yte = _split(X, y)
    Dataset = type("Dataset", (), {})
    ds = Dataset()
    ds.X_train, ds.X_test, ds.y_train, ds.y_test = Xtr, Xte, ytr, yte

    surrogate, metrics = train_surrogate(ds)
    assert surrogate.target_names == ["t1", "t2"]
    assert metrics["t1"]["r2"] > 0.8
