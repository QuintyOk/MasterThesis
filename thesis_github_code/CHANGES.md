# Code-cleaning summary

The scripts retain the original analytical operations and execution order. The cleanup focused on readable formatting, concise documentation, import organisation, and clearer diagnostic output.

## SCE scripts

### `01_clean_sce.py`

- Added a module docstring describing the cleaning scope and confidential-data requirement.
- Grouped the cleaning steps around metadata removal, date conversion, preview removal, completion checks, campus filtering, and fieldwork timing.
- Wrapped long filters and diagnostic statements for readability.
- Preserved every original cleaning rule and output filename.

### `02_format_sce.py`

- Added a module docstring and docstrings for all helper functions.
- Organised comments around mode profiles, availability, experiment assignment, block assignment, task expansion, choice reconstruction, Ngene merging, and parking follow-up variables.
- Reformatted long expressions, tables, and checks.
- Added context for the single hard-coded response exclusion.
- Preserved the original transformations, response exclusion, and output filename.

### `03_describe_sce.py`

- Reordered imports into standard-library and third-party groups.
- Added a module docstring and helper-function docstrings.
- Grouped the analysis around modal split, commute characteristics, availability, vanpool results, experiments, parking-rights responses, and distance bands.
- Added a warning that the open-text Word output contains ResponseIds and must remain private.
- Preserved every original analysis and generated output.

### `05_estimate_sce_base_choice_mnl.py`

- Added a module docstring and clearer documentation for model preparation, utility specification, estimation, fitted probabilities, policy simulations, and scenario combinations.
- Added concise docstrings to the simulation helpers.
- Consolidated imports and wrapped long model expressions.
- Preserved the original MNL specification and simulation logic.

### `06_estimate_sce_final_choice_mnl.py`

- Applied the same model-code cleanup as the base-choice script.
- Updated diagnostic wording and the Biogeme model label so the output identifies the final-choice model correctly.
- Preserved the original final-choice specification and simulation logic.

### `07_estimate_sce_give_up_parking_logit.py`

- Added a module docstring and comments for preparation, estimation, fitted probabilities, and policy simulations.
- Updated the Biogeme model label and diagnostic wording.
- Added a prominent warning about the original Yes and No alternative coding.
- Preserved the original coding and model calculations.

## PVE scripts

### `01_clean_pve.py`

- Added a module docstring describing the cleaning scope and confidential-data requirement.
- Grouped the cleaning steps around metadata removal, date conversion, fieldwork timing, completion checks, and campus filtering.
- Wrapped long filters and diagnostic statements.
- Preserved every original cleaning rule and output filename.

### `02_format_pve.py`

- Added a module docstring and docstrings for the mode-profile and policy-selection helpers.
- Organised comments around respondent characteristics, mode availability, TFA rankings, PVE outputs, policy packages, working-from-home responses, and open-text variables.
- Reformatted long expressions and added context for the hard-coded response exclusion.
- Preserved every original transformation and output filename.

### `03_describe_and_correlate_pve.py`

- Reordered imports into standard-library and third-party groups.
- Added a module docstring and docstrings for ranking validation, bootstrap intervals, and correlation calculations.
- Organised the descriptive analysis and respondent-level Spearman correlation analysis into clear sections.
- Preserved the random seed, 10,000 bootstrap samples, confidence level, and correlation calculations.

### `04_analyse_pve.py`

- Reordered imports and added a module docstring.
- Added docstrings for dictionary parsing, package flattening, experiment assignment, subgroup analysis, and working-from-home scoring.
- Organised comments around TFA rankings, policy selection, packages, subgroup analysis, car reduction, and working-from-home effects.
- Wrapped long logical conditions and grouped calculations.
- Preserved the full-sample and subgroup analyses.
