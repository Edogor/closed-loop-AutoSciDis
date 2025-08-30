"""
Basic Workflow
    Two Independent Variables, One Dependent Variable
    Theorist: Nuts (yours), Bayesian Machine Scientist, Logistic Regression
    Experimentalist: Random init + Model Disagreement
    Runner: Firebase Runner (no prolific recruitment)
"""

import json
import pathlib
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt

from autora.variable import VariableCollection, Variable
from autora.theorist.bms import BMSRegressor
from autora.experimentalist.grid import grid_pool
from autora.experimentalist.random import random_sample
from autora.experimentalist.model_disagreement import model_disagreement_sample
from autora.experiment_runner.firebase_prolific import firebase_runner
from autora.state import StandardState, on_state, Delta

from sklearn.linear_model import LogisticRegression
from sklearn.base import BaseEstimator, ClassifierMixin

from trial_sequence import trial_sequence
from stimulus_sequence import stimulus_sequence
from preprocessing import trial_list_to_experiment_data

# --- Nuts theorist import (handles both export names) ---
try:
    from autora.theorist.nuts import NutsRegressor  # preferred export name
except Exception:
    from autora.theorist.nuts import NutsTheorists as NutsRegressor  # fallback

# ---- Use your experimentalist if available; fallback to the example signature ----
try:
    from autora.experimentalist.nuts import nuts_sample as _nuts_sample

    def pick_conditions(allowed, existing, ivs, models, k):
        return _nuts_sample(
            allowed_conditions=allowed,
            existing_conditions=existing,
            num_samples=k,
            feature_cols=ivs,
        )
except ModuleNotFoundError:
    from autora.experimentalist.autora_experimentalist_example import sample as _fallback_sample

    def pick_conditions(allowed, existing, ivs, models, k):
        ref = (existing[ivs] if existing is not None and not existing.empty
               else allowed.iloc[0:0][ivs])
        return _fallback_sample(
            conditions=allowed[ivs],
            models=models,
            reference_conditions=ref,
            num_samples=k,
        )



np.seterr(all="ignore")


# ------------- Study parameters -------------
num_cycles = 2
num_trials = 10
num_conditions_per_cycle = 2


# ------------- Variables / design space -------------
variables = VariableCollection(
    independent_variables=[
        Variable(name="dots_left", allowed_values=np.linspace(1, 100, 100)),
        Variable(name="dots_right", allowed_values=np.linspace(1, 100, 100)),
    ],
    dependent_variables=[Variable(name="accuracy", value_range=(0, 1))],
)

allowed_conditions = grid_pool(variables)
# remove equal-dot conditions
allowed_conditions = allowed_conditions[
    allowed_conditions["dots_left"] != allowed_conditions["dots_right"]
].reset_index(drop=True)


# ------------- State -------------
state = StandardState(variables=variables)


# ------------- LogisticRegressor wrapper -------------
class LogisticRegressor(BaseEstimator, ClassifierMixin):
    def __init__(self, *args, **kwargs):
        self.model = LogisticRegression(*args, **kwargs)

    def fit(self, X, y):
        y_1d = np.asarray(y).ravel()
        self.model.fit(X, y_1d)
        return self

    def predict(self, X):
        # probability of positive class as (n, 1)
        proba = self.model.predict_proba(X)[:, 1]
        return proba.reshape(-1, 1)


# ------------- Instantiate theorists -------------
bms_theorist = BMSRegressor(epochs=500)
lr_theorist = LogisticRegressor()
nuts_theorist = NutsRegressor()  # add params here if you want


# ------------- Theorist on state -------------
@on_state()
def theorist_on_state(experiment_data, variables):
    # nothing to do if no data yet
    if experiment_data is None or experiment_data.empty:
        return Delta()

    ivs = [iv.name for iv in variables.independent_variables]
    dvs = [dv.name for dv in variables.dependent_variables]

    X = experiment_data[ivs]
    y_df = experiment_data[dvs]          # DataFrame for Nuts/BMS
    y_lr = y_df.values.ravel()           # 1-D vector for scikit

    model_nuts = nuts_theorist.fit(X, y_df)
    model_bms = bms_theorist.fit(X, y_df)
    model_lr  = lr_theorist.fit(X, y_lr)

    # order matters for plotting/indexing later:
    return Delta(models=[model_nuts, model_bms, model_lr])


# ------------- Experimentalists -------------
@on_state()
def initialize_state(allowed_conditions, num_samples):
    return Delta(conditions=random_sample(allowed_conditions, num_samples))

@on_state()
def experimentalist_on_state(allowed_conditions, experiment_data, variables, models_to_compare, num_samples):
    ivs = [iv.name for iv in variables.independent_variables]
    existing = (experiment_data[ivs].drop_duplicates()
                if experiment_data is not None and not experiment_data.empty
                else pd.DataFrame(columns=ivs))
    chosen = pick_conditions(allowed_conditions, existing, ivs, models_to_compare, num_samples)
    return Delta(conditions=chosen.reset_index(drop=True))



# ------------- Firebase credentials -------------
CRED_PATH = pathlib.Path(__file__).with_name("firebase-service-account.json")
firebase_credentials = json.loads(CRED_PATH.read_text(encoding="utf-8"))

experiment_runner = firebase_runner(
    firebase_credentials=firebase_credentials,
    time_out=5,
    sleep_time=3,
)


# ------------- Runner on state -------------
@on_state()
def runner_on_state(conditions):
    res = []
    for _, c in conditions.iterrows():
        iv_1 = c["dots_left"]
        iv_2 = c["dots_right"]
        timeline = trial_sequence(iv_1, iv_2, num_trials)
        print("Generated counterbalanced trial sequence.")
        js_code = stimulus_sequence(timeline)
        print("Compiled experiment.")
        res.append(js_code)

    conditions_to_send = conditions.copy()
    conditions_to_send["experiment_code"] = res

    print("Uploading the experiment...")
    data_raw = experiment_runner(conditions_to_send)
    print("Collected experimental data.")

    # preprocess
    experiment_data = pd.DataFrame()
    for item in data_raw:
        _lst = json.loads(item)["trials"]
        _df = trial_list_to_experiment_data(_lst)
        experiment_data = pd.concat([experiment_data, _df], axis=0)

    experiment_data = experiment_data.reset_index(drop=True)
    print("Preprocessed experimental data.")
    return Delta(experiment_data=experiment_data)


# ------------- Workflow loop -------------
state = initialize_state(
    state, allowed_conditions=allowed_conditions,
    num_samples=num_conditions_per_cycle
)

for _ in range(num_cycles):
    state = runner_on_state(state)
    print("Finished data collection and preprocessing.")
    state = theorist_on_state(state)
    print("Fitted models.")
    models_to_compare = [state.models[-1], state.models[-2], state.models[-3]]
    state = experimentalist_on_state(
        state,
        allowed_conditions=allowed_conditions,
        models_to_compare=models_to_compare,
        num_samples=num_conditions_per_cycle
    )
    print("Determined experiment conditions.")


# ------------- Plot (3 panels: LR, BMS, Nuts) -------------
ivs = [iv.name for iv in variables.independent_variables]
dvs = [dv.name for dv in variables.dependent_variables]
X = state.experiment_data[ivs]
y = state.experiment_data[dvs]

iv1_range = variables.independent_variables[0].allowed_values
iv2_range = variables.independent_variables[1].allowed_values
iv1_grid, iv2_grid = np.meshgrid(iv1_range, iv2_range)
iv_grid = np.c_[iv1_grid.ravel(), iv2_grid.ravel()]

# retrieve in the order we stored them: [Nuts, BMS, LR]
model_nuts, model_bms, model_lr = state.models[-3], state.models[-2], state.models[-1]

def _ensure_grid_pred(model):
    pred = model.predict(iv_grid)
    pred = np.asarray(pred).reshape(iv1_grid.shape)
    return pred

dv_pred_lr   = _ensure_grid_pred(model_lr)
dv_pred_bms  = _ensure_grid_pred(model_bms)
dv_pred_nuts = _ensure_grid_pred(model_nuts)

fig = plt.figure(figsize=(18, 5))

ax1 = fig.add_subplot(131, projection="3d")
ax1.scatter(X["dots_left"], X["dots_right"], y, color="red", label="Data")
ax1.plot_surface(iv1_grid, iv2_grid, dv_pred_lr, cmap="viridis", alpha=0.6)
ax1.set_xlabel("dots_left"); ax1.set_ylabel("dots_right"); ax1.set_zlabel("Accuracy"); ax1.set_zlim(0, 1)
ax1.set_title("Logistic Regression")

ax2 = fig.add_subplot(132, projection="3d")
ax2.scatter(X["dots_left"], X["dots_right"], y, color="red", label="Data")
ax2.plot_surface(iv1_grid, iv2_grid, dv_pred_bms, cmap="viridis", alpha=0.6)
ax2.set_xlabel("dots_left"); ax2.set_ylabel("dots_right"); ax2.set_zlabel("Accuracy"); ax2.set_zlim(0, 1)
try:
    ax2.set_title("BMS: " + model_bms.repr())
except Exception:
    ax2.set_title("BMS")

ax3 = fig.add_subplot(133, projection="3d")
ax3.scatter(X["dots_left"], X["dots_right"], y, color="red", label="Data")
ax3.plot_surface(iv1_grid, iv2_grid, dv_pred_nuts, cmap="viridis", alpha=0.6)
ax3.set_xlabel("dots_left"); ax3.set_ylabel("dots_right"); ax3.set_zlabel("Accuracy"); ax3.set_zlim(0, 1)
try:
    title = getattr(model_nuts, "print_eqn", lambda: "")() or "Nuts"
    ax3.set_title(str(title) if isinstance(title, str) else "Nuts")
except Exception:
    ax3.set_title("Nuts")

plt.tight_layout()
plt.savefig("model_comparison.png", dpi=160)
plt.show()

# save data for later re-plotting if needed
state.experiment_data.to_csv("experiment_data.csv", index=False)
print("Saved: experiment_data.csv and model_comparison.png")
