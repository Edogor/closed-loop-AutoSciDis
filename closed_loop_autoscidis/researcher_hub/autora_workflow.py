"""
Basic Workflow — Digit Memory
    One Independent Variable (n_digits), One Dependent Variable (accuracy)
    Theorist: Nuts, Bayesian Machine Scientist, Logistic Regression
    Experimentalist: Nuts (for both initialization and model-based sampling)
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
from autora.experiment_runner.firebase_prolific import firebase_runner
from autora.state import StandardState, on_state, Delta

from sklearn.linear_model import LogisticRegression
from sklearn.base import BaseEstimator, ClassifierMixin

from experiment_digit_memory import trial_sequence as dm_trial_sequence
from experiment_digit_memory import stimulus_sequence as dm_stimulus_sequence
from preprocessing import digit_memory_to_experiment_data

# --- Nuts theorist import (handles both export names) ---
try:
    from autora.theorist.nuts import NutsRegressor  # preferred export name
except Exception:
    from autora.theorist.nuts import NutsTheorists as NutsRegressor  # fallback

# ---- Always use nuts experimentalist ----
from autora.experimentalist.nuts import sample as _nuts_sample

def pick_conditions(allowed, existing, ivs, models, k):
    print("[nuts experimentalist] Selecting conditions using nuts experimentalist.")
    return _nuts_sample(
        conditions=allowed,
        models=models,
        reference_conditions=existing,
        num_samples=k
    )



np.seterr(all="ignore")


# ------------- Study parameters -------------
num_cycles = 2
num_trials = 4  # trials per experiment run
num_conditions_per_cycle = 1  # distinct n_digits conditions per cycle
N_DIGITS_LEVELS = list(range(3, 10))  # 3..9


# ------------- Variables / design space -------------
variables = VariableCollection(
    independent_variables=[
        Variable(name="n_digits", allowed_values=N_DIGITS_LEVELS),
    ],
    dependent_variables=[Variable(name="accuracy", value_range=(0, 1))],
)

allowed_conditions = grid_pool(variables)


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
def initialize_state(allowed_conditions, num_samples, variables):
    ivs = [iv.name for iv in variables.independent_variables]
    existing = pd.DataFrame(columns=ivs)
    chosen = pick_conditions(allowed_conditions, existing, ivs, [], num_samples)
    return Delta(conditions=chosen.reset_index(drop=True))

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
        n_digits = int(c["n_digits"])
        # Generate digit memory trial sequence
        timeline = dm_trial_sequence(number_of_trials=num_trials, n_levels=[n_digits])
        print(f"Generated counterbalanced trial sequence for n_digits={n_digits}.")
        js_code = dm_stimulus_sequence(timeline)
        print(f"Compiled experiment for n_digits={n_digits}.")
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
        _df = digit_memory_to_experiment_data(_lst)
        experiment_data = pd.concat([experiment_data, _df], axis=0)

    experiment_data = experiment_data.reset_index(drop=True)
    print("Preprocessed experimental data.")
    return Delta(experiment_data=experiment_data)


# ------------- Workflow loop -------------
state = initialize_state(
    state, allowed_conditions=allowed_conditions,
    num_samples=num_conditions_per_cycle,
    variables=variables
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


# ------------- Plot (1D: n_digits vs accuracy) -------------
ivs = [iv.name for iv in variables.independent_variables]
dvs = [dv.name for dv in variables.dependent_variables]
X = state.experiment_data[ivs]
y = state.experiment_data[dvs]

# Aggregate data by n_digits (mean accuracy)
agg = state.experiment_data.groupby('n_digits')['accuracy'].mean().reset_index()

# Create a grid for predictions
iv_range = variables.independent_variables[0].allowed_values
iv_grid = pd.DataFrame({'n_digits': iv_range})

# retrieve in the order we stored them: [Nuts, BMS, LR]
model_nuts, model_bms, model_lr = state.models[-3], state.models[-2], state.models[-1]

# Get predictions
dv_pred_lr = model_lr.predict(iv_grid).ravel()
dv_pred_bms = model_bms.predict(iv_grid).ravel()
dv_pred_nuts = model_nuts.predict(iv_grid).ravel()

fig, (ax1, ax2, ax3) = plt.subplots(1, 3, figsize=(18, 5))

# Plot 1: Logistic Regression
ax1.scatter(agg['n_digits'], agg['accuracy'], color='red', s=100, label='Data', zorder=3)
ax1.plot(iv_grid['n_digits'], dv_pred_lr, 'b-', linewidth=2, label='Model')
ax1.set_xlabel('Number of Digits', fontsize=12)
ax1.set_ylabel('Accuracy', fontsize=12)
ax1.set_ylim(-0.1, 1.1)
ax1.set_title('Logistic Regression', fontsize=14)
ax1.legend()
ax1.grid(True, alpha=0.3)

# Plot 2: BMS
ax2.scatter(agg['n_digits'], agg['accuracy'], color='red', s=100, label='Data', zorder=3)
ax2.plot(iv_grid['n_digits'], dv_pred_bms, 'b-', linewidth=2, label='Model')
ax2.set_xlabel('Number of Digits', fontsize=12)
ax2.set_ylabel('Accuracy', fontsize=12)
ax2.set_ylim(-0.1, 1.1)
try:
    ax2.set_title(f"BMS: {model_bms.repr()}", fontsize=14)
except Exception:
    ax2.set_title("BMS", fontsize=14)
ax2.legend()
ax2.grid(True, alpha=0.3)

# Plot 3: Nuts
ax3.scatter(agg['n_digits'], agg['accuracy'], color='red', s=100, label='Data', zorder=3)
ax3.plot(iv_grid['n_digits'], dv_pred_nuts, 'b-', linewidth=2, label='Model')
ax3.set_xlabel('Number of Digits', fontsize=12)
ax3.set_ylabel('Accuracy', fontsize=12)
ax3.set_ylim(-0.1, 1.1)
try:
    title = getattr(model_nuts, "print_eqn", lambda: "")() or "Nuts"
    ax3.set_title(str(title) if isinstance(title, str) else "Nuts", fontsize=14)
except Exception:
    ax3.set_title("Nuts", fontsize=14)
ax3.legend()
ax3.grid(True, alpha=0.3)

plt.tight_layout()
plt.savefig("model_comparison.png", dpi=160)
plt.show()

# save data for later re-plotting if needed
state.experiment_data.to_csv("experiment_data.csv", index=False)
print("Saved: experiment_data.csv and model_comparison.png")
