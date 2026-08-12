"""Describe the final PVE sample and analyse ranking correlations.

The first part reports respondent characteristics and mode availability. The
second part checks the completeness of the four TFA-based rankings, calculates
respondent-level Spearman correlations with bootstrap confidence intervals,
and reports descriptive correlations between aggregate policy rankings.

The formatted employee-level data required by this script are confidential."""

from itertools import combinations

import numpy as np
import pandas as pd
from scipy.stats import spearmanr

# Load the formatted PVE dataset.
data_formatted = pd.read_excel(
    r"data\Access & Mobility Survey Acceptability Formatted Data.xlsx",
    engine="openpyxl",
)

pd.set_option('display.max_rows', None)

pd.set_option('display.max_columns', None)

pd.set_option('display.max_colwidth', None)

pd.set_option('display.width', None)

print("\n" + "=" * 80)

print("Columns data formatted: ", data_formatted.columns)

print("The number of respondents after data cleaning: ", data_formatted["ResponseId"].nunique())

print("\n" + "=" * 80)

print(data_formatted["primary_transport_mode"].value_counts())

# Describe primary commuting modes and respondent characteristics.
modal_split = (
    data_formatted[["ResponseId", "primary_transport_mode"]]
    .drop_duplicates("ResponseId")["primary_transport_mode"]
    .value_counts(dropna=False)
)
nan_ids = data_formatted.loc[
    data_formatted["primary_transport_mode"].isna(),
    "ResponseId"
]

print("ResponseIds with NaN primary transport mode:")
print(nan_ids.tolist())

print("Current modal split (based on primary transport mode):")
print(modal_split)

print("\n" + "=" * 80)

commute_stats = (
    data_formatted["commute_distance_km_range"].describe()
)
print("Descriptive statistics for commute distance (km):")
print(commute_stats)
print("Value Counts for commute distance (km):")
print(data_formatted["commute_distance_km_range"].value_counts())

print("\n" + "=" * 80)

print("Descriptive statistics for office days per week:")
print(data_formatted["office_days_per_week"].describe())
print("Value Counts for office days per week:")
print(data_formatted["office_days_per_week"].value_counts())

print("\n" + "=" * 80)

print("Descriptive statistics for wfh_capabilities per week:")
print(data_formatted["wfh_capabilities"].describe())
print("Value Counts for wfh_capabilities:")
print(data_formatted["wfh_capabilities"].value_counts())

print("\n" + "=" * 80)

print("Descriptive statistics for car_available per week:")
print(data_formatted["car_available"].describe())
print("Value Counts for car_available:")
print(data_formatted["car_available"].value_counts())

print("\n" + "=" * 80)

print("Descriptive statistics for bike_available per week:")
print(data_formatted["bike_available"].describe())
print("Value Counts for bike_available:")
print(data_formatted["bike_available"].value_counts())

print("\n" + "=" * 80)

print("Descriptive statistics for vanpool_available per week:")
print(data_formatted["vanpool_available"].describe())
print("Value Counts for vanpool_available:")
print(data_formatted["vanpool_available"].value_counts())

print("\n" + "=" * 80)

print("Descriptive statistics for familiar_vanpool per week:")
print(data_formatted["familiar_vanpool"].describe())
print("Value Counts for familiar_vanpool:")
print(data_formatted["familiar_vanpool"].value_counts())

print("\n" + "=" * 80)

print("Descriptive statistics for familiar_pr per week:")
print(data_formatted["familiar_pr"].describe())
print("Value Counts for familiar_pr:")
print(data_formatted["familiar_pr"].value_counts())

print("\n" + "=" * 80)

print("Descriptive statistics for contract_typer per week:")
print(data_formatted["contract_type"].describe())
print("Value Counts for contract_type:")
print(data_formatted["contract_type"].value_counts())

print("\n" + "=" * 80)

print("Descriptive statistics for work_location per week:")
print(data_formatted["work_location"].describe())
print("Value Counts for work_location:")
print(data_formatted["work_location"].value_counts())

print("\n" + "=" * 80)

print("Descriptive statistics for work_location per week:")
print(data_formatted["work_location"].describe())
print("Value Counts for work_location:")
print(data_formatted["work_location"].value_counts())

print("\n" + "=" * 80)

print("Descriptive statistics for vanpool_convenient:")
print(data_formatted["vanpool_convenient"].describe())
print("Value Counts for vanpool_convenient:")
print(data_formatted["vanpool_convenient"].value_counts())

print("\n" + "=" * 80)

# Summarise respondent-level mode availability.
availability_cols = ["car_available", "bike_available", "vanpool_available"]

pd.set_option("display.max_rows", None)
pd.set_option("display.max_columns", None)
pd.set_option("display.width", None)
pd.set_option("display.max_colwidth", None)

availability_cols = ["car_available", "bike_available", "vanpool_available"]


def yes_no(series):
    """Collapse detailed availability responses to Yes and No."""
    return series.apply(lambda x: "Yes" if isinstance(x, str) and x.startswith("Yes") else "No")

availability_yesno_pct = (
    data_formatted[["ResponseId"] + availability_cols]
    .drop_duplicates("ResponseId")[availability_cols]
    .apply(yes_no)
    .apply(lambda s: s.value_counts(normalize=True) * 100)
    .round(1)
)

print("Percentage availability (Yes/No, respondent level):")
print(availability_yesno_pct)

pd.set_option("display.max_rows", None)
pd.set_option("display.max_columns", None)
pd.set_option("display.width", None)
pd.set_option("display.max_colwidth", None)

# Configure the ranking-correlation analysis.
DATA_PATH = r"data\Access & Mobility Survey Acceptability Formatted Data.xlsx"

NUMBER_OF_BOOTSTRAP_SAMPLES = 10_000
BOOTSTRAP_CONFIDENCE_LEVEL = 0.95
RANDOM_SEED = 20260803

# Reload the formatted dataset for the self-contained correlation block.
data_formatted = pd.read_excel(
    DATA_PATH,
    engine="openpyxl",
)

print("=" * 120)
print("PVE RANKING CORRELATION ANALYSIS")
print("=" * 120)

print(f"\nDataset loaded from {DATA_PATH}")
print(f"Number of rows in dataset = {len(data_formatted)}")
print(
    "Number of unique respondents = "
    f"{data_formatted['ResponseId'].nunique()}"
)

# Keep the six policies in the same order for every ranking dimension.
ranking_columns = {
    "Perceived effectiveness": [
        "parking_rights_effectiveness_rank",
        "parking_costs_effectiveness_rank",
        "parking_reservation_effectiveness_rank",
        "pr_reward_effectiveness_rank",
        "vp_taxi_effectiveness_rank",
        "vp_departure_effectiveness_rank",
    ],
    "Fairness": [
        "parking_rights_fairness_rank",
        "parking_costs_fairness_rank",
        "parking_reservation_fairness_rank",
        "pr_reward_fairness_rank",
        "vp_taxi_fairness_rank",
        "vp_departure_fairness_rank",
    ],
    "Convenience": [
        "parking_rights_convenience_rank",
        "parking_costs_convenience_rank",
        "parking_reservation_convenience_rank",
        "pr_reward_convenience_rank",
        "vp_taxi_convenience_rank",
        "vp_departure_convenience_rank",
    ],
    "Personal support": [
        "parking_rights_support_rank",
        "parking_costs_support_rank",
        "parking_reservation_support_rank",
        "pr_reward_support_rank",
        "vp_taxi_support_rank",
        "vp_departure_support_rank",
    ],
}

policy_display_names = [
    "Parking rights",
    "Parking payment",
    "Priority reservation",
    "P&R reward",
    "Vanpool emergency taxi",
    "Vanpool departure frequency",
]

# Validate and convert the ranking variables.
all_rank_columns = [
    column
    for dimension_columns in ranking_columns.values()
    for column in dimension_columns
]

missing_columns = [
    column
    for column in all_rank_columns
    if column not in data_formatted.columns
]

if missing_columns:
    raise KeyError(
        "The following required ranking columns are missing from "
        f"the formatted PVE dataset\n{missing_columns}"
    )

print("\nAll required ranking columns were found.")

data_formatted[all_rank_columns] = data_formatted[
    all_rank_columns
].apply(
    pd.to_numeric,
    errors="coerce",
)

# Identify complete rankings before calculating correlations.
expected_ranks = [1, 2, 3, 4, 5, 6]


def has_complete_ranking(row):
    """Return whether a respondent used every rank from 1 to 6 once."""

    observed_ranks = row.dropna().tolist()

    return (
        len(observed_ranks) == 6
        and sorted(observed_ranks) == expected_ranks
    )

valid_ranking_masks = {
    dimension: data_formatted[columns].apply(
        has_complete_ranking,
        axis=1,
    )
    for dimension, columns in ranking_columns.items()
}

print("\n" + "-" * 120)
print("NUMBER OF COMPLETE RANKINGS PER DIMENSION")
print("-" * 120)

for dimension, valid_mask in valid_ranking_masks.items():
    print(f"{dimension} = {int(valid_mask.sum())}")


def bootstrap_mean_confidence_interval(
    values,
    n_resamples=NUMBER_OF_BOOTSTRAP_SAMPLES,
    confidence_level=BOOTSTRAP_CONFIDENCE_LEVEL,
    seed=RANDOM_SEED,
):
    """Bootstrap a percentile confidence interval for the mean rho."""

    values = np.asarray(values, dtype=float)

    if len(values) < 2:
        return np.nan, np.nan

    random_generator = np.random.default_rng(seed)

    bootstrap_indices = random_generator.integers(
        low=0,
        high=len(values),
        size=(n_resamples, len(values)),
    )

    bootstrap_means = values[bootstrap_indices].mean(axis=1)

    alpha = (1 - confidence_level) / 2

    confidence_interval_low, confidence_interval_high = np.quantile(
        bootstrap_means,
        [alpha, 1 - alpha],
    )

    return confidence_interval_low, confidence_interval_high


def calculate_spearman_correlation(values_1, values_2):
    """Return Spearman's rank-correlation coefficient."""

    result = spearmanr(values_1, values_2)

    if hasattr(result, "statistic"):
        return float(result.statistic)

    return float(result[0])

# Calculate respondent-level correlations for every dimension pair.
dimension_names = list(ranking_columns.keys())

mean_rho_matrix = pd.DataFrame(
    np.eye(len(dimension_names)),
    index=dimension_names,
    columns=dimension_names,
)

pairwise_n_matrix = pd.DataFrame(
    pd.NA,
    index=dimension_names,
    columns=dimension_names,
    dtype="Int64",
)

for dimension in dimension_names:
    pairwise_n_matrix.loc[dimension, dimension] = int(
        valid_ranking_masks[dimension].sum()
    )

correlation_results = []
respondent_level_correlations = {}

dimension_pairs = list(
    combinations(dimension_names, 2)
)

for pair_number, (dimension_1, dimension_2) in enumerate(
    dimension_pairs
):
    columns_1 = ranking_columns[dimension_1]
    columns_2 = ranking_columns[dimension_2]

    valid_pair_mask = (
        valid_ranking_masks[dimension_1]
        & valid_ranking_masks[dimension_2]
    )

    valid_pair_data = data_formatted.loc[
        valid_pair_mask,
        columns_1 + columns_2,
    ].copy()

    respondent_rhos = valid_pair_data.apply(
        lambda row: calculate_spearman_correlation(
            row[columns_1].to_numpy(dtype=float),
            row[columns_2].to_numpy(dtype=float),
        ),
        axis=1,
    ).dropna()

    pair_name = f"{dimension_1} versus {dimension_2}"

    respondent_level_correlations[pair_name] = respondent_rhos

    mean_rho = respondent_rhos.mean()
    median_rho = respondent_rhos.median()

    confidence_interval_low, confidence_interval_high = (
        bootstrap_mean_confidence_interval(
            values=respondent_rhos.to_numpy(),
            n_resamples=NUMBER_OF_BOOTSTRAP_SAMPLES,
            confidence_level=BOOTSTRAP_CONFIDENCE_LEVEL,
            seed=RANDOM_SEED + pair_number,
        )
    )

    mean_rho_matrix.loc[
        dimension_1,
        dimension_2,
    ] = mean_rho

    mean_rho_matrix.loc[
        dimension_2,
        dimension_1,
    ] = mean_rho

    pairwise_n_matrix.loc[
        dimension_1,
        dimension_2,
    ] = len(respondent_rhos)

    pairwise_n_matrix.loc[
        dimension_2,
        dimension_1,
    ] = len(respondent_rhos)

    correlation_results.append({
        "dimension_1": dimension_1,
        "dimension_2": dimension_2,
        "valid_respondents": len(respondent_rhos),
        "mean_spearman_rho": mean_rho,
        "bootstrap_95_ci_low": confidence_interval_low,
        "bootstrap_95_ci_high": confidence_interval_high,
        "median_spearman_rho": median_rho,
        "interquartile_range_low": respondent_rhos.quantile(0.25),
        "interquartile_range_high": respondent_rhos.quantile(0.75),
        "share_positive": (respondent_rhos > 0).mean(),
        "share_zero": np.isclose(respondent_rhos, 0).mean(),
        "share_negative": (respondent_rhos < 0).mean(),
    })

respondent_level_correlation_summary = pd.DataFrame(
    correlation_results
)

# Compare the six aggregate mean policy ranks descriptively.
policy_mean_ranks = pd.DataFrame(
    index=policy_display_names
)

for dimension, columns in ranking_columns.items():
    valid_dimension_data = data_formatted.loc[
        valid_ranking_masks[dimension],
        columns,
    ]

    policy_mean_ranks[dimension] = (
        valid_dimension_data
        .mean(axis=0)
        .to_numpy()
    )

aggregate_policy_rho_matrix = policy_mean_ranks.corr(
    method="spearman"
)

# Compare predicted effectiveness and acceptability for four policies.
decision_grade_policy_ranks = pd.DataFrame({
    "policy": [
        "Parking rights",
        "Parking payment",
        "Priority reservation",
        "P&R reward",
    ],
    "predicted_effectiveness_rank": [
        1,
        2,
        3,
        4,
    ],
    "acceptability_rank": [
        1,
        4,
        3,
        2,
    ],
})

decision_grade_spearman_rho = (
    calculate_spearman_correlation(
        decision_grade_policy_ranks[
            "predicted_effectiveness_rank"
        ],
        decision_grade_policy_ranks[
            "acceptability_rank"
        ],
    )
)

print("\n" + "=" * 120)
print("FINAL RESULTS")
print("=" * 120)

print("\n1. RESPONDENT-LEVEL SPEARMAN CORRELATIONS")
print("-" * 120)

print(
    respondent_level_correlation_summary
    .round(3)
    .to_string(index=False)
)

print(
    "\nInterpretation\n"
    "A positive coefficient means respondents generally ranked "
    "the policies similarly on the two dimensions.\n"
    "A negative coefficient means policies ranked favourably on "
    "one dimension tended to be ranked unfavourably on the other."
)

print("\n" + "=" * 120)
print("2. MEAN RESPONDENT-LEVEL SPEARMAN CORRELATION MATRIX")
print("=" * 120)

print(
    mean_rho_matrix
    .round(3)
    .to_string()
)

print("\n" + "=" * 120)
print("3. PAIRWISE NUMBER OF VALID RESPONDENTS")
print("=" * 120)

print(
    pairwise_n_matrix
    .to_string()
)

print("\n" + "=" * 120)
print("4. AVERAGE POLICY RANKS PER ACCEPTABILITY DIMENSION")
print("=" * 120)

print(
    policy_mean_ranks
    .round(3)
    .to_string()
)

print("\n" + "=" * 120)
print("5. CORRELATIONS BETWEEN AGGREGATE POLICY RANKINGS")
print("=" * 120)

print(
    aggregate_policy_rho_matrix
    .round(3)
    .to_string()
)

print(
    "\nThese correlations compare the six average policy ranks. "
    "They should be interpreted descriptively because the analysis "
    "contains only six policies."
)

print("\n" + "=" * 120)
print("6. PREDICTED EFFECTIVENESS VERSUS ACCEPTABILITY")
print("=" * 120)

print(
    decision_grade_policy_ranks
    .to_string(index=False)
)

print(
    "\nDescriptive Spearman correlation between the "
    "predicted-effectiveness ranking and acceptability ranking "
    f"= {decision_grade_spearman_rho:.3f}"
)

print(
    "\nThis coefficient is based on four decision-grade policies. "
    "It should be treated as a descriptive summary rather than "
    "an inferential statistical test."
)

print("\n" + "=" * 120)
print("END OF CORRELATION ANALYSIS")
print("=" * 120)
