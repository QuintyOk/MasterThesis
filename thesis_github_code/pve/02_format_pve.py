"""Format the cleaned PVE and acceptability survey data.

The script derives respondent characteristics and mode availability, converts
the four TFA-based ranking questions, stores the selected policy levels and
modelled modal-split feedback, constructs each respondent's policy package,
and formats the working-from-home and optional open-text responses.

The analytical transformations are preserved from the final thesis code."""

import numpy as np
import pandas as pd

pd.set_option('display.max_rows', None)

pd.set_option('display.max_columns', None)

pd.set_option('display.max_colwidth', None)

pd.set_option('display.width', None)

# Load the cleaned PVE export and remove the Qualtrics label row.
clean_data = pd.read_excel(
    r"data\Access & Mobility Survey Acceptability Clean Data.xlsx",
    engine="openpyxl",
)

clean_data = clean_data.drop(index=0).reset_index(drop=True)
print("Final Number of respondents:", clean_data.shape)

print("\n" + "=" * 80)

# Start the respondent-level analytical dataset.
columns_to_keep = ["ResponseId", "Q25", "Q21"]

data_formatted = clean_data[columns_to_keep].copy()

data_formatted = data_formatted.rename(
    columns={
        "Q25": "commute_distance_km_range",
        "Q21": "office_days_per_week",
    }
)

print("\n" + "=" * 80)

print("value_counts office days", data_formatted["office_days_per_week"].value_counts())

data_formatted["office_days_per_week"] = (
    data_formatted["office_days_per_week"]
    .astype(str)
    .str.extract(r"(\d+)", expand=False)
    .astype(int)
)
print("value_counts office days", data_formatted["office_days_per_week"].value_counts())

print("\n" + "=" * 80)

# Reconstruct weekly use of each commuting mode.
transport_mode_map = {
    "Q23_1": "car_asml",
    "Q23_2": "car_pr",
    "Q23_3": "moped",
    "Q23_4": "bike",
    "Q23_5": "vanpool",
    "Q23_6": "carpool",
    "Q23_7": "bus",
    "Q23_8": "train_bus",
    "Q23_9": "train_ebike",
}


def parse_weekly_frequency(value):
    """Convert a Qualtrics weekly-frequency response to an integer."""
    if pd.isna(value):
        return 0
    return int(value.split("d")[0])


def build_transport_profile(row):
    """Build a weekly mode-use profile for one respondent."""
    return {
        mode_name: parse_weekly_frequency(row[q_col])
        for q_col, mode_name in transport_mode_map.items()
    }

clean_data["weekly_transport_profile"] = clean_data.apply(
    build_transport_profile,
    axis=1
)

data_formatted["weekly_commute_profile"] = clean_data.apply(build_transport_profile, axis=1)


def get_primary_transport_mode(profile):
    """Return the mode used most often during a typical week."""
    if not profile:
        return None

    max_trips = max(profile.values())

    if max_trips == 0:
        return None

    return max(profile, key=profile.get)

data_formatted["primary_transport_mode"] = data_formatted[
    "weekly_commute_profile"
].apply(get_primary_transport_mode)
print(
    "Primary transport mode values:",
    data_formatted["primary_transport_mode"].value_counts(),
)

print("\n" + "=" * 80)

# Derive car availability from the survey response.
data_formatted["car_available"] = clean_data["Q24"]
print("Car availability value counts (before):")
print(data_formatted["car_available"].value_counts(dropna=False))

data_formatted["car_available"] = data_formatted["car_available"].apply(
    lambda x: "No" if str(x).strip() == "No, (almost) never" else "Yes"
)

print("Car availability value counts (after):")
print(data_formatted["car_available"].value_counts(dropna=False))

print("\n" + "=" * 80)

print("commuting range", data_formatted["commute_distance_km_range"].value_counts())
# Treat cycling as feasible for commute ranges up to 30 kilometres.
bike_yes_ranges = [
    "Less than 5 km",
    "5–10 km",
    "10–20 km",
    "20–30 km"
]

data_formatted["bike_available"] = (
    data_formatted["commute_distance_km_range"]
    .isin(bike_yes_ranges)
    .map({True: "Yes", False: "No"})
)

print("Bike available counts:", data_formatted["bike_available"].value_counts())

print("\n" + "=" * 80)

print("Value counts vanpool: \n ", clean_data["Q30"].value_counts(dropna=False))

# Derive vanpool availability from the feasibility question.
nan_ids = clean_data.loc[clean_data["Q30"].isna(), "ResponseId"]

# Remove the response with a missing vanpool feasibility answer.
data_formatted = data_formatted[data_formatted["ResponseId"] != "R_23lFF1YaQLFo62Y"]

data_formatted["vanpool_available"] = (
    clean_data["Q30"].notna()
    & (clean_data["Q30"] != "No, the current pick-up locations are not feasible for me")
).map({True: "Yes", False: "No"})
data_formatted["vanpool_convenient"] = clean_data["Q30"]
print(data_formatted["vanpool_available"].head(10))
print(
    "Number of respondents with vanpool available: \n",
    (data_formatted["vanpool_available"] == "Yes").sum(),
)

print("vanpool value counts", data_formatted["vanpool_available"].value_counts())

print("\n" + "=" * 80)
data_formatted["familiar_vanpool"] = clean_data["Q28"]
print("Stats for vanpool familiarity")
print(data_formatted["familiar_vanpool"].value_counts())

print("\n" + "=" * 80)
data_formatted["familiar_pr"] = clean_data["Q26"]
print("Stats for P+R familiarity")
print(data_formatted["familiar_pr"].value_counts())

print("\n" + "=" * 80)
data_formatted["contract_type"] = clean_data["Q32"]
print("Contract types value counts")
print(data_formatted["contract_type"].value_counts())

print("\n" + "=" * 80)
data_formatted["wfh_capabilities"] = clean_data["Q22"]
print("Contract types value counts")
print(data_formatted["wfh_capabilities"].value_counts())

print("\n" + "=" * 80)
data_formatted["work_location"] = clean_data["Q19"]
print("work locations")
print(data_formatted["work_location"].value_counts())

print("\n" + "=" * 80)
print("Formatting ranking: policy effectiveness (column rename)")

# Rename and convert the perceived-effectiveness rankings.
data_formatted = data_formatted.join(
    clean_data[["Q4_1", "Q4_2", "Q4_3", "Q4_4", "Q4_5", "Q4_6"]]
    .rename(columns={
        "Q4_1": "parking_rights_effectiveness_rank",
        "Q4_2": "parking_costs_effectiveness_rank",
        "Q4_3": "parking_reservation_effectiveness_rank",
        "Q4_4": "pr_reward_effectiveness_rank",
        "Q4_5": "vp_taxi_effectiveness_rank",
        "Q4_6": "vp_departure_effectiveness_rank"
    })
    .apply(pd.to_numeric)
)

print("\nPreview of renamed columns:")
print(data_formatted[[
    "parking_rights_effectiveness_rank",
    "parking_costs_effectiveness_rank",
    "parking_reservation_effectiveness_rank",
    "pr_reward_effectiveness_rank",
    "vp_taxi_effectiveness_rank",
    "vp_departure_effectiveness_rank"
]].head())

print("\n" + "=" * 80)
print("Formatting ranking: policy fairness (column rename)")

# Rename the fairness rankings.
data_formatted = data_formatted.join(
    clean_data[["Q8_1", "Q8_2", "Q8_3", "Q8_4", "Q8_5", "Q8_6"]]
    .rename(columns={
        "Q8_1": "parking_rights_fairness_rank",
        "Q8_2": "parking_costs_fairness_rank",
        "Q8_3": "parking_reservation_fairness_rank",
        "Q8_4": "pr_reward_fairness_rank",
        "Q8_5": "vp_taxi_fairness_rank",
        "Q8_6": "vp_departure_fairness_rank"
    })
)

print("\nPreview of renamed fairness ranking columns:")
print(data_formatted[[
    "parking_rights_fairness_rank",
    "parking_costs_fairness_rank",
    "parking_reservation_fairness_rank",
    "pr_reward_fairness_rank",
    "vp_taxi_fairness_rank",
    "vp_departure_fairness_rank"
]].head())

print("\n" + "=" * 80)
print("Formatting ranking: policy convenience (column rename)")

# Rename and convert the convenience rankings.
data_formatted = data_formatted.join(
    clean_data[["Q10_1","Q10_2","Q10_3","Q10_4","Q10_5","Q10_6"]]
    .rename(columns={
        "Q10_1": "parking_rights_convenience_rank",
        "Q10_2": "parking_costs_convenience_rank",
        "Q10_3": "parking_reservation_convenience_rank",
        "Q10_4": "pr_reward_convenience_rank",
        "Q10_5": "vp_taxi_convenience_rank",
        "Q10_6": "vp_departure_convenience_rank"
    })
    .apply(pd.to_numeric)
)

print("\nPreview of renamed convenience columns:")
print(data_formatted[[
    "parking_rights_convenience_rank",
    "parking_costs_convenience_rank",
    "parking_reservation_convenience_rank",
    "pr_reward_convenience_rank",
    "vp_taxi_convenience_rank",
    "vp_departure_convenience_rank"
]].head())

print("\n" + "=" * 80)
print("Formatting ranking: policy personal support (column rename)")

# Rename and convert the personal-support rankings.
data_formatted = data_formatted.join(
    clean_data[["Q11_1","Q11_2","Q11_3","Q11_4","Q11_5","Q11_6"]]
    .rename(columns={
        "Q11_1": "parking_rights_support_rank",
        "Q11_2": "parking_costs_support_rank",
        "Q11_3": "parking_reservation_support_rank",
        "Q11_4": "pr_reward_support_rank",
        "Q11_5": "vp_taxi_support_rank",
        "Q11_6": "vp_departure_support_rank"
    })
    .apply(pd.to_numeric)
)

print("\nPreview of renamed personal support columns:")
print(data_formatted[[
    "parking_rights_support_rank",
    "parking_costs_support_rank",
    "parking_reservation_support_rank",
    "pr_reward_support_rank",
    "vp_taxi_support_rank",
    "vp_departure_support_rank"
]].head())

print("\n" + "=" * 80)
print("Formatting PVE outputs (modal split + reduction)")

# Convert the modelled modal shares and car reduction to numeric values.
pve_cols = [
    "pve_share_car_percent",
    "pve_share_bike_percent",
    "pve_share_public_transport_percent",
    "pve_car_reduction_pp"
]

data_formatted[pve_cols] = clean_data[pve_cols].apply(pd.to_numeric)

print("\nPreview of PVE outputs:")
print(data_formatted[pve_cols].head())

print("\nData types:")
print(data_formatted[pve_cols].dtypes)

print("\n" + "=" * 80)
print("Creating per-policy key-value columns")

# Store the selected level and label for each policy.
data_formatted["parking_rights_policy_pve"] = clean_data.apply(
    lambda row: {
        "value": row["pve_parking_rights_policy"],
        "label": row["pve_parking_rights_policy_label"]
    }, axis=1
)

data_formatted["parking_cost_policy_pve"] = clean_data.apply(
    lambda row: {
        "value": row["pve_parking_cost"],
        "label": row["pve_parking_cost_label"]
    }, axis=1
)

data_formatted["parking_reservation_policy_pve"] = clean_data.apply(
    lambda row: {
        "value": row["pve_parking_reservation"],
        "label": row["pve_parking_reservation_label"]
    }, axis=1
)

data_formatted["pr_reward_policy_pve"] = clean_data.apply(
    lambda row: {
        "value": row["pve_pr_reward"],
        "label": row["pve_pr_reward_label"]
    }, axis=1
)

data_formatted["vp_taxi_policy_pve"] = clean_data.apply(
    lambda row: {
        "value": row["pve_vp_taxi"],
        "label": row["pve_vp_taxi_label"]
    }, axis=1
)

data_formatted["vp_frequency_policy_pve"] = clean_data.apply(
    lambda row: {
        "value": row["pve_vp_frequency"],
        "label": row["pve_vp_frequency_label"]
    }, axis=1
)

print("\n" + "=" * 80)
print("Creating full policy package")

# Combine the six selected policy levels into one package object.
data_formatted["policy_package"] = data_formatted.apply(
    lambda row: {
        "parking_rights": row["parking_rights_policy_pve"],
        "parking_cost": row["parking_cost_policy_pve"],
        "parking_reservation": row["parking_reservation_policy_pve"],
        "pr_reward": row["pr_reward_policy_pve"],
        "vp_taxi": row["vp_taxi_policy_pve"],
        "vp_frequency": row["vp_frequency_policy_pve"]
    },
    axis=1
)

print(data_formatted["policy_package"].head(2))

print(
    data_formatted["policy_package"]
    .apply(lambda x: set(x.keys()))
    .value_counts()
)

print("\n" + "=" * 80)
print("Formatting working-from-home effect (Q13)")

# Rename the policy-specific working-from-home responses.
data_formatted = data_formatted.join(
    clean_data[["Q13_1", "Q13_2", "Q13_3", "Q13_4", "Q13_5", "Q13_6"]]
    .rename(columns={
        "Q13_1": "parking_rights_wfh_effect",
        "Q13_2": "parking_costs_wfh_effect",
        "Q13_3": "parking_reservation_wfh_effect",
        "Q13_4": "pr_reward_wfh_effect",
        "Q13_5": "vp_taxi_wfh_effect",
        "Q13_6": "vp_departure_wfh_effect"
    })
)

print(data_formatted[[
    "parking_rights_wfh_effect",
    "parking_costs_wfh_effect",
    "parking_reservation_wfh_effect",
    "pr_reward_wfh_effect",
    "vp_taxi_wfh_effect",
    "vp_departure_wfh_effect"
]].head())

print("\n" + "=" * 80)
print("Formatting open-text commute questions")

# Retain the optional open-text responses in the formatted dataset.
data_formatted = data_formatted.join(
    clean_data[["Q14", "Q15", "Q16", "Q17"]]
    .rename(columns={
        "Q14": "commute_stress_experience",
        "Q15": "commute_improvements",
        "Q16": "barriers_sustainable_commuting",
        "Q17": "additional_comments"
    })
)

print(data_formatted[[
    "commute_stress_experience",
    "commute_improvements",
    "barriers_sustainable_commuting",
    "additional_comments"
]].head())

print("\n" + "=" * 80)
print("In the formatted dataset, you can find: ")
print(data_formatted.columns)
print(" ")
print(data_formatted.head(20))

# Save the formatted PVE dataset.
data_formatted.to_excel(
    r"data\Access & Mobility Survey Acceptability Formatted Data.xlsx",
    index=False
)
