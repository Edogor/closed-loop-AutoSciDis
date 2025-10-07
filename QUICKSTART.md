# Quick Start Guide: Digit Memory Experiment

## What Has Been Implemented

A complete digit memory experiment is now integrated into your closed-loop AutoRA workflow. Participants see random digit sequences, memorize them, and type them back. The system automatically collects data and uses it to build theoretical models.

## Experiment Details

- **What it measures**: Memory span for digit sequences
- **Independent Variable**: `n_digits` (3-9) - how many digits are shown
- **Dependent Variable**: `accuracy` (0 or 1) - whether the participant was correct
- **Duration**: ~30-60 seconds per participant (depends on number of trials)

## How to Deploy

### 1. Prerequisites
```bash
# In researcher_hub directory
cd closed_loop_autoscidis/researcher_hub
pip install -r requirements.txt

# In testing_zone directory
cd closed_loop_autoscidis/testing_zone
npm install
```

### 2. Add Firebase Credentials

Place your Firebase service account JSON file here:
```
closed_loop_autoscidis/researcher_hub/firebase-service-account.json
```

You can get this file from:
1. Go to Firebase Console → Project Settings → Service Accounts
2. Click "Generate New Private Key"
3. Save as `firebase-service-account.json`

### 3. Deploy Web Experiment

```bash
cd closed_loop_autoscidis/testing_zone
npm run build
firebase deploy
```

Your experiment will be available at the URL shown after deployment.

### 4. Run the Workflow

```bash
cd closed_loop_autoscidis/researcher_hub
python autora_workflow.py
```

The workflow will:
1. Generate initial experiment conditions (random n_digits values)
2. Upload experiments to Firebase
3. Wait for participants to complete them
4. Download and preprocess the data
5. Fit three theoretical models (Nuts, BMS, Logistic)
6. Use model disagreement to select new conditions
7. Repeat for the configured number of cycles

## Configuration

Edit these variables in `autora_workflow.py`:

```python
num_cycles = 2                    # How many closed-loop iterations
num_trials = 4                    # Trials per experiment session
num_conditions_per_cycle = 1      # Conditions to test per cycle
N_DIGITS_LEVELS = list(range(3, 10))  # Range of n_digits (3-9)
```

## Output

After running, you'll get:

1. **experiment_data.csv** - All collected data:
   ```
   n_digits,accuracy
   3,1.0
   5,0.0
   7,1.0
   ```

2. **model_comparison.png** - Visual comparison of the three models showing:
   - How accuracy changes with n_digits
   - Model predictions vs. actual data
   - Three subplots (Logistic, BMS, Nuts)

## Expected Results

Typical pattern: As `n_digits` increases, `accuracy` decreases (it's harder to remember more digits).

Example:
- 3 digits: ~90% accuracy
- 5 digits: ~70% accuracy
- 7 digits: ~40% accuracy
- 9 digits: ~20% accuracy

The theoretical models will capture this relationship and predict where to collect more data.

## Troubleshooting

### "ModuleNotFoundError: No module named 'autora'"
```bash
pip install -r requirements.txt
```

### "Firebase credentials not found"
Make sure `firebase-service-account.json` is in the `researcher_hub/` directory.

### "No data collected"
- Check that your experiment is deployed: `firebase deploy`
- Verify Firebase Firestore is enabled in your project
- Check Firestore rules allow read/write access

### Testing without Firebase
You can test the experiment components locally:
```bash
cd researcher_hub
python -c "from experiment_digit_memory import trial_sequence, stimulus_sequence; print('OK')"
```

## Need Help?

See the detailed documentation in:
- `DIGIT_MEMORY_README.md` - Full technical documentation
- `autora_workflow.py` - Commented workflow code
- `experiment_digit_memory.py` - Experiment implementation

## Key Features

✅ **Closed-Loop**: Automatically generates new conditions based on model disagreement  
✅ **Multi-Model**: Compares Nuts, BMS, and Logistic Regression  
✅ **Firebase-Ready**: Deploys to web for online data collection  
✅ **Real-Time Feedback**: Participants see if they're correct immediately  
✅ **Robust**: Handles early termination and edge cases  
✅ **Documented**: Comprehensive README and inline comments  

## What's Different from the Dots Experiment?

The digit memory experiment replaces the previous dots comparison experiment:

| Aspect | Dots Experiment | Digit Memory |
|--------|----------------|--------------|
| IVs | dots_left, dots_right (2D) | n_digits (1D) |
| DV | accuracy (equal/unequal) | accuracy (correct recall) |
| Display | Visual dots | Text digits |
| Task | Comparison | Memory recall |
| Duration | 2 seconds | 5 seconds |

All workflow components work the same way - only the experiment changed!
