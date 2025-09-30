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
    """
    Tiny safe templater: replaces %%token%% with value.
    Keeps JS braces `{}` and `${}` intact (so we avoid Python f-string conflicts).
    """
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
                # SweetPea often returns ['5'] or Level objects; normalize to int
                if isinstance(v, list):
                    v = v[0]
                return int(str(v))

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
        <p><em>Drücke eine Taste, um zu starten.</em></p>
      </div>`,
    choices: "ALL_KEYS"
  });
"""
    parts.append(header)

    # Per-trial blocks
    for t in trials:
        n = int(t["n_digits"])
        block = _fill(r"""
  // --- Trial for n_digits = %%n%% ---
  // 1) DISPLAY digits (5s, no keys) — store 'shown' also globally for robust access
  timeline.push({
    type: jsPsychHtmlKeyboardResponse,
    stimulus: "",
    choices: "NO_KEYS",
    trial_duration: 5000,
    on_start: function(trial){
      const shown = randDigits(%%n%%);
      trial.stimulus = `<div style='font-size:48px;letter-spacing:.15em;text-align:center'>${shown}</div>`;
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
    data: { phase: "recall", n_digits: %%n%% }
  });

  // 3) FEEDBACK — robust comparison using global cache + normalization
  timeline.push({
    type: jsPsychHtmlKeyboardResponse,
    stimulus: "<div style='text-align:center'></div>",
    choices: "ALL_KEYS",
    trial_duration: 900,
    on_start: function(trial){
      const last = jsPsych.data.get().last(1).values()[0];

      // Antwort aus survey-html-form
      let resp = "";
      if (last && last.response) {
        if (typeof last.response.response === "string") {
          resp = last.response.response;
        } else {
          const vals = Object.values(last.response);
          resp = (vals.length ? String(vals[0]) : "");
        }
      }

      // shown aus globalem Cache
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
        if (!Array.isArray(window.__autora_observation__)) window.__autora_observation__ = [];
        window.__autora_observation__.push({
          n_digits: (typeof window.__lastNDigits !== "undefined") ? window.__lastNDigits : undefined,
          shown: shownClean,
          response: respClean,
          correct: !!correct
        });
      }

      trial.stimulus = `
        <div style='text-align:center'>
          <p>${correct ? "✅ Richtig!" : "❌ Falsch."}</p>
          <p style='color:#666;font-size:14px'>
            Gezeigt: <b>${shownClean}</b> &nbsp;|&nbsp; Eingabe: <b>${respClean}</b>
          </p>
        </div>`;
    }

      });
""", n=n)
        parts.append(block)

    # End screen + export observation for runner
    footer = r"""
  timeline.push({
    type: jsPsychHtmlKeyboardResponse,
    stimulus: `<div style="text-align:center"><p>Vielen Dank!</p><p><em>Drücke eine Taste zum Beenden.</em></p></div>`,
    choices: "ALL_KEYS",
    on_finish: function(trial){
      const rows = jsPsych.data.get()
        .filterCustom(d => d.phase === "feedback")
        .values()
        .map(d => ({ n_digits: d.n_digits, shown: d.shown, response: d.response, correct: !!d.correct }));
      window.__autora_observation__ = rows;
    }
  });

  await jsPsych.run(timeline);
  return window.__autora_observation__;
}
"""
    parts.append(footer)

    return "".join(parts)
