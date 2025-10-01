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

# --- Import preprocessing functions
from preprocessing import digit_memory_trial_list_to_experiment_data

# ==============================
# Parameters
# ==============================
num_cycles: int = 1                 # closed-loop cycles
num_trials: int = 4                # trials per experiment (inside JS timeline)
num_conditions_per_cycle: int = 1   # distinct n_digits conditions per cycle
N_DIGITS_LEVELS: List[int] = list(range(3, 10))  # 3..9

# Debug mode: Set to False to reduce verbose logging
DEBUG_MODE: bool = True

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
def runner_on_state(conditions: pd.DataFrame, experiment_data: pd.DataFrame = None):
    """
    Build one JS experiment per condition (n_digits), run it via Firebase,
    and parse observations into tidy (n_digits, accuracy) rows.
    Accumulates data with existing experiment_data if present.
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

    runner = firebase_runner(firebase_credentials=firebase_credentials, time_out=300, sleep_time=5)

    print("Uploading the experiment to Firebase and waiting for data...")
    data_raw: List[str] = runner(to_send)
    print("Collected experimental data.")
    
    # DEBUG: Log what we received from Firebase
    if DEBUG_MODE:
        print(f"\n=== DEBUG: Firebase returned {len(data_raw)} items ===")
        for idx, item in enumerate(data_raw):
            print(f"Item {idx}: type={type(item)}, length={len(item) if isinstance(item, str) else 'N/A'}")
            if isinstance(item, str):
                print(f"  First 200 chars: {item[:200]}")

    # Parse observations
    rows: List[Dict[str, Any]] = []
    for item in data_raw:
        try:
            payload = json.loads(item)
            if DEBUG_MODE:
                print(f"\n=== DEBUG: Parsed payload type: {type(payload)} ===")
                if isinstance(payload, dict):
                    print(f"  Payload keys: {list(payload.keys())}")
                elif isinstance(payload, list):
                    print(f"  Payload is list with {len(payload)} items")
                    if len(payload) > 0:
                        print(f"  First item type: {type(payload[0])}")
                        if isinstance(payload[0], dict):
                            print(f"  First item keys: {list(payload[0].keys())}")
        except Exception as e:
            print(f"Warning: could not JSON-decode runner item; skipping. Error: {e}")
            continue

        # Handle different data structures that Firebase might return
        if isinstance(payload, dict) and "trials" in payload:
            trials = payload["trials"]
            if DEBUG_MODE:
                print(f"=== DEBUG: Found 'trials' key with {len(trials)} trials ===")
        elif isinstance(payload, list):
            trials = payload
            if DEBUG_MODE:
                print(f"=== DEBUG: Using payload directly as trials list ({len(trials)} items) ===")
        else:
            trials = payload.get("observation", [])
            if DEBUG_MODE:
                print(f"=== DEBUG: Using 'observation' key with {len(trials)} trials ===")

        # Use the digit memory preprocessing function
        if trials:
            if DEBUG_MODE:
                print(f"=== DEBUG: Processing {len(trials)} trials ===")
                if len(trials) > 0:
                    print(f"  First trial: {trials[0]}")
            processed_data = digit_memory_trial_list_to_experiment_data(trials, debug=DEBUG_MODE)
            if DEBUG_MODE:
                print(f"=== DEBUG: Preprocessing result: {len(processed_data)} rows ===")
            # Convert DataFrame to list of dictionaries and extend rows
            if not processed_data.empty:
                rows.extend(processed_data.to_dict('records'))
                if DEBUG_MODE:
                    print(f"=== DEBUG: Total rows accumulated: {len(rows)} ===")

    new_exp_df = (
        pd.DataFrame(rows).astype({"n_digits": int, "accuracy": float})
        if rows else pd.DataFrame(columns=["n_digits", "accuracy"])
    )
    
    # Provide clear feedback about data collection
    if len(rows) == 0:
        print("\n" + "="*70)
        print("⚠️  WARNING: No experimental data was collected!")
        print("="*70)
        print("\nPossible reasons:")
        print("1. No participants have completed the experiment yet")
        print("   → Check your Firebase console to see if conditions were uploaded")
        print("   → Participants need to visit the testing zone URL to complete experiments")
        print("   → Make sure the testing zone is deployed and accessible")
        print("2. The timeout might still be too short for participants to complete")
        print(f"   → Current timeout: 300 seconds (5 minutes)")
        print("3. Firebase connection issues")
        print("   → Verify firebase-service-account.json is correct")
        print("   → Check Firebase console for any errors")
        print("4. Data structure mismatch")
        print("   → Check Firebase console to see what data is stored")
        print("   → The data should be in 'observations' collection")
        print("\nTo manually test:")
        print("1. Deploy the testing zone: cd testing_zone && npm run build && firebase deploy")
        print("2. Visit the testing zone URL in your browser")
        print("3. Complete an experiment")
        print("4. Check Firebase console for the observation data")
        print("="*70 + "\n")
    else:
        print(f"✓ Successfully collected {len(rows)} trials from Firebase")
    
    # Accumulate with existing experiment data
    if experiment_data is not None and not experiment_data.empty:
        combined_df = pd.concat([experiment_data, new_exp_df], ignore_index=True)
        # Remove any potential duplicate rows (same n_digits and accuracy at same time)
        # but keep legitimate repeated experiments
        print(f"Accumulated experimental data: {len(new_exp_df)} new + {len(experiment_data)} existing = {len(combined_df)} total rows.")
    else:
        combined_df = new_exp_df
        print(f"Preprocessed experimental data: {len(combined_df)} rows.")
    
    # Ensure the data types are correct
    if not combined_df.empty:
        combined_df = combined_df.astype({"n_digits": int, "accuracy": float})
    
    return Delta(experiment_data=combined_df)

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
print("\n" + "="*70)
print("🔬 AutoRA Digit Memory Experiment Workflow")
print("="*70)
print(f"Configuration:")
print(f"  - Cycles: {num_cycles}")
print(f"  - Trials per condition: {num_trials}")
print(f"  - Conditions per cycle: {num_conditions_per_cycle}")
print(f"  - N-digits levels: {N_DIGITS_LEVELS}")
print(f"  - Firebase timeout: 300 seconds (5 minutes)")
print(f"  - Total expected trials: {num_cycles * num_conditions_per_cycle * num_trials}")
print(f"  - Debug mode: {'ENABLED' if DEBUG_MODE else 'DISABLED'}")
if DEBUG_MODE:
    print(f"    (Set DEBUG_MODE = False to reduce logging)")
print("="*70 + "\n")

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

    # Check if we have enough models for model disagreement
    models_to_compare = state.models[-3:] if len(state.models) >= 3 else state.models
    if len(models_to_compare) >= 2:
        # Use model disagreement when we have at least 2 models
        state = experimentalist_on_state(
            state,
            allowed_conditions=allowed_conditions,
            models_to_compare=models_to_compare,
            num_samples=num_conditions_per_cycle
        )
        print("Determined experiment conditions using model disagreement.")
    else:
        # Fall back to random sampling when we don't have enough models
        print(f"Not enough models ({len(models_to_compare)}) for model disagreement; using random sampling.")
        next_conditions = random_sample(allowed_conditions, num_conditions_per_cycle)
        state = state + Delta(conditions=next_conditions)
        print("Determined experiment conditions using random sampling.")

# ==============================
# Save collected data
# ==============================
if state.experiment_data is not None and not state.experiment_data.empty:
    # Save raw data
    data_filename = f"experiment_data_digit_memory_{num_cycles}cycles_{len(state.experiment_data)}trials.csv"
    state.experiment_data.to_csv(data_filename, index=False)
    print(f"\n📊 Saved experimental data to: {data_filename}")
    
    # Save aggregated summary
    agg_data = state.experiment_data.groupby('n_digits').agg({
        'accuracy': ['count', 'mean', 'std']
    }).round(4)
    agg_data.columns = ['n_trials', 'mean_accuracy', 'std_accuracy']
    summary_filename = f"experiment_summary_digit_memory_{num_cycles}cycles.csv"
    agg_data.to_csv(summary_filename)
    print(f"📈 Saved data summary to: {summary_filename}")
    
    print(f"\n🎯 Data collection complete! Collected {len(state.experiment_data)} trials across {len(state.experiment_data['n_digits'].unique())} conditions.")
else:
    print("\n⚠️  Warning: No experimental data was collected!")

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

# ==============================
# Data Analysis Functions
# ==============================
def analyze_collected_data(experiment_data: pd.DataFrame):
    """
    Analyze and summarize the collected experimental data
    """
    if experiment_data is None or experiment_data.empty:
        print("No data to analyze.")
        return None
    
    print("\n" + "="*50)
    print("EXPERIMENTAL DATA ANALYSIS")
    print("="*50)
    
    # Basic statistics
    print(f"Total trials collected: {len(experiment_data)}")
    print(f"Unique n_digits conditions tested: {sorted(experiment_data['n_digits'].unique())}")
    print(f"Overall accuracy: {experiment_data['accuracy'].mean():.3f} ± {experiment_data['accuracy'].std():.3f}")
    
    # Per-condition analysis
    print("\nPer-condition results:")
    summary = experiment_data.groupby('n_digits').agg({
        'accuracy': ['count', 'mean', 'std']
    }).round(3)
    summary.columns = ['n_trials', 'mean_accuracy', 'std_accuracy']
    print(summary)
    
    # Check for sufficient data per condition
    print("\nData sufficiency check:")
    min_trials_per_condition = 3
    sufficient_data = summary[summary['n_trials'] >= min_trials_per_condition]
    insufficient_data = summary[summary['n_trials'] < min_trials_per_condition]
    
    if len(sufficient_data) > 0:
        print(f"✅ {len(sufficient_data)} conditions have sufficient data (≥{min_trials_per_condition} trials)")
    if len(insufficient_data) > 0:
        print(f"⚠️  {len(insufficient_data)} conditions have insufficient data (<{min_trials_per_condition} trials):")
        for n_digits in insufficient_data.index:
            print(f"   n_digits={n_digits}: {insufficient_data.loc[n_digits, 'n_trials']} trials")
    
    return summary


def save_data_with_metadata(experiment_data: pd.DataFrame, models: list, metadata: dict = None):
    """
    Save experimental data with metadata about the experiment
    """
    import json
    from datetime import datetime
    
    if experiment_data is None or experiment_data.empty:
        print("No data to save.")
        return
    
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    
    # Save data
    data_filename = f"digit_memory_experiment_{timestamp}.csv"
    experiment_data.to_csv(data_filename, index=False)
    
    # Save metadata
    metadata_dict = {
        "timestamp": timestamp,
        "total_trials": len(experiment_data),
        "unique_conditions": experiment_data['n_digits'].unique().tolist(),
        "overall_accuracy": float(experiment_data['accuracy'].mean()),
        "models_fitted": len(models),
        "data_filename": data_filename
    }
    
    if metadata:
        metadata_dict.update(metadata)
    
    metadata_filename = f"digit_memory_metadata_{timestamp}.json"
    with open(metadata_filename, 'w') as f:
        json.dump(metadata_dict, f, indent=2)
    
    print(f"💾 Saved data to: {data_filename}")
    print(f"📋 Saved metadata to: {metadata_filename}")
    
    return data_filename, metadata_filename

# Analyze the final collected data
analyze_collected_data(state.experiment_data)

# Save data with comprehensive metadata
if state.experiment_data is not None and not state.experiment_data.empty:
    experiment_metadata = {
        "num_cycles": num_cycles,
        "num_trials_per_condition": num_trials,
        "num_conditions_per_cycle": num_conditions_per_cycle,
        "n_digits_levels": N_DIGITS_LEVELS,
        "preprocessing_function": "digit_memory_trial_list_to_experiment_data"
    }
    save_data_with_metadata(state.experiment_data, state.models, experiment_metadata)
