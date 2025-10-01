import pandas as pd

def trial_list_to_experiment_data(trial_sequence):
    """
    Parse a trial sequence (from jsPsych) into dependent and independent variables

    independent variables: dots_left, dots_right
    dependent: accuracy
    """

    # define dictionary to store the results
    results_dict = {
        'dots_left': [],
        'dots_right': [],
        'accuracy': []
    }
    for trial in trial_sequence:
        # Filter experiment events that are not displaying the dots
        if trial['trial_type'] != 'rok':
            continue

        # Filter trials without reaction time
        if 'rt' not in trial or trial['rt'] is None: # key_response
            continue

        # the number of dots is equivalent to the number of oobs (oriented objects) as set in the SweetBean script
        dots_left = trial['number_of_oobs'][0] # oriented objects
        dots_right = trial['number_of_oobs'][1]
        choice = trial['key_press']

        # compute accuracy
        if dots_left == dots_right and choice == 'y' or dots_left != dots_right and choice == 'n':
            accuracy = 1
        else:
            accuracy = 0

        # add results to dictionary
        results_dict['dots_left'].append(int(dots_left))
        results_dict['dots_right'].append(int(dots_right))
        results_dict['accuracy'].append(float(accuracy))

    # convert dictionary to pandas dataframe
    experiment_data = pd.DataFrame(results_dict)

    return experiment_data


def digit_memory_trial_list_to_experiment_data(trial_sequence):
    """
    Parse a digit memory trial sequence into dependent and independent variables
    
    independent variables: n_digits
    dependent variables: accuracy
    """
    
    print(f"\n=== DEBUG: digit_memory_trial_list_to_experiment_data called with {len(trial_sequence) if isinstance(trial_sequence, list) else 'non-list'} items ===")
    
    # define dictionary to store the results
    results_dict = {
        'n_digits': [],
        'accuracy': []
    }
    
    for idx, trial in enumerate(trial_sequence):
        # Handle different possible trial data structures
        n_digits = None
        correct = None
        
        if idx < 3:  # Only print details for first few trials to avoid spam
            print(f"  Trial {idx}: {trial}")
        
        # Try to extract n_digits from various possible locations
        if 'n_digits' in trial:
            n_digits = trial['n_digits']
        elif 'data' in trial and isinstance(trial['data'], dict) and 'n_digits' in trial['data']:
            n_digits = trial['data']['n_digits']
        
        # Try to extract correct/accuracy from various possible locations
        if 'correct' in trial:
            correct = trial['correct']
        elif 'data' in trial and isinstance(trial['data'], dict) and 'correct' in trial['data']:
            correct = trial['data']['correct']
        elif 'accuracy' in trial:
            correct = trial['accuracy']
        
        # Only add to results if we have both n_digits and correct values
        if n_digits is not None and correct is not None:
            # Ensure proper data types
            try:
                results_dict['n_digits'].append(int(n_digits))
                results_dict['accuracy'].append(float(1.0 if correct else 0.0))
                if idx < 3:
                    print(f"    ✓ Extracted: n_digits={n_digits}, correct={correct}")
            except (ValueError, TypeError) as e:
                print(f"Warning: Could not parse trial data: n_digits={n_digits}, correct={correct}, error={e}")
                continue
        else:
            if idx < 3:
                print(f"    ✗ Missing data: n_digits={n_digits}, correct={correct}")
    
    print(f"=== DEBUG: Extracted {len(results_dict['n_digits'])} valid trials ===")
    
    # convert dictionary to pandas dataframe
    experiment_data = pd.DataFrame(results_dict)
    
    return experiment_data