# Firebase Data Collection - Complete Fix Package

## 📦 What's Included

This fix package contains everything needed to resolve Firebase data collection issues and ensure smooth operation of the AutoRA digit memory experiment workflow.

### 🔧 Core Fixes

1. **autora_workflow.py** - Main workflow with timeout fix (5s → 300s)
2. **preprocessing.py** - Enhanced data preprocessing with debug support

### 📚 Documentation

1. **FIX_SUMMARY.md** - Quick overview of what was fixed (START HERE)
2. **DEBUGGING_FIREBASE.md** - Detailed troubleshooting guide
3. **DATA_COLLECTION_IMPROVEMENTS.md** - Technical details of improvements
4. **README.md** - Updated setup and usage instructions

### 🛠️ Testing Tools

1. **verify_firebase_setup.py** - Verify configuration before running workflow
2. **test_pipeline.py** - Test data processing without Firebase

## 🚀 Quick Start

### Step 1: Verify Your Setup
```bash
cd closed_loop_autoscidis/researcher_hub
python verify_firebase_setup.py
```

**Expected output:**
```
✅ PASSED: Credentials file found and valid
✅ PASSED: autora.experiment_runner.firebase_prolific imported successfully
✅ PASSED: Generated 2 trials, ... chars of JS code
✅ PASSED: Preprocessing correctly converted 2 trials to 2 rows
```

### Step 2: Test the Pipeline (Optional)
```bash
python test_pipeline.py
```

**Expected output:**
```
✅ All tests passed!
📝 Summary:
  ✓ Mock data generation works
  ✓ JSON parsing works
  ✓ Preprocessing function works
  ✓ Data types are correct
  ✓ Edge cases handled
```

### Step 3: Deploy Testing Zone
```bash
cd ../testing_zone
npm run build
firebase deploy --only hosting
```

**Note the URL** (e.g., `https://your-project.web.app`)

### Step 4: Run the Workflow
```bash
cd ../researcher_hub
python autora_workflow.py
```

**Expected output (with DEBUG_MODE=True):**
```
🔬 AutoRA Digit Memory Experiment Workflow
Configuration:
  - Firebase timeout: 300 seconds (5 minutes)
  - Debug mode: ENABLED

=== CYCLE 1/1 ===
Uploading the experiment to Firebase and waiting for data...
Collected experimental data.
✓ Successfully collected 4 trials from Firebase
Preprocessed experimental data: 4 rows.
```

## 📋 Troubleshooting Checklist

### If you get "0 rows collected":

- [ ] **Run verification**: `python verify_firebase_setup.py`
  - All checks should pass
  
- [ ] **Check Firebase credentials**
  - File exists: `firebase-service-account.json`
  - File contains valid JSON with required fields
  
- [ ] **Verify testing zone deployed**
  - Run: `cd ../testing_zone && firebase deploy --only hosting`
  - Open the URL in browser
  - Check for JavaScript errors (F12 console)
  
- [ ] **Check Firebase Firestore**
  - Go to: https://console.firebase.google.com/
  - Your project → Firestore Database
  - `conditions` collection should have documents (uploaded by workflow)
  - `observations` collection should have documents (after experiments complete)
  
- [ ] **Test manually**
  - Open testing zone URL in browser
  - Complete an experiment
  - Check Firestore for new observation
  - Run workflow again

- [ ] **Check debug output**
  - Set `DEBUG_MODE = True` in autora_workflow.py
  - Look for: "Firebase returned X items" (should be > 0)
  - Look for: "Extracted X valid trials" (should be > 0)

### If verification fails:

1. **Credentials error**:
   - Regenerate service account key in Firebase Console
   - Save as `firebase-service-account.json`

2. **Import error**:
   - Run: `pip install -r requirements.txt`

3. **Module error**:
   - Check all files are present
   - Check Python version (≥3.8)

## 📖 Documentation Guide

### For Quick Reference
→ **FIX_SUMMARY.md** - What was fixed, how to use

### For Troubleshooting
→ **DEBUGGING_FIREBASE.md** - Step-by-step debugging

### For Understanding
→ **DATA_COLLECTION_IMPROVEMENTS.md** - Technical details

### For Setup
→ **README.md** - Installation and basic usage

## 🎯 Key Points

### ✅ What Was Fixed

1. **Timeout**: Increased from 5s to 300s (5 minutes)
   - **Critical** - This was preventing all data collection
   
2. **Debug Logging**: Added comprehensive tracking
   - Shows what Firebase returns
   - Tracks data through pipeline
   - Toggle with `DEBUG_MODE` variable
   
3. **Error Messages**: Added clear guidance
   - Explains why no data collected
   - Provides troubleshooting steps
   - Lists common causes

4. **Testing Tools**: Created verification scripts
   - Pre-flight checks (verify_firebase_setup.py)
   - Pipeline testing (test_pipeline.py)

### ✅ What You Need to Do

1. Run verification script
2. Ensure testing zone is deployed
3. Have participants complete experiments
4. Run workflow

The workflow will now collect data correctly when experiments are completed!

## 🔍 Understanding Data Flow

```
┌─────────────────────────────────────────────────────────────┐
│ 1. Researcher Hub (autora_workflow.py)                      │
│    • Generates experiment conditions                         │
│    • Uploads to Firebase Firestore                          │
└─────────────────┬───────────────────────────────────────────┘
                  │
                  ▼
┌─────────────────────────────────────────────────────────────┐
│ 2. Firebase Firestore                                        │
│    • Stores conditions in 'conditions' collection           │
└─────────────────┬───────────────────────────────────────────┘
                  │
                  ▼
┌─────────────────────────────────────────────────────────────┐
│ 3. Participant Browser (Testing Zone)                       │
│    • Fetches condition from Firestore                       │
│    • Runs JavaScript experiment (experiment_digit_memory.py)│
│    • Collects: n_digits, shown, response, correct          │
│    • Uploads observations to Firestore                      │
└─────────────────┬───────────────────────────────────────────┘
                  │
                  ▼
┌─────────────────────────────────────────────────────────────┐
│ 4. Firebase Firestore                                        │
│    • Stores observations in 'observations' collection       │
└─────────────────┬───────────────────────────────────────────┘
                  │
                  ▼
┌─────────────────────────────────────────────────────────────┐
│ 5. Researcher Hub (firebase_runner)                         │
│    • Polls Firestore for up to 300 seconds                 │
│    • Downloads observation data as JSON strings             │
│    • Returns to workflow                                    │
└─────────────────┬───────────────────────────────────────────┘
                  │
                  ▼
┌─────────────────────────────────────────────────────────────┐
│ 6. Researcher Hub (preprocessing.py)                        │
│    • Parses JSON: [{"n_digits": 5, "correct": true}, ...]  │
│    • Extracts n_digits and accuracy (1.0 or 0.0)          │
│    • Creates pandas DataFrame                               │
└─────────────────┬───────────────────────────────────────────┘
                  │
                  ▼
┌─────────────────────────────────────────────────────────────┐
│ 7. Researcher Hub (theorist/experimentalist)                │
│    • Uses data for model fitting                           │
│    • Selects next experiment conditions                     │
└─────────────────────────────────────────────────────────────┘
```

## 🎓 FAQ

### Q: Why was the timeout so short?
**A:** It was likely a placeholder value. Human experiments need much more time than automated tests.

### Q: How do I reduce logging verbosity?
**A:** Set `DEBUG_MODE = False` in `autora_workflow.py` (line ~63)

### Q: Can I test without deploying to Firebase?
**A:** Yes! Run `python test_pipeline.py` to test the data processing pipeline with mock data.

### Q: How do I know if experiments are being completed?
**A:** Check Firebase Console → Firestore Database → `observations` collection. Should have documents after experiments complete.

### Q: What if I still get 0 rows?
**A:** Follow the troubleshooting checklist above. Most likely cause: experiments not being completed by participants.

### Q: How long should I wait?
**A:** The workflow will wait up to 300 seconds (5 minutes) for participants to complete experiments.

## 📞 Support

If issues persist:

1. Review all documentation files
2. Run both verification scripts
3. Check Firebase Console for data
4. Share debug output when asking for help

## 🎉 Success Indicators

You'll know it's working when you see:

✅ `verify_firebase_setup.py` passes all checks
✅ `test_pipeline.py` passes all tests
✅ Workflow shows: "Successfully collected X trials from Firebase"
✅ CSV files are created with actual data
✅ Model fit plots are generated
✅ No "Warning: No experimental data was collected!"

---

**The complete fix package is ready to use!** 🚀

Start with **FIX_SUMMARY.md** for a quick overview, then run the verification scripts.
