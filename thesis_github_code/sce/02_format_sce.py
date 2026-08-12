"""Format the cleaned SCE data for descriptive analysis and Biogeme.

The script derives respondent characteristics and mode availability, assigns
respondents to availability experiments and design blocks, expands the data to
the task level, reconstructs the three recorded choices, merges the Ngene
attribute design, and writes the formatted SCE dataset.

The analytical transformations are preserved from the final thesis code."""

import numpy as np
import pandas as pd

# Load the cleaned SCE export and remove the Qualtrics label row.
clean_data = pd.read_excel(
    r"data\Access & Mobility Survey Clean Data.xlsx",
    engine="openpyxl",
)

clean_data = clean_data.drop(index=0).reset_index(drop=True)

print("\n" + "=" * 80)

# Start the respondent-level analytical dataset.
columns_to_keep = ["ResponseId", "Q1.3", "Q46"]

data_formatted = clean_data[columns_to_keep].copy()

data_formatted = data_formatted.rename(
    columns={
        "Q1.3": "commute_distance_km",
        "Q46": "office_days_per_week",
    }
)

print("\n" + "=" * 80)

data_formatted["office_days_per_week"] = (
    data_formatted["office_days_per_week"]
    .astype(str)
    .str.extract(r"(\d+)", expand=False)
    .astype(int)
)

print("\n" + "=" * 80)

# Reconstruct weekly use of each commuting mode.
transport_mode_map = {
    "Q1.4_1": "car_asml",
    "Q1.4_2": "car_pr",
    "Q1.4_3": "carpool",
    "Q1.4_4": "vanpool",
    "Q1.4_5": "bike",
    "Q1.4_6": "moped",
    "Q1.4_7": "bus",
    "Q1.4_8": "train_bus",
    "Q1.4_9": "train_ebike",
}


def parse_weekly_frequency(value):
    """Convert a Qualtrics weekly-frequency response to an integer."""
    if pd.isna(value):
        return 0
    return int(value.split("x")[0])


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

data_formatted["weekly_commute_profile"] = clean_data.apply(
    build_transport_profile, axis=1
)


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

print("\n" + "=" * 80)

# Derive car availability and reconcile it with reported car use.
data_formatted["car_available"] = clean_data["Q1.5"]

print("Car availability value counts (before override):")
print(data_formatted["car_available"].value_counts(dropna=False))
print()

used_car = data_formatted["weekly_commute_profile"].apply(
    lambda profile: profile.get("car_asml", 0) > 0 or profile.get("car_pr", 0) > 0
)

data_formatted.loc[used_car, "car_available"] = "Yes, always"

print("Car availability value counts (after override):")
print(data_formatted["car_available"].value_counts(dropna=False))
print()

print("Car users who were overridden to 'Yes, always':")
print(
    data_formatted.loc[
        used_car & (clean_data["Q1.5"] != "Yes, always"),
        ["weekly_commute_profile"]
    ].head(10)
)

print("\n" + "=" * 80)

# Treat cycling as available for commutes of at most 30 kilometres.
data_formatted["bike_available"] = (
        data_formatted["commute_distance_km"] <= 30
).map({True: "Yes", False: "No"})

print("\n" + "=" * 80)

print("Value counts vanpool: \n ", clean_data["Q64"].value_counts(dropna=False))

# Derive vanpool availability from feasible pick-up locations.
data_formatted["vanpool_available"] = (
        clean_data["Q64"]
        .notna()
        & (clean_data["Q64"] != "None of the locations are convenient for me")
).map({True: "Yes", False: "No"})

print(data_formatted["vanpool_available"].head(10))
print("Number of respondents with vanpool available: \n",
      (data_formatted["vanpool_available"] == "Yes").sum())

print("\n" + "=" * 80)

# Extract the respondent-specific travel-time variables.
data_formatted["car_time"] = (
    clean_data["Q15"]
    .astype(str)
    .str.extract(r"(\d+)", expand=False)
    .astype("Int64")
)

data_formatted["pr_time"] = clean_data["PR_time"]

data_formatted["bike_time"] = (
    clean_data["Q16"]
    .astype(str)
    .str.extract(r"(\d+)", expand=False)
    .astype("Int64")
)

data_formatted["pt_time"] = (
    clean_data["Q17"]
    .astype(str)
    .str.extract(r"(\d+)", expand=False)
    .astype("Int64")
)

data_formatted["vp_time"] = clean_data["vp_time"]

print(data_formatted[["car_time", "pr_time", "bike_time", "pt_time", "vp_time"]].head(20))

print("\n" + "=" * 80)
data_formatted["familiar_vanpool"] = clean_data["Q638"]
print("Stats for vanpool familiarity")
print(data_formatted["familiar_vanpool"].value_counts())

print("\n" + "=" * 80)
data_formatted["vanpool_convenient_existing_location"] = clean_data["Q64"]
print("Existing convenient vanpool location counts: \n",
      data_formatted["vanpool_convenient_existing_location"].value_counts())

data_formatted["vanpool_likelihood_if_available"] = clean_data["Q640"]
print("How likely to choose vanpool: \n",
      data_formatted["vanpool_likelihood_if_available"].value_counts())
data_formatted["vanpool_desired_city"] = clean_data["Q641"]

print("\n" + "=" * 80)

car_yes = data_formatted["car_available"].isin([
    "Yes, always",
    "Yes, but only in consultation with other household members"
])

bike_yes = data_formatted["bike_available"] == "Yes"
vanpool_yes = data_formatted["vanpool_available"] == "Yes"

# Assign the availability experiment implied by each feasible choice set.
data_formatted["experiment"] = np.nan

data_formatted.loc[(~bike_yes) & (~car_yes) & (vanpool_yes), "experiment"] = 1

data_formatted.loc[(bike_yes) & (~car_yes) & (vanpool_yes), "experiment"] = 2

data_formatted.loc[(~bike_yes) & (car_yes) & (~vanpool_yes), "experiment"] = 3

data_formatted.loc[(bike_yes) & (car_yes) & (~vanpool_yes), "experiment"] = 4

data_formatted.loc[(~bike_yes) & (car_yes) & (vanpool_yes), "experiment"] = 5

data_formatted.loc[(bike_yes) & (car_yes) & (vanpool_yes), "experiment"] = 6

data_formatted["experiment"] = data_formatted["experiment"].astype("Int64")

pd.set_option("display.max_rows", None)
pd.set_option("display.max_columns", None)
pd.set_option("display.width", None)
pd.set_option("display.max_colwidth", None)

print(
    data_formatted[
        ["car_available", "bike_available", "vanpool_available", "experiment"]
    ].head(20)
)
print(
    "How many people are there per experiment? \n",
    data_formatted["experiment"].value_counts(),
)
print(
    "Number of people that do not fall in any experiment: ",
    data_formatted["experiment"].isna().sum(),
)

print(
    "Sanity check exp 1&2: \n",
    pd.crosstab(
        data_formatted["car_available"],
        data_formatted["vanpool_available"],
        margins=True,
    ),
)

print("\n" + "=" * 80)

# Identify the randomised design block from the first populated task field.
block_anchors = {
    1: {"A": ["Q3"]},
    2: {"A": ["Q3.1"]},
    3: {"A": ["Q3.2"], "B": ["Q3.3"], "C": ["Q3.4"]},
    4: {"A": ["Q3.5"], "B": ["Q3.6"], "C": ["Q3.7"]},
    5: {"A": ["Q3.8"], "B": ["Q3.9"], "C": ["Q3.10"]},
    6: {"A": ["Q61"], "B": ["Q3.11"], "C": ["Q3.12"]},
}


def assign_block(row):
    """Identify the experimental block from the populated anchor question."""
    exp = row["experiment"]
    if pd.isna(exp):
        return pd.NA
    raw = clean_data.loc[clean_data["ResponseId"] == row["ResponseId"]].iloc[0]
    return next(
        (
            b
            for b, cs in block_anchors[int(exp)].items()
            if any(pd.notna(raw[c]) for c in cs)
        ),
        pd.NA,
    )

data_formatted["block"] = data_formatted.apply(assign_block, axis=1)

# Remove the response whose task fields did not identify a valid design block.
data_formatted = data_formatted[
    data_formatted["ResponseId"] != "R_8PuJ1ZSxEgQYXfZ"
].reset_index(drop=True)

print(
    "Checking that the blocks are correct: \n",
    data_formatted["block"].value_counts(dropna=False),
)
print(pd.crosstab(data_formatted["experiment"], data_formatted["block"], dropna=False))
print(
    data_formatted.loc[
        data_formatted["experiment"].notna() & data_formatted["block"].isna(),
        ["ResponseId", "experiment"],
    ].to_string(index=False)
)

print("\n" + "=" * 80)

# Expand each respondent to one row per SCE task.
data_formatted["n_tasks"] = np.where(
    data_formatted["experiment"].isin([1, 2]),
    6,
    8
)

data_formatted = data_formatted.loc[
    data_formatted.index.repeat(data_formatted["n_tasks"])
].copy()

block_task_map = {
    "A": [2, 6, 7, 9, 10, 13, 17, 21],
    "B": [1, 8, 11, 18, 19, 20, 22, 23],
    "C": [3, 4, 5, 12, 14, 15, 16, 24],
}

data_formatted["_task_pos"] = data_formatted.groupby("ResponseId").cumcount()

data_formatted["task"] = data_formatted.apply(
    lambda r: block_task_map[r["block"]][r["_task_pos"]]
    if pd.notna(r["block"]) else pd.NA,
    axis=1
)

data_formatted = data_formatted.drop(columns=["n_tasks", "_task_pos"]).reset_index(drop=True)

print("\n" + "=" * 80)

# Reconstruct the base, parking-rights, and conditional task responses.
mode_map = {
    "Car": "car",
    "P+R": "pr",
    "Vanpool": "vanpool",
    "Public Transport": "pt",
    "(e)-Bicycle": "bike",
    "(e-)Bicycle": "bike",
}


def normalize_mode(val):
    """Map a respondent-facing mode label to the analysis label."""
    if pd.isna(val):
        return pd.NA
    return mode_map.get(str(val).strip(), pd.NA)


def get_base_choice(row):
    """Recover the first mode choice recorded for an SCE task."""
    if pd.isna(row["experiment"]) or pd.isna(row["block"]):
        return pd.NA

    raw = clean_data.loc[clean_data["ResponseId"] == row["ResponseId"]].iloc[0]

    anchor_col = block_anchors[int(row["experiment"])][row["block"]][0]
    start_idx = clean_data.columns.get_loc(anchor_col)

    task_pos = block_task_map[row["block"]].index(row["task"])
    base_idx = start_idx + task_pos * 3

    if base_idx >= len(clean_data.columns):
        return pd.NA

    return normalize_mode(raw.iloc[base_idx])

data_formatted["base_choice"] = data_formatted.apply(get_base_choice, axis=1)
print(
    "Checking if base choice is done right: \n",
    data_formatted["base_choice"].value_counts(dropna=False),
)

print("\n" + "=" * 80)


def get_give_up_parking(row):
    """Recover the parking-rights decision recorded for an SCE task."""
    if pd.isna(row["experiment"]) or pd.isna(row["block"]):
        return pd.NA

    raw = clean_data.loc[clean_data["ResponseId"] == row["ResponseId"]].iloc[0]

    anchor_col = block_anchors[int(row["experiment"])][row["block"]][0]
    start_idx = clean_data.columns.get_loc(anchor_col)

    task_pos = block_task_map[row["block"]].index(row["task"])
    park_idx = start_idx + task_pos * 3 + 1

    if park_idx >= len(clean_data.columns):
        return pd.NA

    return raw.iloc[park_idx]

data_formatted["give_up_parking"] = data_formatted.apply(get_give_up_parking, axis=1)

print(
    "Checking whether give_up_parking is done right: \n",
    data_formatted["give_up_parking"].value_counts(dropna=False),
)

print("\n" + "=" * 80)


def get_conditional_choice(row):
    """Recover the mode chosen after giving up parking rights."""
    if pd.isna(row["experiment"]) or pd.isna(row["block"]):
        return pd.NA

    raw = clean_data.loc[clean_data["ResponseId"] == row["ResponseId"]].iloc[0]

    anchor_col = block_anchors[int(row["experiment"])][row["block"]][0]
    start_idx = clean_data.columns.get_loc(anchor_col)

    task_pos = block_task_map[row["block"]].index(row["task"])
    cond_idx = start_idx + task_pos * 3 + 2

    if cond_idx >= len(clean_data.columns):
        return pd.NA

    return normalize_mode(raw.iloc[cond_idx])


def get_final_choice(row):
    """Construct the final task choice from the parking-rights decision."""
    give_up = row["give_up_parking"]

    if pd.isna(give_up):
        return pd.NA

    if give_up == "Yes":
        return get_conditional_choice(row)

    if give_up == "No":
        return row["base_choice"]

    return pd.NA

data_formatted["final_choice"] = data_formatted.apply(get_final_choice, axis=1)

print(
    "Checking whether final_choice was created correctly: \n",
    data_formatted["final_choice"].value_counts(dropna=False),
)

print("# Invalid car choices when give_up = Yes:")

invalid = data_formatted[
    (data_formatted["give_up_parking"] == "Yes") &
    (data_formatted["final_choice"] == "car")
]

print("Number of invalid car choices:", len(invalid))
print(invalid[["base_choice", "final_choice"]].head(20))

print("\n" + "=" * 80)
print("Analyzing mode choice after giving up parking rights (base choice = car)")

car_base_df = data_formatted.loc[
    data_formatted["base_choice"] == "car"
    ].copy()

print("Number of task observations with base choice = car:", car_base_df.shape[0])

gave_up_parking_df = car_base_df.loc[
    car_base_df["give_up_parking"] == "Yes"
    ].copy()

print("Number of task observations where parking was given up:", gave_up_parking_df.shape[0])

print("Final mode choice after giving up parking (counts):")
final_choice_counts = gave_up_parking_df["final_choice"].value_counts(dropna=False)
print(final_choice_counts)

print("\nFinal mode choice after giving up parking (percentages):")
final_choice_percentages = (
        final_choice_counts / final_choice_counts.sum() * 100
).round(1)
print(final_choice_percentages)

final_choice_summary = pd.DataFrame({
    "count": final_choice_counts,
    "percentage": final_choice_percentages
})

print("\nSummary table: Mode chosen after giving up parking (base choice = car)")
print(final_choice_summary)

print("\n" + "=" * 80)

# Merge the final 24-row Ngene design with the task-level responses.
design = pd.DataFrame({
    "task": list(range(1, 25)),
    "car.parking_cost": [
        3, 1.5, 3, 1.5, 1.5, 0, 0, 0, 3, 0, 0, 1.5, 3, 0, 3, 1.5, 3, 1.5, 3, 1.5, 1.5, 0, 3, 0
    ],
    "car.parking_reservation": [
        2, 0, 2, 0, 1, 2, 0, 2, 2, 1, 0, 1, 1, 0, 0, 2, 1, 2, 0, 1, 1, 1, 0, 2
    ],
    "parkride.pr_reward": [
        0, 1.5, 0, 1.5, 1.5, 0, 1.5, 3, 3, 3, 1.5, 3, 0, 1.5, 3, 1.5, 0, 3, 0, 1.5, 3, 0, 3, 0
    ],
    "vanpool.vp_taxi_guarantee": [
        0, 1, 1, 0, 1, 1, 1, 0, 1, 0, 0, 1, 0, 1, 1, 1, 1, 0, 0, 0, 1, 0, 0, 0
    ],
    "vanpool.vp_departures_per_hour": [
        4, 4, 1, 4, 4, 1, 4, 2, 1, 2, 2, 1, 1, 1, 1, 4, 1, 2, 2, 4, 4, 2, 2, 2
    ]
})

data_formatted = data_formatted.merge(design, on="task", how="left")

for col in [
    "car.parking_cost",
    "car.parking_reservation",
    "parkride.pr_reward",
    "vanpool.vp_taxi_guarantee",
    "vanpool.vp_departures_per_hour",
]:
    print(f"\nValue counts for {col}:")
    print(data_formatted[col].value_counts(dropna=False))

print("\n" + "=" * 80)

# Add respondent-level follow-up answers and derived parking variables.
data_formatted["give_up_parking_any_answer"] = data_formatted["ResponseId"].map(
    clean_data.set_index("ResponseId")["Q626"]
)

print(
    "Checking whether give_up_parking_any_answer works",
    data_formatted["give_up_parking_any_answer"].value_counts(dropna=False),
)

gave_up_parking_any = (data_formatted.groupby("ResponseId")["give_up_parking"]
                       .apply(lambda x: "Yes" if (x == "Yes").any() else "No"))

data_formatted["gave_up_parking_any"] = data_formatted["ResponseId"].map(gave_up_parking_any)

print("Checking gave_up_parking from task level choices:")
print(
    data_formatted[
        [
            "ResponseId",
            "give_up_parking",
            "gave_up_parking_any",
            "give_up_parking_any_answer",
        ]
    ].head(30)
)
print(data_formatted["gave_up_parking_any"].value_counts(dropna=False))

data_formatted["reward_choice_if_gave_up_parking"] = data_formatted["ResponseId"].map(
    clean_data.set_index("ResponseId")["Q627"]
)

print("Checking if final_parking_give up works", data_formatted["reward_choice_if_gave_up_parking"]
      .value_counts(dropna=False))

data_formatted["reason_not_giving_up_parking"] = data_formatted["ResponseId"].map(
    clean_data.set_index("ResponseId")["Q628"]
)

data_formatted["additional_comments"] = data_formatted["ResponseId"].map(
    clean_data.set_index("ResponseId")["Q643"]
)

data_formatted["parking_guaranteed"] = 0

data_formatted.loc[
    data_formatted["car.parking_reservation"] == 1,
    "parking_guaranteed"
] = 1

data_formatted.loc[
    (data_formatted["car.parking_reservation"] == 2)
    & (data_formatted["commute_distance_km"] > 20),
    "parking_guaranteed"
] = 1

data_formatted["bike_allowance"] = (
    data_formatted["ResponseId"]
    .map(clean_data.set_index("ResponseId")["bike_allowance"])
    .str.replace("€", "", regex=False)
    .astype(float)
)

data_formatted["car_allowance"] = (
    data_formatted["ResponseId"]
    .map(clean_data.set_index("ResponseId")["car_allowance"])
    .str.replace("€", "", regex=False)
    .astype(float)
)

print("\n" + "=" * 80)
print("In the formatted dataset, you can find: ")
print(data_formatted.columns)
print(" ")
print(data_formatted.head(20))

# Save the formatted task-level SCE dataset.
data_formatted.to_excel(
    r"data\Access & Mobility Survey Formatted Data.xlsx",
    index=False
)
