# 📋 Firebase Data Collection - Implementation Checklist

Use this checklist to implement the fix and verify everything works.

## ✅ Phase 1: Understand the Fix

- [ ] Read `COMPLETE_FIX_PACKAGE.md` OR `VISUAL_GUIDE.md` (choose one for overview)
- [ ] Understand root cause: **5 second timeout was too short**
- [ ] Understand solution: **Increased to 300 seconds (5 minutes)**

**Why this matters:** The timeout was preventing ANY data collection. This is the critical fix.

---

## ✅ Phase 2: Verify Your Setup

### 2.1 Check Environment
- [ ] Navigate to researcher_hub directory
  ```bash
  cd closed_loop_autoscidis/researcher_hub
  ```

- [ ] Python 3.8+ installed
  ```bash
  python --version
  ```

- [ ] Virtual environment activated (if using)
  ```bash
  # If not activated:
  source venv/bin/activate  # Linux/Mac
  # or
  venv\Scripts\activate     # Windows
  ```

### 2.2 Install Dependencies
- [ ] Install required packages
  ```bash
  pip install -r requirements.txt
  ```

### 2.3 Check Firebase Credentials
- [ ] File exists: `firebase-service-account.json`
  ```bash
  ls -la firebase-service-account.json
  ```

- [ ] If missing, download from Firebase Console:
  - [ ] Go to https://console.firebase.google.com/
  - [ ] Your Project → Settings (⚙️) → Service Accounts
  - [ ] Click "Generate new private key"
  - [ ] Save as `firebase-service-account.json`

### 2.4 Run Verification Script
- [ ] Execute verification
  ```bash
  python verify_firebase_setup.py
  ```

- [ ] All checks passed ✅
  - [ ] ✅ Credentials file found and valid
  - [ ] ✅ Firebase imports successful
  - [ ] ✅ Experiment modules working
  - [ ] ✅ Preprocessing module working

**If any check fails:** See the script output for specific instructions.

---

## ✅ Phase 3: Test the Pipeline (Optional but Recommended)

- [ ] Run pipeline test
  ```bash
  python test_pipeline.py
  ```

- [ ] All tests passed ✅
  - [ ] ✅ Mock data generation works
  - [ ] ✅ JSON parsing works
  - [ ] ✅ Preprocessing function works
  - [ ] ✅ Data types correct
  - [ ] ✅ Edge cases handled

**This test runs WITHOUT Firebase**, just to verify the data processing logic.

---

## ✅ Phase 4: Deploy Testing Zone

### 4.1 Navigate to Testing Zone
- [ ] Change directory
  ```bash
  cd ../testing_zone
  ```

### 4.2 Check Configuration
- [ ] `.env` file exists
  ```bash
  cat .env
  ```

- [ ] Verify settings (should have):
  ```
  REACT_APP_apiKey=...
  REACT_APP_projectId=...
  REACT_APP_useProlificId=False
  ```

### 4.3 Build and Deploy
- [ ] Install dependencies (if not done)
  ```bash
  npm install
  ```

- [ ] Build the app
  ```bash
  npm run build
  ```

- [ ] Deploy to Firebase
  ```bash
  firebase deploy --only hosting
  ```

- [ ] Note the deployed URL (e.g., `https://your-project.web.app`)
  ```
  My URL: _________________________________
  ```

### 4.4 Test Deployed App
- [ ] Open URL in browser
- [ ] No JavaScript errors (check F12 console)
- [ ] App loads correctly

---

## ✅ Phase 5: Test Data Collection Manually (Recommended)

### 5.1 Complete One Experiment
- [ ] Open testing zone URL in browser
- [ ] Complete the digit memory experiment
  - See digits for 5 seconds
  - Type them back
  - Complete all trials

### 5.2 Verify Data in Firebase
- [ ] Go to Firebase Console: https://console.firebase.google.com/
- [ ] Navigate to Firestore Database
- [ ] Check `conditions` collection: Has documents ✅
- [ ] Check `observations` collection: Has documents ✅

**If observations collection is empty:** The experiment data wasn't uploaded. Check browser console for errors.

---

## ✅ Phase 6: Run the Workflow

### 6.1 Return to Researcher Hub
- [ ] Navigate back
  ```bash
  cd ../researcher_hub
  ```

### 6.2 Configure Workflow (Optional)
- [ ] Open `autora_workflow.py`
- [ ] Check settings (lines 57-63):
  ```python
  num_cycles: int = 1              # How many cycles
  num_trials: int = 4              # Trials per experiment
  num_conditions_per_cycle: int = 1  # Conditions per cycle
  DEBUG_MODE: bool = True          # Verbose logging
  ```

- [ ] Adjust if needed
  - [ ] Set `DEBUG_MODE = False` for cleaner output (once working)

### 6.3 Run Workflow
- [ ] Execute workflow
  ```bash
  python autora_workflow.py
  ```

### 6.4 Check Output
- [ ] Should see configuration summary:
  ```
  🔬 AutoRA Digit Memory Experiment Workflow
  Configuration:
    - Firebase timeout: 300 seconds (5 minutes)
    - Debug mode: ENABLED/DISABLED
  ```

- [ ] Should see cycle progress:
  ```
  === CYCLE 1/1 ===
  Generated counterbalanced trial sequence for n_digits=X.
  Compiled experiment for n_digits=X.
  Uploading the experiment to Firebase and waiting for data...
  ```

### 6.5 Wait for Data Collection
- [ ] Workflow is waiting (up to 5 minutes)
- [ ] Participant completes experiment during this time
- [ ] OR use the observation from Phase 5 (manual test)

### 6.6 Verify Success
- [ ] Should see:
  ```
  Collected experimental data.
  ✓ Successfully collected X trials from Firebase
  Preprocessed experimental data: X rows.
  ```

- [ ] Should NOT see:
  ```
  ⚠️ Warning: No experimental data was collected!
  ```

---

## ✅ Phase 7: Verify Results

### 7.1 Check Generated Files
- [ ] CSV file created: `experiment_data_digit_memory_*.csv`
  ```bash
  ls -lh experiment_data_*.csv
  ```

- [ ] Open CSV and verify data:
  - [ ] Has `n_digits` column
  - [ ] Has `accuracy` column
  - [ ] Has actual data rows

### 7.2 Check Summary Files
- [ ] Summary CSV: `experiment_summary_*.csv`
- [ ] Plot generated: `model_fits_digit_memory.png`

### 7.3 Review Data
- [ ] Open CSV in spreadsheet or Python
- [ ] Verify data makes sense:
  - [ ] n_digits values are in expected range (3-9)
  - [ ] accuracy values are 0.0 or 1.0
  - [ ] Number of rows matches expectations

---

## ✅ Phase 8: Troubleshooting (If Needed)

### If You Got "0 rows collected":

- [ ] Review debug output (if DEBUG_MODE=True)
- [ ] Check Firebase Console for data
- [ ] Read `DEBUGGING_FIREBASE.md`
- [ ] Follow troubleshooting steps there

### Common Issues:

**No participants:**
- [ ] Deploy testing zone
- [ ] Complete experiment manually
- [ ] Or recruit participants

**Firebase errors:**
- [ ] Check credentials file
- [ ] Verify Firebase project accessible
- [ ] Check Firestore Database is enabled

**Data structure issues:**
- [ ] Check DEBUG_MODE output
- [ ] See what Firebase returned
- [ ] Verify data format matches expected

---

## ✅ Phase 9: Production Use

### Once Everything Works:

- [ ] Set `DEBUG_MODE = False` for cleaner output
- [ ] Adjust `num_cycles` for your needs
- [ ] Adjust `num_trials` for your needs
- [ ] Configure participant recruitment (if using Prolific)

### For Multiple Cycles:

- [ ] The workflow will:
  1. Generate conditions
  2. Collect data
  3. Fit models
  4. Use model disagreement to select next conditions
  5. Repeat

---

## 📊 Success Criteria

You've successfully implemented the fix when:

- ✅ Verification script passes all checks
- ✅ Test pipeline passes all tests
- ✅ Testing zone deploys without errors
- ✅ Manual experiment completes successfully
- ✅ Data appears in Firebase Firestore
- ✅ Workflow shows "Successfully collected X trials"
- ✅ CSV files contain actual data
- ✅ No "Warning: No experimental data" messages

---

## 📝 Notes and Observations

Use this space to track your progress:

```
Date: _______________

Verification passed: Yes / No
Pipeline test passed: Yes / No
Testing zone deployed: Yes / No
Manual test completed: Yes / No
Workflow first run: Yes / No
Data collected: Yes / No

Issues encountered:
_________________________________
_________________________________
_________________________________

Solutions applied:
_________________________________
_________________________________
_________________________________
```

---

## 🎉 Completion

- [ ] All phases completed
- [ ] Data collection working
- [ ] Workflow running successfully
- [ ] Ready for production use!

**Congratulations! The fix is fully implemented and working!** 🎊

---

## 📚 Quick Reference

- **Overview**: `COMPLETE_FIX_PACKAGE.md` or `VISUAL_GUIDE.md`
- **Quick ref**: `FIX_SUMMARY.md`
- **Troubleshooting**: `DEBUGGING_FIREBASE.md`
- **Technical**: `DATA_COLLECTION_IMPROVEMENTS.md`

**Need help?** Check the troubleshooting guides or review the debug output.
