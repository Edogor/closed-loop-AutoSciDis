## Create an autora-workflow

### Setting up an virtual environment

Install this in an environment using your chosen package manager. In this example we are using virtualenv

Install:

- python (3.8 or greater): https://www.python.org/downloads/
- virtualenv: https://virtualenv.pypa.io/en/latest/installation.html

Install the Prolific Recruitment Manager as part of the autora package:

Change to the directory of the autora_workflow. Here, we define the autora workflow

```shell
cd researcher_environment
```

### Create a virtual environment

```shell
virtualenv venv
```

### Install dependencies

Install the requirements:

```shell
pip install -r requirements.txt
```

### Verify Firebase Setup

Before running the workflow, verify that your Firebase configuration is correct:

```shell
python verify_firebase_setup.py
```

This will check:
- Firebase credentials file exists and is valid
- Required Python packages are installed
- Experiment generation works correctly
- Data preprocessing works correctly

If all checks pass, you can proceed to run the workflow.

### Test Data Pipeline (Optional)

To test the data processing pipeline without Firebase or participants:

```shell
python test_pipeline.py
```

This generates mock data and verifies:
- Mock data generation
- JSON parsing
- Data preprocessing
- Data types
- Edge case handling

Useful for understanding how data flows through the system.

### Write your code

The autora_workflow.py file shows a basic example on how to run a closed loop autora experiment. Navigate [here](https://autoresearch.github.io/autora/) for more advanced options.

### Troubleshooting

If you encounter issues with data collection:

1. Run the verification script: `python verify_firebase_setup.py`
2. Check the detailed debugging guide: `DEBUGGING_FIREBASE.md`
3. Look at the debug output when running `autora_workflow.py`

Common issues:
- **No data collected**: Make sure experiments are actually being completed by participants
- **Timeout errors**: The timeout is set to 300 seconds (5 minutes) - adjust if needed
- **Firebase connection**: Verify credentials in `firebase-service-account.json`
