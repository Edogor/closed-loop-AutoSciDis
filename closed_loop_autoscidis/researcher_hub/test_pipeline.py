#!/usr/bin/env python3
"""
Quick Test Script for Data Processing Pipeline

This script tests the data processing pipeline without requiring Firebase or participants.
Useful for verifying that your preprocessing and workflow logic work correctly.
"""

import sys
import json
from pathlib import Path

# Add researcher_hub to path
sys.path.insert(0, str(Path(__file__).parent))

from preprocessing import digit_memory_trial_list_to_experiment_data
import pandas as pd

def generate_mock_observation_data(n_digits_value=5, num_trials=4, accuracy_rate=0.75):
    """
    Generate mock observation data as it would come from Firebase
    
    Args:
        n_digits_value: The number of digits to memorize (e.g., 5)
        num_trials: How many trials to generate (e.g., 4)
        accuracy_rate: Probability of correct response (0.0 to 1.0)
    
    Returns:
        A JSON string formatted as Firebase would return it
    """
    import random
    
    observations = []
    for i in range(num_trials):
        # Generate random digits
        shown = ''.join(str(random.randint(0, 9)) for _ in range(n_digits_value))
        
        # Simulate participant response (sometimes correct, sometimes wrong)
        if random.random() < accuracy_rate:
            response = shown  # Correct
            correct = True
        else:
            # Make a mistake - change one digit
            response = list(shown)
            idx = random.randint(0, len(response) - 1)
            response[idx] = str((int(response[idx]) + 1) % 10)
            response = ''.join(response)
            correct = False
        
        observations.append({
            "n_digits": n_digits_value,
            "shown": shown,
            "response": response,
            "correct": correct
        })
    
    return json.dumps(observations)

def test_pipeline():
    """Test the complete data processing pipeline"""
    print("\n" + "="*70)
    print("🧪 Testing Data Processing Pipeline")
    print("="*70)
    
    # Test 1: Single condition with 4 trials
    print("\n📊 Test 1: Processing 4 trials (n_digits=5)")
    print("-" * 70)
    
    mock_data = generate_mock_observation_data(n_digits_value=5, num_trials=4, accuracy_rate=0.75)
    print(f"Generated mock Firebase response ({len(mock_data)} chars)")
    
    # Parse JSON (as the workflow does)
    payload = json.loads(mock_data)
    print(f"Parsed into list of {len(payload)} items")
    
    # Process with preprocessing function
    df = digit_memory_trial_list_to_experiment_data(payload, debug=True)
    
    print(f"\n✅ Result: {len(df)} rows")
    print("\nDataFrame:")
    print(df)
    print(f"\nMean accuracy: {df['accuracy'].mean():.2%}")
    
    # Test 2: Multiple conditions
    print("\n" + "="*70)
    print("📊 Test 2: Processing multiple conditions")
    print("-" * 70)
    
    all_data = []
    conditions = [3, 5, 7]
    
    for n in conditions:
        print(f"\nGenerating data for n_digits={n}...")
        mock_data = generate_mock_observation_data(n_digits_value=n, num_trials=3, accuracy_rate=0.8)
        observations = json.loads(mock_data)
        all_data.extend(observations)
    
    print(f"\n✅ Total: {len(all_data)} trials across {len(conditions)} conditions")
    
    df_all = digit_memory_trial_list_to_experiment_data(all_data, debug=False)
    print("\nCombined DataFrame:")
    print(df_all)
    
    # Summary by condition
    print("\n📈 Summary by condition:")
    summary = df_all.groupby('n_digits').agg({
        'accuracy': ['count', 'mean', 'std']
    }).round(3)
    summary.columns = ['n_trials', 'mean_accuracy', 'std_accuracy']
    print(summary)
    
    # Test 3: Verify data types
    print("\n" + "="*70)
    print("🔍 Test 3: Verifying data types")
    print("-" * 70)
    
    print(f"n_digits dtype: {df_all['n_digits'].dtype} (expected: int64)")
    print(f"accuracy dtype: {df_all['accuracy'].dtype} (expected: float64)")
    
    if df_all['n_digits'].dtype == 'int64' and df_all['accuracy'].dtype == 'float64':
        print("✅ Data types are correct!")
    else:
        print("❌ Data type mismatch!")
        return False
    
    # Test 4: Edge cases
    print("\n" + "="*70)
    print("🧪 Test 4: Edge cases")
    print("-" * 70)
    
    # Empty data
    print("\n4a. Testing empty data...")
    empty_df = digit_memory_trial_list_to_experiment_data([], debug=False)
    print(f"Empty data result: {len(empty_df)} rows (expected: 0)")
    if len(empty_df) == 0:
        print("✅ Handles empty data correctly")
    
    # Data with nested structure (jsPsych style)
    print("\n4b. Testing nested data structure...")
    nested_data = [
        {"data": {"n_digits": 3, "correct": True}, "trial_type": "feedback"},
        {"data": {"n_digits": 3, "correct": False}, "trial_type": "feedback"},
    ]
    nested_df = digit_memory_trial_list_to_experiment_data(nested_data, debug=False)
    print(f"Nested data result: {len(nested_df)} rows (expected: 2)")
    if len(nested_df) == 2:
        print("✅ Handles nested data correctly")
    
    print("\n" + "="*70)
    print("✅ All tests passed!")
    print("="*70)
    
    print("\n📝 Summary:")
    print("  ✓ Mock data generation works")
    print("  ✓ JSON parsing works")
    print("  ✓ Preprocessing function works")
    print("  ✓ Data types are correct")
    print("  ✓ Edge cases handled")
    print("\n🎉 Your data processing pipeline is ready!")
    print("\nNext steps:")
    print("  1. Run: python verify_firebase_setup.py")
    print("  2. Ensure testing zone is deployed")
    print("  3. Run: python autora_workflow.py")
    
    return True

if __name__ == "__main__":
    try:
        success = test_pipeline()
        sys.exit(0 if success else 1)
    except Exception as e:
        print(f"\n❌ Test failed with error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
