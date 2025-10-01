# Debugging Firebase Data Collection

This document explains how to debug and fix issues with Firebase data collection in the AutoRA workflow.

## Problem Symptoms

- Workflow shows "Collected experimental data. Preprocessed experimental data: 0 rows."
- Warning: "No experimental data was collected!"
- Cannot find data in Firebase console

## Common Causes and Solutions

### 1. **Firebase Timeout Too Short** ✅ FIXED

**Cause**: The `firebase_runner` timeout was set to 5 seconds, which is not enough time for participants to complete even one trial.

**Solution**: Timeout has been increased to 300 seconds (5 minutes).

**Verification**: Check line ~130 in `autora_workflow.py`:
```python
runner = firebase_runner(firebase_credentials=firebase_credentials, time_out=300, sleep_time=5)
```

### 2. **No Participants Completing Experiments**

**Cause**: The workflow uploads experiment conditions to Firebase, but no one has actually run the experiments yet.

**How to check**:
1. Go to Firebase Console: https://console.firebase.google.com/
2. Navigate to your project → Firestore Database
3. Look for collections: `conditions` and `observations`
4. Check if there are conditions but no observations

**Solution**:
- **Option A: Manual Testing**
  1. Deploy testing zone:
     ```bash
     cd closed_loop_autoscidis/testing_zone
     npm run build
     firebase deploy
     ```
  2. Get the deployed URL from Firebase Hosting
  3. Open the URL in your browser
  4. Complete the experiment
  5. Run the workflow again

- **Option B: Development Mode**
  1. Edit `testing_zone/.env` and set:
     ```
     REACT_APP_devNoDb=False
     REACT_APP_useProlificId=False
     ```
  2. Run testing zone locally:
     ```bash
     cd testing_zone
     npm start
     ```
  3. Open http://localhost:3000 in your browser
  4. Complete the experiment

### 3. **Firebase Credentials Issues**

**Cause**: The `firebase-service-account.json` file is missing or has incorrect credentials.

**How to check**:
```bash
ls -la closed_loop_autoscidis/researcher_hub/firebase-service-account.json
```

**Solution**:
1. Go to Firebase Console
2. Project Settings → Service Accounts
3. Generate new private key
4. Save as `firebase-service-account.json` in researcher_hub directory
5. Verify the file has these fields:
   - type
   - project_id
   - private_key_id
   - private_key
   - client_email

### 4. **Data Structure Mismatch**

**Cause**: The JavaScript experiment returns data in a different format than expected.

**How to check**: Look at the debug output when running the workflow:
```
=== DEBUG: Firebase returned X items ===
=== DEBUG: Parsed payload type: <class 'list'> ===
=== DEBUG: Found X trials ===
```

**Expected data structure**:
```json
[
  {"n_digits": 3, "shown": "123", "response": "123", "correct": true},
  {"n_digits": 5, "shown": "12345", "response": "12346", "correct": false}
]
```

### 5. **Testing Zone Not Properly Deployed**

**Cause**: The testing zone might not be deployed or might have build errors.

**Solution**:
```bash
cd closed_loop_autoscidis/testing_zone

# Install dependencies if needed
npm install

# Build the app
npm run build

# Deploy to Firebase
firebase deploy --only hosting
```

Check for any errors during build or deployment.

## Step-by-Step Debugging Guide

### Step 1: Verify Firebase Setup

```bash
# Check if credentials file exists
ls -la closed_loop_autoscidis/researcher_hub/firebase-service-account.json

# Check if testing zone is configured
cat closed_loop_autoscidis/testing_zone/.env
```

### Step 2: Check Firebase Console

1. Go to: https://console.firebase.google.com/
2. Select your project
3. Go to Firestore Database
4. Check for these collections:
   - `conditions`: Should have documents when workflow runs
   - `observations`: Should have documents after experiments are completed

### Step 3: Test Data Parsing

Run the test script:
```bash
python /tmp/test_data_parsing.py
```

This verifies that the preprocessing function works correctly.

### Step 4: Test Experiment Generation

Run the test script:
```bash
python /tmp/test_experiment_generation.py
```

This verifies that the JavaScript experiment code is generated correctly.

### Step 5: Manual Test with Browser

1. Deploy testing zone:
   ```bash
   cd closed_loop_autoscidis/testing_zone
   npm run build
   firebase deploy --only hosting
   ```

2. Get the URL (should be something like `https://your-project.web.app`)

3. Open in browser and complete an experiment

4. Check Firebase console for new observation document

5. Run workflow again:
   ```bash
   cd closed_loop_autoscidis/researcher_hub
   python autora_workflow.py
   ```

### Step 6: Check Debug Output

When running the workflow, look for these debug messages:

```
=== DEBUG: Firebase returned X items ===
```
- Should be > 0 if experiments were completed

```
=== DEBUG: Parsed payload type: <class 'list'> ===
```
- Should be a list

```
=== DEBUG: Using payload directly as trials list (X items) ===
```
- X should match number of trials completed

```
=== DEBUG: Processing X trials ===
```
- Should match the number from above

```
=== DEBUG: Extracted X valid trials ===
```
- Should be > 0 if data is correctly formatted

## Understanding the Data Flow

```
1. [Researcher Hub]
   autora_workflow.py generates experiment conditions
   ↓ Uploads to Firebase

2. [Firebase]
   Stores conditions in Firestore
   
3. [Participant/Browser]
   testing_zone app fetches condition
   ↓ Runs JavaScript experiment
   ↓ Collects data (n_digits, correct)
   ↓ Uploads observations to Firebase

4. [Firebase]
   Stores observations in Firestore
   
5. [Researcher Hub]
   firebase_runner polls Firebase for observations
   ↓ Downloads observation data
   ↓ Parses JSON
   ↓ Extracts n_digits and accuracy
   ↓ Returns to workflow
```

## Expected Output When Working

```
🔬 AutoRA Digit Memory Experiment Workflow
Configuration:
  - Cycles: 1
  - Trials per condition: 4
  - Conditions per cycle: 1
  - Firebase timeout: 300 seconds (5 minutes)

=== CYCLE 1/1 ===
Generated counterbalanced trial sequence for n_digits=5.
Compiled experiment for n_digits=5.
Uploading the experiment to Firebase and waiting for data...
Collected experimental data.

=== DEBUG: Firebase returned 1 items ===
=== DEBUG: Parsed payload type: <class 'list'> ===
=== DEBUG: Using payload directly as trials list (4 items) ===
=== DEBUG: Processing 4 trials ===
=== DEBUG: Extracted 4 valid trials ===

✓ Successfully collected 4 trials from Firebase
Preprocessed experimental data: 4 rows.
```

## Still Having Issues?

1. **Enable more detailed logging**: Edit autora_workflow.py and add more print statements
2. **Check Firebase logs**: Go to Firebase Console → Functions → Logs (if using Cloud Functions)
3. **Test locally**: Use development mode to bypass Firebase and test the experiment directly
4. **Verify data manually**: Check Firestore Database in Firebase Console to see actual data structure

## Contact

If you've followed all steps and still have issues, please provide:
1. The debug output from running the workflow
2. A screenshot of your Firestore Database collections
3. Any error messages from browser console (F12) when running the experiment
4. The `.env` file configuration (without sensitive data)
