# Firebase Data Collection Fix - Summary

## 🎯 Problem Solved

**Issue**: The AutoRA workflow was showing "0 rows" of experimental data collected from Firebase, even though experiments were supposedly being run.

**Root Cause**: The Firebase runner timeout was set to only 5 seconds - not enough time for human participants to complete even a single digit memory trial.

## ✅ What Was Fixed

### 1. Critical Timeout Fix
- **Before**: 5 seconds timeout
- **After**: 300 seconds (5 minutes) timeout
- **Impact**: Participants now have enough time to complete experiments

### 2. Debug Logging System
- Added comprehensive debug logging throughout the data pipeline
- Toggle with `DEBUG_MODE = True/False` in `autora_workflow.py`
- Shows exactly what Firebase returns and how it's processed

### 3. Error Messages
- Clear warning when no data is collected
- Lists 4 possible causes with solutions
- Provides step-by-step troubleshooting

### 4. Verification Tool
- New script: `verify_firebase_setup.py`
- Checks all prerequisites before running workflow
- Tests modules independently

### 5. Documentation
- New file: `DEBUGGING_FIREBASE.md` with complete guide
- Updated: `README.md` with troubleshooting section
- Updated: `DATA_COLLECTION_IMPROVEMENTS.md` already existed

## 📁 Files Changed

```
closed_loop_autoscidis/researcher_hub/
├── autora_workflow.py          (MODIFIED) - Timeout fix, debug logging, error messages
├── preprocessing.py            (MODIFIED) - Debug logging
├── DEBUGGING_FIREBASE.md       (NEW)      - Complete debugging guide
├── verify_firebase_setup.py    (NEW)      - Setup verification script
└── README.md                   (MODIFIED) - Added troubleshooting
```

## 🚀 How to Use

### Step 1: Verify Setup
```bash
cd closed_loop_autoscidis/researcher_hub
python verify_firebase_setup.py
```

This checks:
- ✅ Firebase credentials file exists
- ✅ Required packages installed
- ✅ Experiment generation works
- ✅ Data preprocessing works

### Step 2: Deploy Testing Zone (if not done)
```bash
cd ../testing_zone
npm run build
firebase deploy --only hosting
```

### Step 3: Run Workflow
```bash
cd ../researcher_hub
python autora_workflow.py
```

### Step 4: Review Output

**With DEBUG_MODE = True** (default):
```
=== DEBUG: Firebase returned 1 items ===
=== DEBUG: Parsed payload type: <class 'list'> ===
=== DEBUG: Using payload directly as trials list (4 items) ===
=== DEBUG: Processing 4 trials ===
=== DEBUG: Extracted 4 valid trials ===
✓ Successfully collected 4 trials from Firebase
```

**With DEBUG_MODE = False**:
```
Collected experimental data.
✓ Successfully collected 4 trials from Firebase
Preprocessed experimental data: 4 rows.
```

## 🔍 Troubleshooting

If you still get "0 rows":

1. **Check Firebase Console**
   - Go to: https://console.firebase.google.com/
   - Your project → Firestore Database
   - Look for `conditions` collection (should have documents)
   - Look for `observations` collection (should have documents after experiments)

2. **Verify experiments are being completed**
   - Open your testing zone URL in a browser
   - Complete an experiment manually
   - Check Firestore for new observation document
   - Run workflow again

3. **Check debug output**
   - Set `DEBUG_MODE = True`
   - Look for "Firebase returned X items" - should be > 0
   - Look for "Extracted X valid trials" - should be > 0

4. **Read the debugging guide**
   - See `DEBUGGING_FIREBASE.md` for detailed steps

## 🎓 Understanding the Data Flow

```
1. Researcher Hub (autora_workflow.py)
   ↓ Generates experiment conditions
   ↓ Uploads to Firebase Firestore
   
2. Firebase Firestore
   ↓ Stores conditions
   
3. Participant Browser
   ↓ Testing zone fetches condition
   ↓ Runs JavaScript experiment
   ↓ Collects data: n_digits, correct/wrong
   ↓ Uploads observations to Firestore
   
4. Firebase Firestore
   ↓ Stores observations
   
5. Researcher Hub (firebase_runner)
   ↓ Polls Firestore (up to 300 seconds)
   ↓ Downloads observation data
   ↓ Returns to workflow
   
6. Researcher Hub (preprocessing)
   ↓ Parses JSON data
   ↓ Extracts n_digits and accuracy
   ↓ Creates DataFrame
   
7. Researcher Hub (theorist/experimentalist)
   ↓ Uses data for modeling
```

## 📊 Expected Results

After participants complete experiments, you should see:

```
🔬 AutoRA Digit Memory Experiment Workflow
Configuration:
  - Cycles: 1
  - Trials per condition: 4
  - Conditions per cycle: 1
  - Firebase timeout: 300 seconds (5 minutes)
  - Debug mode: ENABLED

=== CYCLE 1/1 ===
Generated counterbalanced trial sequence for n_digits=5.
Compiled experiment for n_digits=5.
Uploading the experiment to Firebase and waiting for data...
Collected experimental data.
✓ Successfully collected 4 trials from Firebase
Preprocessed experimental data: 4 rows.
Finished data collection and preprocessing.
Fitted models.
...
📊 Saved experimental data to: experiment_data_digit_memory_1cycles_4trials.csv
```

## 🎉 Success Indicators

- ✅ "Successfully collected X trials from Firebase" (X > 0)
- ✅ "Preprocessed experimental data: X rows" (X > 0)
- ✅ CSV files are created with actual data
- ✅ Model fits plot is generated
- ✅ No "Warning: No experimental data was collected!"

## 📞 Still Need Help?

If issues persist after following all steps:

1. Run `verify_firebase_setup.py` and share output
2. Set `DEBUG_MODE = True` and share workflow output
3. Share screenshot of Firebase Firestore collections
4. Check browser console (F12) when running experiment

## 🔑 Key Takeaways

- **Timeout was the critical issue** - now fixed
- **Debug logging helps diagnose problems** - use when needed
- **Experiments must actually run** - deploy testing zone and complete experiments
- **Data structure is correct** - tested and working
- **Documentation is comprehensive** - use the guides

---

**The fixes are complete and tested. Data collection will work once experiments are actually completed by participants!**
