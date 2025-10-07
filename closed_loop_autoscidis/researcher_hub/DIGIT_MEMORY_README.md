# Digit Memory Experiment

This directory contains the implementation of a digit memory experiment integrated into the closed-loop AutoRA workflow.

## Overview

The digit memory experiment measures participants' ability to remember sequences of digits. The experiment is parameterized by the number of digits (`n_digits`), which serves as the independent variable.

## Experiment Flow

1. **Display Phase** (5 seconds): A random sequence of digits is shown to the participant
2. **Recall Phase**: The participant types in the digits they remember
3. **Feedback Phase** (1 second): Immediate feedback ("Richtig!" or "Falsch.") is shown

## Files

### `experiment_digit_memory.py`

Contains two main functions:

- **`trial_sequence(number_of_trials, n_levels)`**: Generates a counterbalanced sequence of trials with varying `n_digits` values. Uses SweetPea if available, otherwise falls back to a simple balanced randomization.

- **`stimulus_sequence(trials)`**: Converts the trial sequence into JavaScript code that runs in the browser using jsPsych plugins.

### `preprocessing.py`

Contains the `digit_memory_to_experiment_data()` function that converts raw trial data into a pandas DataFrame with:
- **Independent variable**: `n_digits` (number of digits shown)
- **Dependent variable**: `accuracy` (normalized Damerau-Levenshtein similarity between 0 and 1)

The accuracy is calculated using the normalized Damerau-Levenshtein similarity between the shown digits and the participant's response, where:
- 1.0 = perfect match (all digits correct in correct order)
- 0.0 = completely different
- Values between 0 and 1 = partial similarity (some digits correct or transposed)

### `autora_workflow.py`

The main closed-loop workflow that:
1. Generates experiment conditions using experimentalists (random sampling, model disagreement)
2. Deploys experiments to Firebase
3. Collects participant data
4. Fits theoretical models (BMS, Nuts, Logistic Regression)
5. Uses models to generate new experiment conditions

## Integration with Testing Zone

The experiment requires the following jsPsych plugins (already added to `package.json`):
- `jspsych` (^7.3.0)
- `@jspsych/plugin-html-keyboard-response` (^1.1.0)
- `@jspsych/plugin-survey-html-form` (^1.0.0)

These are imported and exposed as globals in `testing_zone/src/design/main.js`:
- `initJsPsych`
- `jsPsychHtmlKeyboardResponse`
- `jsPsychSurveyHtmlForm`

## Data Collection

The experiment collects observations in the following format:

```json
{
  "trials": [
    {
      "n_digits": 5,
      "shown": "12345",
      "response": "12345",
      "correct": true
    },
    ...
  ]
}
```

This data is:
1. Sent to Firebase Firestore (`autora_out` collection)
2. Downloaded by the AutoRA workflow
3. Preprocessed into experimental data
4. Used by theorists to fit models
5. Used by experimentalists to select new conditions

## Running the Workflow

1. Ensure Firebase credentials are in `firebase-service-account.json`
2. Run the workflow:
   ```bash
   cd researcher_hub
   python autora_workflow.py
   ```

The workflow will:
- Generate initial conditions using random sampling
- Upload experiments to Firebase
- Wait for participants to complete the experiment
- Collect and preprocess data
- Fit three types of models (Nuts, BMS, Logistic Regression)
- Use model disagreement to select new conditions
- Repeat for the specified number of cycles

## Configuration

Key parameters in `autora_workflow.py`:
- `num_cycles`: Number of closed-loop iterations (default: 2)
- `num_trials`: Trials per experiment run (default: 4)
- `num_conditions_per_cycle`: Distinct n_digits conditions per cycle (default: 1)
- `N_DIGITS_LEVELS`: Range of n_digits values (default: 3-9)

## Output

The workflow generates:
- `experiment_data.csv`: All collected experimental data
- `model_comparison.png`: Visualization comparing the three models
