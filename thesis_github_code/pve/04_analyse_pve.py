"""Analyse PVE policy selections, acceptability rankings, and WFH responses.

The script reports full-sample and subgroup summaries of the four TFA-based
rankings, selected policy levels and packages, predicted car reduction, and
policy-specific working-from-home responses. It preserves the analytical order
and calculations used during the final thesis analysis."""

import ast

import numpy as np
import pandas as pd

# Load the formatted PVE dataset.
df = pd.read_excel(
    r"data/Access & Mobility Survey Acceptability Formatted Data.xlsx",
    engine="openpyxl",
)

pd.set_option('display.max_rows', None)

pd.set_option('display.max_columns', None)

pd.set_option('display.max_colwidth', None)

pd.set_option('display.width', None)

# Report the four TFA-based ranking dimensions for the full sample.
effectiveness_cols = [
    'parking_rights_effectiveness_rank',
    'parking_costs_effectiveness_rank',
    'parking_reservation_effectiveness_rank',
    'pr_reward_effectiveness_rank',
    'vp_taxi_effectiveness_rank',
    'vp_departure_effectiveness_rank'
]

print("\n# ================= EFFECTIVENESS =================")
print("\n# Average ranks")
print(df[effectiveness_cols].mean().sort_values())

print("\n# Value counts per policy")
for col in effectiveness_cols:
    print(f"\n## {col}")
    print(df[col].value_counts().sort_index())

fairness_cols = [
    'parking_rights_fairness_rank',
    'parking_costs_fairness_rank',
    'parking_reservation_fairness_rank',
    'pr_reward_fairness_rank',
    'vp_taxi_fairness_rank',
    'vp_departure_fairness_rank'
]

print("\n# ================= FAIRNESS =================")
print("\n# Average ranks")
print(df[fairness_cols].mean().sort_values())

print("\n# Value counts per policy")
for col in fairness_cols:
    print(f"\n## {col}")
    print(df[col].value_counts().sort_index())

convenience_cols = [
    'parking_rights_convenience_rank',
    'parking_costs_convenience_rank',
    'parking_reservation_convenience_rank',
    'pr_reward_convenience_rank',
    'vp_taxi_convenience_rank',
    'vp_departure_convenience_rank'
]

print("\n# ================= CONVENIENCE =================")
print("\n# Average ranks")
print(df[convenience_cols].mean().sort_values())

print("\n# Value counts per policy")
for col in convenience_cols:
    print(f"\n## {col}")
    print(df[col].value_counts().sort_index())

support_cols = [
    'parking_rights_support_rank',
    'parking_costs_support_rank',
    'parking_reservation_support_rank',
    'pr_reward_support_rank',
    'vp_taxi_support_rank',
    'vp_departure_support_rank'
]

print("\n# ================= SUPPORT =================")
print("\n# Average ranks")
print(df[support_cols].mean().sort_values())

print("\n# Value counts per policy")
for col in support_cols:
    print(f"\n## {col}")
    print(df[col].value_counts().sort_index())

# Parse and summarise the selected level of each PVE policy.
pve_cols = [
    'parking_rights_policy_pve',
    'parking_cost_policy_pve',
    'parking_reservation_policy_pve',
    'pr_reward_policy_pve',
    'vp_taxi_policy_pve',
    'vp_frequency_policy_pve'
]


def ensure_dict(x):
    """Parse a stored dictionary value when Excel returns it as text."""
    if isinstance(x, dict):
        return x
    try:
        return ast.literal_eval(str(x))
    except:
        return None

print("\n# ================= PVE POLICY SELECTION =================")

for col in pve_cols:
    df[col + "_dict"] = df[col].apply(ensure_dict)

    labels = df[col + "_dict"].apply(
        lambda x: x.get('label') if isinstance(x, dict) else np.nan
    )

    print(f"\n## {col}")

    counts = labels.value_counts()
    print(counts)

    print("\nProportions:")
    print((counts / counts.sum()).round(3))

# Count complete policy packages and summarise their predicted impact.
packages = df['policy_package'].apply(ensure_dict)


def flatten_package(d):
    """Convert a policy package to a hashable tuple for counting."""
    if not isinstance(d, dict):
        return None
    return tuple(sorted(
        (policy, details.get('label'))
        for policy, details in d.items()
    ))

packages_flat = packages.apply(flatten_package)

package_counts = packages_flat.value_counts()

print("\n# ================= POLICY PACKAGE COUNTS =================")
print(package_counts)

print("\n# ================= CAR REDUCTION (FULL SAMPLE) =================")

print(df['pve_car_reduction_pp'].describe())

print("\n# ================= PER EXPERIMENT GROUP =================")

# Reconstruct the six availability experiments used in the survey.
def assign_experiment(row):
    """Assign the availability experiment implied by a respondent profile."""
    if (
        row["bike_available"] == "No"
        and row["car_available"] == "No"
        and row["vanpool_available"] == "Yes"
    ):
        return "Experiment 1: Vanpool, PT"
    elif (
        row["bike_available"] == "Yes"
        and row["car_available"] == "No"
        and row["vanpool_available"] == "Yes"
    ):
        return "Experiment 2: Bike, Vanpool, PT"
    elif (
        row["bike_available"] == "No"
        and row["car_available"] == "Yes"
        and row["vanpool_available"] == "No"
    ):
        return "Experiment 3: Car, P+R, PT"
    elif (
        row["bike_available"] == "Yes"
        and row["car_available"] == "Yes"
        and row["vanpool_available"] == "No"
    ):
        return "Experiment 4: Bike, Car, P+R, PT"
    elif (
        row["bike_available"] == "No"
        and row["car_available"] == "Yes"
        and row["vanpool_available"] == "Yes"
    ):
        return "Experiment 5: Vanpool, Car, P+R, PT"
    elif (
        row["bike_available"] == "Yes"
        and row["car_available"] == "Yes"
        and row["vanpool_available"] == "Yes"
    ):
        return "Experiment 6: Bike, Vanpool, Car, P+R, PT"
    else:
        return "No Experiment Assigned"

df['experiment_group'] = df.apply(assign_experiment, axis=1)

print("Experiment group sizes: ")
print(df['experiment_group'].value_counts())


def run_analysis(sub_df, group_name):
    """Print policy selections and packages for one respondent group."""
    print(f"\n\n# ================= {group_name} =================")

    for col in pve_cols:
        labels = sub_df[col].apply(ensure_dict).apply(
            lambda x: x.get('label') if isinstance(x, dict) else np.nan
        )

        print(f"\n## {col}")
        counts = labels.value_counts()
        print(counts)

        print("\nProportions:")
        print((counts / counts.sum()).round(3))

    packages = sub_df['policy_package'].apply(ensure_dict)

    def flatten_package(d):
        """Convert a policy package to a hashable tuple for counting."""
        if not isinstance(d, dict):
            return None
        return tuple(sorted(
            (policy, details.get('label'))
            for policy, details in d.items()
        ))

    packages_flat = packages.apply(flatten_package)

    package_counts = packages_flat.value_counts()

    print("\n# Top 10 policy packages")
    print(package_counts.head(10))

for group in df['experiment_group'].unique():
    sub_df = df[df['experiment_group'] == group]
    run_analysis(sub_df, group)

print("\n# ================= CAR REDUCTION PER EXPERIMENT =================")

exp_stats = df.groupby('experiment_group')['pve_car_reduction_pp'].describe()
print(exp_stats)

print("\n# ================= PER DISTANCE GROUP =================")

for dist in df['commute_distance_km_range'].dropna().unique():
    sub_df = df[df['commute_distance_km_range'] == dist]
    run_analysis(sub_df, f"Distance group: {dist}")

print("\n# ================= CAR REDUCTION PER DISTANCE GROUP =================")

dist_stats = df.groupby('commute_distance_km_range')['pve_car_reduction_pp'].describe()
print(dist_stats)

print("\n# ================= PER WFH CAPABILITY GROUP =================")

for wfh in df['wfh_capabilities'].dropna().unique():
    sub_df = df[df['wfh_capabilities'] == wfh]
    run_analysis(sub_df, f"WFH group: {wfh}")

print("\n# ================= CAR REDUCTION PER WFH CAPABILITY =================")

wfh_stats = df.groupby('wfh_capabilities')['pve_car_reduction_pp'].describe()
print(wfh_stats)

# Repeat the ranking summaries for experiment, distance, and WFH groups.
def run_acceptability_analysis(sub_df, group_name):
    """Print all four acceptability rankings for one group."""

    print("\n" + "="*100)
    print(f"# ACCEPTABILITY ANALYSIS FOR: {group_name}")
    print("="*100)

    print(f"\n# Sample size: {len(sub_df)}")

    frameworks = {
        "EFFECTIVENESS": [
            'parking_rights_effectiveness_rank',
            'parking_costs_effectiveness_rank',
            'parking_reservation_effectiveness_rank',
            'pr_reward_effectiveness_rank',
            'vp_taxi_effectiveness_rank',
            'vp_departure_effectiveness_rank'
        ],
        "FAIRNESS": [
            'parking_rights_fairness_rank',
            'parking_costs_fairness_rank',
            'parking_reservation_fairness_rank',
            'pr_reward_fairness_rank',
            'vp_taxi_fairness_rank',
            'vp_departure_fairness_rank'
        ],
        "CONVENIENCE": [
            'parking_rights_convenience_rank',
            'parking_costs_convenience_rank',
            'parking_reservation_convenience_rank',
            'pr_reward_convenience_rank',
            'vp_taxi_convenience_rank',
            'vp_departure_convenience_rank'
        ],
        "SUPPORT": [
            'parking_rights_support_rank',
            'parking_costs_support_rank',
            'parking_reservation_support_rank',
            'pr_reward_support_rank',
            'vp_taxi_support_rank',
            'vp_departure_support_rank'
        ]
    }

    for framework_name, cols in frameworks.items():

        print("\n" + "-"*80)
        print(f"# FRAMEWORK: {framework_name}")
        print("-"*80)

        print("\n# Average ranks (lower = better):")
        print(sub_df[cols].mean().sort_values())

        print("\n# Value counts per policy:")
        for col in cols:
            print(f"\n## {col}")
            print(sub_df[col].value_counts().sort_index())

print("\n# ================= ACCEPTABILITY PER EXPERIMENT =================")

for group in df['experiment_group'].unique():
    sub_df = df[df['experiment_group'] == group]
    run_acceptability_analysis(sub_df, f"Experiment group: {group}")

print("\n# ================= ACCEPTABILITY PER DISTANCE =================")

for dist in df['commute_distance_km_range'].dropna().unique():
    sub_df = df[df['commute_distance_km_range'] == dist]
    run_acceptability_analysis(sub_df, f"Distance group: {dist}")

print("\n# ================= ACCEPTABILITY PER WFH CAPABILITY =================")

for wfh in df['wfh_capabilities'].dropna().unique():
    sub_df = df[df['wfh_capabilities'] == wfh]
    run_acceptability_analysis(sub_df, f"WFH group: {wfh}")

print("\n\n" + "="*120)
print("# ================= CAR REDUCTION ANALYSIS =================")
print("="*120)

print("\n# -------- FULL SAMPLE --------")
print("\n# Descriptive statistics:")
print(df['pve_car_reduction_pp'].describe())

print("\n# Mean car reduction:")
print(df['pve_car_reduction_pp'].mean())

print("\n\n" + "="*120)
print("# -------- CAR REDUCTION PER EXPERIMENT --------")
print("="*120)

exp_car = (
    df.groupby("experiment_group")["pve_car_reduction_pp"]
    .agg(["mean", "std", "count"])
    .sort_values(by="mean", ascending=False)
)
print(exp_car)

print("\n\n" + "="*120)
print("# -------- CAR REDUCTION PER DISTANCE --------")
print("="*120)

dist_car = (
    df.groupby("commute_distance_km_range")["pve_car_reduction_pp"]
    .agg(["mean", "std", "count"])
    .sort_values(by="mean", ascending=False)
)
print(dist_car)

print("\n\n" + "="*120)
print("# -------- CAR REDUCTION PER WFH CAPABILITY --------")
print("="*120)

wfh_car = (
    df.groupby("wfh_capabilities")["pve_car_reduction_pp"]
    .agg(["mean", "std", "count"])
    .sort_values(by="mean", ascending=False)
)
print(wfh_car)

print("\n\n" + "="*120)
print("# ================= WFH EFFECT ANALYSIS =================")
print("="*120)

# Describe the categorical working-from-home response to each policy.
wfh_cols = [
    'parking_rights_wfh_effect',
    'parking_costs_wfh_effect',
    'parking_reservation_wfh_effect',
    'pr_reward_wfh_effect',
    'vp_taxi_wfh_effect',
    'vp_departure_wfh_effect'
]


def run_wfh_effect_analysis(sub_df, group_name):
    """Print working-from-home responses for one group."""

    print("\n" + "="*100)
    print(f"# WFH EFFECTS FOR: {group_name}")
    print("="*100)

    print(f"\n# Sample size: {len(sub_df)}")

    for col in wfh_cols:
        print(f"\n## {col}")

        counts = sub_df[col].value_counts()
        print(counts)

        print("\nProportions:")
        print((counts / counts.sum()).round(3))

print("\n\n" + "-"*120)
print("# -------- WFH EFFECTS (FULL SAMPLE) --------")
print("-"*120)

run_wfh_effect_analysis(df, "Full sample")

print("\n\n" + "="*120)
print("# -------- WFH EFFECTS PER EXPERIMENT --------")
print("="*120)

for group in df['experiment_group'].unique():
    sub_df = df[df['experiment_group'] == group]
    run_wfh_effect_analysis(sub_df, f"Experiment group: {group}")

print("\n\n" + "="*120)
print("# -------- WFH EFFECTS PER DISTANCE --------")
print("="*120)

for dist in df['commute_distance_km_range'].dropna().unique():
    sub_df = df[df['commute_distance_km_range'] == dist]
    run_wfh_effect_analysis(sub_df, f"Distance group: {dist}")

print("\n\n" + "="*120)
print("# -------- WFH EFFECTS PER WFH CAPABILITY --------")
print("="*120)

for wfh in df['wfh_capabilities'].dropna().unique():
    sub_df = df[df['wfh_capabilities'] == wfh]
    run_wfh_effect_analysis(sub_df, f"WFH group: {wfh}")

print("\n\n" + "="*120)
print("# ================= NUMERIC WFH LIKELIHOOD ANALYSIS =================")
print("="*120)

# Map the ordinal WFH responses to the -2 to +2 analysis scale.
mapping = {
    "Much less likely to work from home": -2,
    "Slightly less likely to work from home": -1,
    "No effect": 0,
    "Slightly more likely to work from home": 1,
    "Much more likely to work from home": 2,
    "Not applicable — I cannot work from home": np.nan
}

print("\n# -------- AVERAGE WFH LIKELIHOOD (FULL SAMPLE) --------")

wfh_avg_full = {}

for col in wfh_cols:
    numeric = df[col].map(mapping)
    wfh_avg_full[col] = numeric.mean()

wfh_avg_full_series = pd.Series(wfh_avg_full).sort_values()

print("\n# Average WFH likelihood per policy:")
print(wfh_avg_full_series)

print("\n# Overall mean across all policies:")
print(wfh_avg_full_series.mean())

print("\n\n" + "="*120)
print("# -------- AVERAGE WFH LIKELIHOOD PER EXPERIMENT --------")
print("="*120)

exp_results = []

for group in df['experiment_group'].unique():
    sub_df = df[df['experiment_group'] == group]

    row = {"experiment_group": group}

    for col in wfh_cols:
        row[col] = sub_df[col].map(mapping).mean()

    exp_results.append(row)

exp_wfh_df = pd.DataFrame(exp_results).set_index("experiment_group")

exp_wfh_df["overall_mean"] = exp_wfh_df.mean(axis=1)

print(exp_wfh_df.sort_values("overall_mean", ascending=False))

print("\n\n" + "="*120)
print("# -------- AVERAGE WFH LIKELIHOOD PER COMMUTE DISTANCE --------")
print("="*120)

dist_results = []

for dist in df['commute_distance_km_range'].dropna().unique():
    sub_df = df[df['commute_distance_km_range'] == dist]

    row = {"commute_distance_km_range": dist}

    for col in wfh_cols:
        row[col] = sub_df[col].map(mapping).mean()

    dist_results.append(row)

dist_wfh_df = pd.DataFrame(dist_results).set_index("commute_distance_km_range")

dist_wfh_df["overall_mean"] = dist_wfh_df.mean(axis=1)

print(dist_wfh_df.sort_values("overall_mean", ascending=False))

print("\n\n" + "="*120)
print("# -------- AVERAGE WFH LIKELIHOOD PER WFH CAPABILITY --------")
print("="*120)

wfhcap_results = []

for wfh in df['wfh_capabilities'].dropna().unique():
    sub_df = df[df['wfh_capabilities'] == wfh]

    row = {"wfh_capabilities": wfh}

    for col in wfh_cols:
        row[col] = sub_df[col].map(mapping).mean()

    wfhcap_results.append(row)

wfhcap_wfh_df = pd.DataFrame(wfhcap_results).set_index("wfh_capabilities")

wfhcap_wfh_df["overall_mean"] = wfhcap_wfh_df.mean(axis=1)

print(wfhcap_wfh_df.sort_values("overall_mean", ascending=False))

print("\n\n" + "="*120)
print("# ================= INTERPRETATION GUIDE =================")
print("="*120)

print("""
# Interpretation:
# +1   = strong increase in likelihood to WFH
#  0   = no overall effect
# -1   = decrease in likelihood to WFH

# In practice:
# values around ±0.05 → very small effect
# values around ±0.10 → modest effect
# values > ±0.20 → strong effect

# The 'overall_mean' column shows the combined WFH effect across all policies
""")
