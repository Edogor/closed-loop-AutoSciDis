# Data Collection Improvements for Researcher Hub

## Summary of Changes

This document describes the improvements made to correctly collect and handle experimental data in the researcher hub, ensuring that both the theorist and experimentalist can effectively work with the collected data.

## Key Improvements

### 1. **Enhanced Data Preprocessing** (`preprocessing.py`)

Added a new robust preprocessing function: `digit_memory_trial_list_to_experiment_data()`

**Features:**
- Handles multiple data structures that might come from Firebase
- Extracts `n_digits` and `correct` values from various locations in trial data
- Robust error handling for malformed data
- Proper data type conversion (int for n_digits, float for accuracy)

**Example usage:**
```python
from preprocessing import digit_memory_trial_list_to_experiment_data

trials = [
    {'n_digits': 3, 'correct': True},
    {'n_digits': 4, 'correct': False},
    # Can also handle nested structures like:
    {'data': {'n_digits': 5, 'correct': True}}
]

processed_data = digit_memory_trial_list_to_experiment_data(trials)
# Returns: DataFrame with columns ['n_digits', 'accuracy']
```

### 2. **Data Accumulation** (`autora_workflow.py`)

Modified `runner_on_state()` to properly accumulate data across experimental cycles instead of replacing it.

**Before:** Each cycle would overwrite previous data
**After:** Each cycle adds new data to existing data

**Key changes:**
- Added `experiment_data` parameter to `runner_on_state`
- Uses `pd.concat()` to combine new and existing data
- Maintains data integrity across cycles
- Provides clear logging of data accumulation

### 3. **Comprehensive Data Analysis and Export**

Added functions for analyzing and saving collected data:

#### `analyze_collected_data(experiment_data)`
- Provides summary statistics
- Shows per-condition results
- Checks data sufficiency for analysis
- Identifies conditions that need more data

#### `save_data_with_metadata(experiment_data, models, metadata)`
- Saves experimental data with timestamps
- Includes comprehensive metadata about the experiment
- Creates both data files (.csv) and metadata files (.json)

### 4. **Enhanced Error Handling**

- Graceful handling of malformed Firebase data
- Proper type checking and conversion
- Informative warning messages for debugging
- Fallback behavior for missing data fields

## Data Flow

The improved workflow follows this sequence:

1. **Experiment Generation**: JavaScript experiments are created for each condition
2. **Firebase Execution**: Experiments run on Firebase with human participants
3. **Data Collection**: Raw trial data is collected from Firebase
4. **Preprocessing**: `digit_memory_trial_list_to_experiment_data()` converts raw data to structured format
5. **Accumulation**: New data is combined with existing data from previous cycles
6. **Analysis**: Theorist uses accumulated data to fit models
7. **Planning**: Experimentalist uses models to select next conditions
8. **Export**: Data and metadata are saved for researcher access

## File Structure

```
researcher_hub/
├── autora_workflow.py          # Main workflow with improvements
├── preprocessing.py            # Enhanced preprocessing functions
├── experiment_digit_memory.py  # Experiment generation (unchanged)
└── (generated files)
    ├── digit_memory_experiment_TIMESTAMP.csv    # Raw experimental data
    ├── digit_memory_metadata_TIMESTAMP.json     # Experiment metadata
    └── model_fits_digit_memory.png              # Visualization
```

## Benefits for Researchers

1. **Reliable Data Collection**: Robust preprocessing handles various data formats from Firebase
2. **Complete Data History**: All experimental data is preserved and accumulated across cycles
3. **Easy Analysis**: Built-in analysis functions provide immediate insights
4. **Reproducibility**: Comprehensive metadata enables experiment reproduction
5. **Interoperability**: Standardized data format works seamlessly with theorist and experimentalist components

## Testing

The implementation has been thoroughly tested with:
- Various data structures from Firebase
- Multi-cycle data accumulation
- Integration with theorist (model fitting)
- Data export and import
- Error handling for malformed data

All tests pass, confirming that the data collection workflow now correctly supports the full research pipeline.

## Usage

To use the improved workflow:

1. Ensure Firebase credentials are properly configured
2. Run `autora_workflow.py` 
3. Data will be automatically collected, preprocessed, and accumulated
4. Final data and analysis will be saved automatically
5. Use the generated CSV files for further analysis or visualization

The improvements ensure that researchers can reliably collect high-quality experimental data that integrates seamlessly with AutoRA's theorist and experimentalist components.