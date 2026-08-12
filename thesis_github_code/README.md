# ASML mobility policy thesis code

This repository contains the analysis scripts and Qualtrics survey instruments used for the master thesis *One Commute, Multiple Perspectives*.

The study combines a stated choice experiment with a Participatory Value Evaluation to compare predicted modal-shift effects, employee acceptability, and possible working-from-home responses to employer mobility policies.

## Repository structure

```text
sce/
    01_clean_sce.py
    02_format_sce.py
    03_describe_sce.py
    05_estimate_sce_base_choice_mnl.py
    06_estimate_sce_final_choice_mnl.py
    07_estimate_sce_give_up_parking_logit.py

pve/
    01_clean_pve.py
    02_format_pve.py
    03_describe_and_correlate_pve.py
    04_analyse_pve.py

survey_instruments/
    sce_survey.qsf
    pve_acceptability_survey.qsf

data/
    README.md
```

## Execution order

Run the SCE scripts in numerical order. Run the PVE scripts in numerical order. The model scripts use the formatted SCE dataset created by `02_format_sce.py`.

The scripts retain the original relative data paths used during the thesis. Most paths use Windows-style backslashes. Update the paths before running the scripts on macOS or Linux.

## Data availability

The employee-level survey data are confidential and are excluded from this repository. The expected filenames are listed in `data/README.md`. For reproducibility, the two QSF survey instrument files can be uploaded directly to Qualtrics to recreate the surveys and collect a new dataset.


## Reproducibility note

The source code was cleaned for publication without changing the analytical statements or calculations.

