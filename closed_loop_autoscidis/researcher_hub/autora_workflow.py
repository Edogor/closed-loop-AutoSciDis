"""
Basic Workflow — Digit Memory
One Independent Variable (n_digits), One Dependent Variable (accuracy)
Theorist: Logistic Regression, Bayesian Machine Scientist, Nuts
Experimentalist: Random Sampling (seed), Model Disagreement
Runner: Firebase Runner (no prolific recruitment)
"""

from __future__ import annotations

import json
import os
import pathlib
from typing import List, Dict, Any

import numpy as np
import pandas as pd
import matplotlib.pyplot as plt

# Quiet noisy gRPC logs (optional)
os.environ.setdefault("GRPC_VERBOSITY", "ERROR")
os.environ.setdefault("GRPC_TRACE", "")

# --- AutoRA core
from autora.variable import VariableCollection, Variable
from autora.state import StandardState, on_state, Delta

# --- Theorists
from autora.theorist.bms import BMSRegressor
from sklearn.linear_model import LogisticRegression
from sklearn.base import BaseEstimator, ClassifierMixin

try:
    from autora.theorist.nuts import NutsRegressor  # preferred name
except ImportError:
    from autora.theorist.nuts import NutsTheorists as NutsRegressor

# --- Experimentalists
from autora.experimentalist.random import random_sample
from autora.experimentalist.model_disagreement import model_disagreement_sample

# --- Runner
from autora.experiment_runner.firebase_prolific import firebase_runner

# --- Import ONLY the digit-memory experiment generators, under unique aliases
from experiment_digit_memory import (
    trial_sequence as dm_trial_sequence,
    stimulus_sequence as dm_stimulus_sequence,
)

# ==============================
# Parameters
# ==============================
num_cycles: int = 1                 # closed-loop cycles
num_trials: int = 4                # trials per experiment (inside JS timeline)
num_conditions_per_cycle: int = 1   # distinct n_digits conditions per cycle
N_DIGITS_LEVELS: List[int] = list(range(3, 10))  # 3..9

# ==============================
# Variables / Design Space
# ==============================
variables = VariableCollection(
    independent_variables=[Variable(name="n_digits", allowed_values=N_DIGITS_LEVELS)],
    dependent_variables=[Variable(name="accuracy", value_range=(0.0, 1.0))],
)
allowed_conditions = pd.DataFrame({"n_digits": N_DIGITS_LEVELS})

# ==============================
# State
# ==============================
state = StandardState(variables=variables)

# ==============================
# Theorists
# ==============================
class LogisticRegressorWrapper(BaseEstimator, ClassifierMixin):
    """Wrap sklearn LogisticRegression so .predict returns P(y=1)."""
    def __init__(self, **kwargs):
        self.model = LogisticRegression(**kwargs)

    def fit(self, X: pd.DataFrame, y: pd.Series | pd.DataFrame):
        y1 = y.values.ravel() if isinstance(y, (pd.DataFrame, pd.Series)) else np.asarray(y).ravel()
        self.model.fit(X, y1.astype(int))
        return self

    def predict(self, X: pd.DataFrame) -> np.ndarray:
        proba = self.model.predict_proba(X)[:, 1]
        return proba.reshape(-1, 1)

bms_theorist = BMSRegressor(epochs=500)
lr_theorist = LogisticRegressorWrapper(max_iter=200)
nuts_theorist = NutsRegressor()

# ==============================
# Components (on_state)
# ==============================
@on_state()
def initialize_state(allowed_conditions: pd.DataFrame, num_samples: int):
    """Seed with random conditions (n_digits)."""
    conds = random_sample(allowed_conditions, num_samples)
    return Delta(conditions=conds)

@on_state()
def runner_on_state(conditions: pd.DataFrame):
    """
    Build one JS experiment per condition (n_digits), run it via Firebase,
    and parse observations into tidy (n_digits, accuracy) rows.
    """
    js_payloads: List[str] = []
    for _, row in conditions.iterrows():
        n = int(row["n_digits"])
        # IMPORTANT: use the digit-memory trial generator (not the old dots one)
        timeline = dm_trial_sequence(number_of_trials=num_trials, n_levels=[n])
        print(f"Generated counterbalanced trial sequence for n_digits={n}.")
        js_code = dm_stimulus_sequence(timeline)
        print(f"Compiled experiment for n_digits={n}.")
        js_payloads.append(js_code)

    to_send = conditions.copy()
    to_send["experiment_code"] = js_payloads

    # Credentials
    cred_path = pathlib.Path(__file__).with_name("firebase-service-account.json")
    firebase_credentials = json.loads(cred_path.read_text(encoding="utf-8"))

    runner = firebase_runner(firebase_credentials=firebase_credentials, time_out=5, sleep_time=3)

    print("Uploading the experiment to Firebase and waiting for data...")
    data_raw: List[str] = runner(to_send)
    print("Collected experimental data.")

    # Parse observations
    rows: List[Dict[str, Any]] = []
    for item in data_raw:
        try:
            payload = json.loads(item)
        except Exception:
            print("Warning: could not JSON-decode runner item; skipping.")
            continue

        if isinstance(payload, dict) and "trials" in payload:
            trials = payload["trials"]
        elif isinstance(payload, list):
            trials = payload
        else:
            trials = payload.get("observation", [])

        for t in trials:
            n = int(t.get("n_digits"))
            correct = bool(t.get("correct"))
            rows.append({"n_digits": n, "accuracy": 1.0 if correct else 0.0})

    exp_df = (
        pd.DataFrame(rows).astype({"n_digits": int, "accuracy": float})
        if rows else pd.DataFrame(columns=["n_digits", "accuracy"])
    )
    print(f"Preprocessed experimental data: {len(exp_df)} rows.")
    return Delta(experiment_data=exp_df)

@on_state()
def theorist_on_state(experiment_data: pd.DataFrame, variables: VariableCollection):
    """Fit Nuts, BMS, and Logistic models."""
    if experiment_data is None or experiment_data.empty:
        print("No experiment data yet; skipping theorist fit.")
        return Delta(models=[])

    ivs = [iv.name for iv in variables.independent_variables]   # ["n_digits"]
    dvs = [dv.name for dv in variables.dependent_variables]     # ["accuracy"]
    X = experiment_data[ivs]
    y = experiment_data[dvs]

    models = [
        nuts_theorist.fit(X, y),
        bms_theorist.fit(X, y),
        lr_theorist.fit(X, y),
    ]
    return Delta(models=models)

@on_state()
def experimentalist_on_state(allowed_conditions: pd.DataFrame,
                             models_to_compare: List[Any],
                             num_samples: int):
    """Model disagreement to pick next n_digits."""
    next_conditions = model_disagreement_sample(
        allowed_conditions,
        models=models_to_compare,
        num_samples=num_samples
    )
    return Delta(conditions=next_conditions)

# ==============================
# Closed-loop Execution
# ==============================
state = initialize_state(
    state,
    allowed_conditions=allowed_conditions,
    num_samples=num_conditions_per_cycle
)

for cycle in range(num_cycles):
    print(f"\n=== CYCLE {cycle+1}/{num_cycles} ===")
    state = runner_on_state(state)
    print("Finished data collection and preprocessing.")
    state = theorist_on_state(state)
    print("Fitted models.")

    models_to_compare = state.models[-3:] if len(state.models) >= 3 else state.models
    state = experimentalist_on_state(
        state,
        allowed_conditions=allowed_conditions,
        models_to_compare=models_to_compare,
        num_samples=num_conditions_per_cycle
    )
    print("Determined experiment conditions.")

# ==============================
# Plot (1D)
# ==============================
if state.experiment_data is not None and not state.experiment_data.empty and state.models:
    iv_name = variables.independent_variables[0].name  # "n_digits"
    dv_name = variables.dependent_variables[0].name    # "accuracy"
    agg = state.experiment_data.groupby(iv_name)[dv_name].mean().reset_index()

    x_grid = np.arange(min(N_DIGITS_LEVELS), max(N_DIGITS_LEVELS) + 0.01, 0.1)
    Xg = pd.DataFrame({iv_name: x_grid})

    curves = []
    labels = []
    try:
        curves.append(state.models[-1].predict(Xg).ravel()); labels.append("Logistic")
    except Exception: pass
    try:
        curves.append(state.models[-2].predict(Xg).ravel()); labels.append("BMS")
    except Exception: pass
    try:
        curves.append(state.models[-3].predict(Xg).ravel()); labels.append("Nuts")
    except Exception: pass

    plt.figure(figsize=(8, 5))
    plt.scatter(agg[iv_name], agg[dv_name], s=60, label="Observed mean")
    for yhat, lab in zip(curves, labels):
        plt.plot(x_grid, np.clip(yhat, 0, 1), label=lab)

    plt.ylim(-0.05, 1.05)
    plt.xlabel("n_digits")
    plt.ylabel("accuracy (P[correct])")
    plt.title("Digit Memory — Model Fits")
    plt.legend()
    plt.tight_layout()
    plt.savefig("model_fits_digit_memory.png")
    plt.show()
else:
    print("No data to plot yet.")
