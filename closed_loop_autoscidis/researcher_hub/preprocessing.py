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


def digit_memory_to_experiment_data(trial_sequence):
    """
    Parse a digit memory trial sequence into dependent and independent variables
    
    independent variable: n_digits
    dependent: accuracy (0 or 1)
    """
    results_dict = {
        'n_digits': [],
        'accuracy': []
    }
    
    for trial in trial_sequence:
        # Only process trials that have the required fields
        if 'n_digits' not in trial or 'correct' not in trial:
            continue
        
        n_digits = int(trial['n_digits'])
        correct = bool(trial['correct'])
        
        results_dict['n_digits'].append(n_digits)
        results_dict['accuracy'].append(1.0 if correct else 0.0)
    
    experiment_data = pd.DataFrame(results_dict)
    return experiment_data