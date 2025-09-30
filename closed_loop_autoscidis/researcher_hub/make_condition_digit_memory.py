# researcher_hub/make_condition_digit_memory.py
from __future__ import annotations
from typing import Dict, Any, List
from experiment_digit_memory import trial_sequence, stimulus_sequence

# Optional: Firestore upload (uncomment to use)
# from firebase_admin import credentials, firestore, initialize_app

# PROJECT_ID = "your-firebase-project-id"
# SERVICE_ACCOUNT_JSON = "path/to/serviceAccountKey.json"

def make_condition_payload(number_of_trials: int = 12,
                           n_levels: List[int] = (3,5,7,9)) -> Dict[str, Any]:
    trials = trial_sequence(number_of_trials=number_of_trials, n_levels=list(n_levels))
    js_code = stimulus_sequence(trials)
    condition = {
        "experiment_code": js_code,
        "n_digits_levels": list(n_levels),
        "meta": {
            "task": "digit_memory",
            "iv": "n_digits",
            "dv": "correct",
            "duration_ms_display": 5000,
            "trials": trials
        }
    }
    return condition

if __name__ == "__main__":
    payload = make_condition_payload(number_of_trials=12, n_levels=(3,5,7,9))
    print("[condition] keys:", list(payload.keys()))
    print("[condition] n_digits_levels:", payload["n_digits_levels"])
    # --- Firestore example (uncomment to push) ---
    # cred = credentials.Certificate(SERVICE_ACCOUNT_JSON)
    # initialize_app(cred, {"projectId": PROJECT_ID})
    # db = firestore.client()
    # ref = db.collection("conditions").document()  # or use a fixed ID
    # ref.set(payload)
    # print("Uploaded condition to:", ref.id)
