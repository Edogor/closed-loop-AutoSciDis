#!/usr/bin/env python3
"""
Firebase Connection Verification Script

This script checks if your Firebase configuration is correct and the connection works.
Run this before running autora_workflow.py to verify your setup.
"""

import json
import pathlib
import sys
from typing import Dict, Any

def check_credentials_file() -> bool:
    """Check if firebase-service-account.json exists and has required fields"""
    print("\n" + "="*70)
    print("1️⃣  Checking Firebase Credentials File")
    print("="*70)
    
    cred_path = pathlib.Path(__file__).with_name("firebase-service-account.json")
    
    if not cred_path.exists():
        print("❌ FAILED: firebase-service-account.json not found!")
        print(f"   Expected location: {cred_path}")
        print("\n📝 To fix:")
        print("   1. Go to Firebase Console: https://console.firebase.google.com/")
        print("   2. Select your project")
        print("   3. Go to Project Settings → Service Accounts")
        print("   4. Click 'Generate new private key'")
        print("   5. Save the file as firebase-service-account.json in:")
        print(f"      {cred_path.parent}")
        return False
    
    try:
        with open(cred_path, 'r', encoding='utf-8') as f:
            creds = json.load(f)
    except Exception as e:
        print(f"❌ FAILED: Could not parse firebase-service-account.json: {e}")
        return False
    
    required_fields = [
        "type", "project_id", "private_key_id", "private_key", 
        "client_email", "client_id", "auth_uri", "token_uri"
    ]
    
    missing_fields = [field for field in required_fields if field not in creds]
    
    if missing_fields:
        print(f"❌ FAILED: Missing required fields: {', '.join(missing_fields)}")
        return False
    
    print(f"✅ PASSED: Credentials file found and valid")
    print(f"   Project ID: {creds.get('project_id')}")
    print(f"   Client Email: {creds.get('client_email')}")
    
    return True

def check_firebase_imports() -> bool:
    """Check if required Firebase packages are installed"""
    print("\n" + "="*70)
    print("2️⃣  Checking Firebase Package Imports")
    print("="*70)
    
    try:
        from autora.experiment_runner.firebase_prolific import firebase_runner
        print("✅ PASSED: autora.experiment_runner.firebase_prolific imported successfully")
        return True
    except ImportError as e:
        print(f"❌ FAILED: Could not import firebase_runner: {e}")
        print("\n📝 To fix:")
        print("   pip install -r requirements.txt")
        return False

def check_experiment_modules() -> bool:
    """Check if experiment modules are working"""
    print("\n" + "="*70)
    print("3️⃣  Checking Experiment Modules")
    print("="*70)
    
    try:
        from experiment_digit_memory import trial_sequence, stimulus_sequence
        print("✅ PASSED: experiment_digit_memory imported successfully")
        
        # Test generation
        trials = trial_sequence(number_of_trials=2, n_levels=[3])
        if len(trials) != 2:
            print(f"⚠️  WARNING: Expected 2 trials, got {len(trials)}")
            return False
        
        js_code = stimulus_sequence(trials)
        if len(js_code) < 1000:
            print(f"⚠️  WARNING: Generated JS code seems too short ({len(js_code)} chars)")
            return False
        
        print(f"✅ PASSED: Generated {len(trials)} trials, {len(js_code)} chars of JS code")
        return True
        
    except Exception as e:
        print(f"❌ FAILED: Error with experiment modules: {e}")
        return False

def check_preprocessing() -> bool:
    """Check if preprocessing module works"""
    print("\n" + "="*70)
    print("4️⃣  Checking Preprocessing Module")
    print("="*70)
    
    try:
        from preprocessing import digit_memory_trial_list_to_experiment_data
        print("✅ PASSED: preprocessing module imported successfully")
        
        # Test with mock data
        test_data = [
            {"n_digits": 3, "correct": True},
            {"n_digits": 5, "correct": False},
        ]
        
        result = digit_memory_trial_list_to_experiment_data(test_data)
        
        if len(result) != 2:
            print(f"⚠️  WARNING: Expected 2 rows, got {len(result)}")
            return False
        
        if list(result.columns) != ["n_digits", "accuracy"]:
            print(f"⚠️  WARNING: Expected columns [n_digits, accuracy], got {list(result.columns)}")
            return False
        
        print(f"✅ PASSED: Preprocessing correctly converted {len(test_data)} trials to {len(result)} rows")
        return True
        
    except Exception as e:
        print(f"❌ FAILED: Error with preprocessing: {e}")
        import traceback
        traceback.print_exc()
        return False

def print_firebase_check_instructions():
    """Print instructions for manually checking Firebase"""
    print("\n" + "="*70)
    print("5️⃣  Manual Firebase Checks")
    print("="*70)
    print("\n📋 Please manually verify the following:")
    print()
    print("1. Firebase Console Access:")
    print("   → Go to: https://console.firebase.google.com/")
    print("   → Can you access your project?")
    print()
    print("2. Firestore Database:")
    print("   → In Firebase Console, go to Firestore Database")
    print("   → Is Firestore enabled?")
    print("   → Can you see collections?")
    print()
    print("3. Testing Zone Deployment:")
    print("   → In Firebase Console, go to Hosting")
    print("   → Is the testing zone deployed?")
    print("   → Note the URL (e.g., https://your-project.web.app)")
    print()
    print("4. Test the deployed app:")
    print("   → Open the testing zone URL in your browser")
    print("   → Does it load without errors?")
    print("   → Check browser console (F12) for JavaScript errors")
    print()

def main():
    print("\n" + "="*70)
    print("🔧 Firebase Setup Verification")
    print("="*70)
    print("\nThis script checks if your Firebase setup is correct.")
    print("Run this before running autora_workflow.py")
    
    checks = [
        ("Credentials File", check_credentials_file),
        ("Firebase Imports", check_firebase_imports),
        ("Experiment Modules", check_experiment_modules),
        ("Preprocessing Module", check_preprocessing),
    ]
    
    results = {}
    for name, check_func in checks:
        try:
            results[name] = check_func()
        except Exception as e:
            print(f"\n❌ UNEXPECTED ERROR in {name}: {e}")
            import traceback
            traceback.print_exc()
            results[name] = False
    
    print_firebase_check_instructions()
    
    # Summary
    print("\n" + "="*70)
    print("📊 Summary")
    print("="*70)
    
    passed = sum(1 for v in results.values() if v)
    total = len(results)
    
    for name, result in results.items():
        status = "✅ PASSED" if result else "❌ FAILED"
        print(f"   {status}: {name}")
    
    print(f"\n   Score: {passed}/{total} checks passed")
    
    if passed == total:
        print("\n✅ All automated checks passed!")
        print("   You can now run autora_workflow.py")
        print("\n   Don't forget to:")
        print("   1. Deploy the testing zone (if not already done)")
        print("   2. Have participants complete experiments OR test manually")
        print("   3. Check the debugging output when running the workflow")
        return 0
    else:
        print("\n❌ Some checks failed!")
        print("   Please fix the issues above before running autora_workflow.py")
        print("\n   For detailed troubleshooting, see:")
        print("   → DEBUGGING_FIREBASE.md")
        return 1

if __name__ == "__main__":
    sys.exit(main())
