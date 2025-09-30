// testing_zone/src/design/main.js
import { initJsPsych } from 'jspsych';
import 'jspsych/css/jspsych.css';
import 'sweetbean/dist/style/main.css';
import 'sweetbean/dist/style/bandit.css';
import * as SweetBeanRuntime from 'sweetbean/dist/runtime';

import htmlKeyboardResponse from '@jspsych/plugin-html-keyboard-response';
import surveyHtmlForm from '@jspsych/plugin-survey-html-form';

// Expose jsPsych + plugins globally
global.initJsPsych = initJsPsych;
global.jsPsychHtmlKeyboardResponse = htmlKeyboardResponse;
global.jsPsychSurveyHtmlForm = surveyHtmlForm;

// Expose SweetBean runtime classes
Object.entries(SweetBeanRuntime).forEach(([k, v]) => { global[k] = v; });

/**
 * The AutoRA website shell calls:
 *   main(participant_id, condition)
 * We eval the JS experiment code attached to the condition doc and run it.
 * Must return a JSON string with observations.
 */
const main = async (participant_id, condition) => {
  // EXACTLY like in the tutorial:
  const observation = await eval(condition['experiment_code'] + "\nrunExperiment();");

  // Our SweetBean code puts rows on window.__autora_observation__
  const rows = (global.window && window.__autora_observation__) || observation || [];
  return JSON.stringify(rows);
};

export default main;
