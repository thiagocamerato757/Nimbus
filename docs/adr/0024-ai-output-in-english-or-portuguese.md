# AI output is in English or Brazilian Portuguese; the interface is English

Coaches read explanations best in their own language, while draft jargon is largely English anyway. Scouting Reports, "Ask the report" answers and copilot explanations are written in English or Brazilian Portuguese, set per Workspace and changeable per report. The interface ships in English only, but every UI string goes through a translation key from the start, so translating it later is not a refactor.

- Character, Team and Player names are never translated. Each Title profile lists, per language, the game terms that stay as players say them (in pt-BR: pick, ban, flex, counter, First Selection, side names and so on); the list is given to the LLM and used by Observation templates.
- Each language needs its own Observation templates and spelled-out-number check.
- Changing a saved report's language re-renders Observations from the same statistics but rewrites the Interpretations, which may emphasise different things. The analyst is warned first ("interpretations will be rewritten; statistics won't change") and the previous version is kept.

The mechanism is built with the first language, English; pt-BR follows right after the MVP as data files only.

## Considered Options

- English only: cheaper, but harder to read during a series for Portuguese-speaking staff.
- Both languages across the whole interface: left as a later translation task.
