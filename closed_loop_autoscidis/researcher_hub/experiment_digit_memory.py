# researcher_hub/experiment_digit_memory.py
from __future__ import annotations
from typing import List, Dict, Any

# ---- (Optional) SweetPea for trial sequencing ----
# We try to use SweetPea to counterbalance n_digits; if it misbehaves, we fall back.
try:
    from sweetpea import Factor, CrossBlock, synthesize_trials  # modern API
    _HAS_SWEETPEA = True
except Exception:
    _HAS_SWEETPEA = False


def _fill(template: str, **kw) -> str:
    """Simple template substitution: %%key%% -> value."""
    out = template
    for k, v in kw.items():
        out = out.replace(f"%%{k}%%", str(v))
    return out


# -----------------------------
# TRIAL SEQUENCE (balanced)
# -----------------------------
def trial_sequence(number_of_trials: int = 12,
                   n_levels: List[int] = (3, 5, 7, 9)) -> List[Dict[str, Any]]:
    """
    Return a counterbalanced list of trials, each with n_digits ∈ n_levels.
    Tries SweetPea; if output is oddly shaped or SAT fails, falls back to a simple balanced generator.
    """
    # SweetPea path
    if _HAS_SWEETPEA:
        try:
            n_digits = Factor("n_digits", [str(n) for n in n_levels])
            block = CrossBlock(design=[n_digits], crossing=[n_digits], constraints=[])
            trials = synthesize_trials(block, samples=number_of_trials)

            def extract_one(v):
                if isinstance(v, (list, tuple)):
                    return int(v[0]) if v else 3
                return int(v)
            seq = [{"n_digits": extract_one(t["n_digits"])} for t in trials]
            # sanity checks
            if len(seq) != number_of_trials or any(d["n_digits"] not in n_levels for d in seq):
                raise ValueError("SweetPea produced unexpected structure.")
            return seq
        except Exception as e:
            print(f"[trial_sequence] SweetPea unavailable or malformed output ({e}). Falling back.")

    # Fallback: simple balanced cycling over levels
    import random
    levels = list(int(x) for x in n_levels)
    reps = (number_of_trials + len(levels) - 1) // len(levels)  # ceil
    arr = (levels * reps)[:number_of_trials]
    random.shuffle(arr)
    return [{"n_digits": int(x)} for x in arr]


# -----------------------------
# STIMULUS SEQUENCE (plain JS)
# -----------------------------
def stimulus_sequence(trials: List[Dict[str, Any]]) -> str:
    """
    Return a JS function string named runExperiment() that the Testing Zone evals.
    Requires these globals to be available in testing_zone:
      - initJsPsych
      - jsPsychHtmlKeyboardResponse
      - jsPsychSurveyHtmlForm
    """
    parts: List[str] = []

    # Header + intro screen
    header = r"""
async function runExperiment(){
  const jsPsych = initJsPsych();
  const timeline = [];

  function randDigits(k){
    let s = '';
    for(let i=0;i<k;i++){ s+=Math.floor(Math.random()*10).toString(); }
    return s;
  }

  // Intro
  timeline.push({
    type: jsPsychHtmlKeyboardResponse,
    stimulus: `
      <div style="text-align:center">
        <h2>Digit Memory</h2>
        <p>Du siehst eine Ziffernfolge für 5 Sekunden und gibst sie danach ein.</p>
        <p>Drücke eine beliebige Taste, um zu beginnen.</p>
      </div>`,
    choices: "ALL_KEYS"
  });

  // Global list to collect feedback-phase observations
  if (typeof window !== "undefined") {
    window.__digitMemoryObs = [];
  }
"""
    parts.append(header)

    # One block per trial
    for t in trials:
        n = int(t.get("n_digits", 5))
        block_template = r"""
  // --- Trial with n_digits = %%n%% ---
  // 1) DISPLAY: show random digits for 5 sec
  timeline.push({
    type: jsPsychHtmlKeyboardResponse,
    stimulus: () => {
      const shown = randDigits(%%n%%);
      return `<div style="text-align:center; font-size:40px; font-weight:bold">${shown}</div>`;
    },
    choices: "NO_KEYS",
    trial_duration: 5000,
    on_finish: (trial) => {
      const shown = trial.stimulus.match(/>\s*(\d+)\s*</)?.[1] || "";
      trial.data = Object.assign({}, trial.data, { phase:"display", n_digits: %%n%%, shown });
      if (typeof window !== "undefined") {
        window.__lastShown = shown;
        window.__lastNDigits = %%n%%;
      }
    }
  });

  // 2) RECALL: text input
  timeline.push({
    type: jsPsychSurveyHtmlForm,
    preamble: `<div style="text-align:center"><p>Bitte gib die Ziffern in der gleichen Reihenfolge ein.</p></div>`,
    html: `
      <div style="text-align:center">
        <input name="response" type="text" autocomplete="off" inputmode="numeric" pattern="[0-9]*" required
               style="font-size:20px;padding:8px 10px;width:100%;max-width:380px"/>
      </div>`,
    button_label: "Weiter",
    on_finish: (trial) => {
      const resp = trial.response?.response || "";
      const shown = (typeof window !== "undefined" && window.__lastShown) ? String(window.__lastShown) : "";

      // Normalisieren
      const clean = s => String(s).trim().replace(/\s+/g, "").replace(/[^0-9]/g, "");
      const respClean  = clean(resp);
      const shownClean = clean(shown);

      const correct = (respClean === shownClean);

      // Daten des Trials
      trial.data = Object.assign({}, trial.data, {
        phase: "feedback",
        n_digits: (typeof window !== "undefined" && window.__lastNDigits) ? window.__lastNDigits : undefined,
        shown: shownClean,
        response: respClean,
        correct
      });

      // **NEU**: Sofort in die globale Beobachtungsliste pushen (robust gegen vorzeitiges Beenden)
      if (typeof window !== "undefined") {
        window.__digitMemoryObs.push({
          n_digits: trial.data.n_digits,
          shown: trial.data.shown,
          response: trial.data.response,
          correct: trial.data.correct
        });
      }
    }
  });

  // 3) SHORT FEEDBACK
  timeline.push({
    type: jsPsychHtmlKeyboardResponse,
    stimulus: () => {
      const last = (typeof window !== "undefined" && window.__digitMemoryObs && window.__digitMemoryObs.length > 0)
                   ? window.__digitMemoryObs[window.__digitMemoryObs.length - 1]
                   : { correct: false };
      const msg = last.correct ? "Richtig!" : "Falsch.";
      const color = last.correct ? "green" : "red";
      return `<div style="text-align:center; font-size:30px; color:${color}; font-weight:bold">${msg}</div>`;
    },
    choices: "NO_KEYS",
    trial_duration: 1000
  });
"""
        parts.append(_fill(block_template, n=n))

    # Footer: end screen + return observations
    footer = r"""
  // End screen
  timeline.push({
    type: jsPsychHtmlKeyboardResponse,
    stimulus: `<div style="text-align:center"><h2>Fertig!</h2><p>Vielen Dank für deine Teilnahme.</p></div>`,
    choices: "NO_KEYS",
    trial_duration: 2000
  });

  await jsPsych.run(timeline);

  // Return observations (from global list, not from jsPsych.data)
  const obs = (typeof window !== "undefined" && window.__digitMemoryObs) ? window.__digitMemoryObs : [];
  return { trials: obs };
}
"""
    parts.append(footer)
    return "".join(parts)
