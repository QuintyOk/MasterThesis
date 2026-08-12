"""Estimate the binary logit model for giving up regular parking rights.

The script prepares the repeated parking-rights decisions, estimates the binary
Biogeme model, reports fitted probabilities, and simulates the policy attributes
under the common base case.

The original analytical specification is retained. Review the alternative
coding note beside the utility functions before re-estimating the model."""

import pandas as pd
import biogeme.biogeme as bio
import biogeme.database as db
import biogeme.models as models
from biogeme.expressions import Beta, Variable
from biogeme.results_processing import get_pandas_estimated_parameters

pd.set_option("display.max_rows", None)
pd.set_option("display.max_columns", None)
pd.set_option("display.width", None)
pd.set_option("display.max_colwidth", None)

# Load the formatted task-level SCE dataset.
data = pd.read_excel(
    r"data\Access & Mobility Survey Formatted Data.xlsx",
    engine="openpyxl"
)

# Retain respondents who entered an SCE experiment.
data = data.loc[data["experiment"].notna()].copy()

data["ResponseId_num"] = (
    data["ResponseId"]
    .astype("category")
    .cat.codes
)

choice_map = {
    "car": 1,
    "pr": 2,
    "vanpool": 3,
    "pt": 4,
    "bike": 5,
}

print("\nRows after car-base filter:", len(data))

# Convert the repeated Yes and No decisions to the numeric outcome.
data["give_up_parking_num"] = data["give_up_parking"].map({"Yes": 1, "No": 0})
data = data.loc[data["give_up_parking_num"].notna()].copy()
data["give_up_parking_num"] = data["give_up_parking_num"].astype(int)

print("=" * 50)
print("Data has been processed for Biogeme use...")

data["car_av"] = (data["car_available"] != "No, (almost) never").astype(int)
data["bike_av"] = (data["bike_available"] == "Yes").astype(int)
data["vanpool_av"] = (data["vanpool_available"] == "Yes").astype(int)
data["pt_av"] = 1
data["pr_av"] = data["car_av"]

print("Availability variables created...")
print("=" * 50)

# Keep the variables used in the binary model specification.
choice_data = data[
    [
        "ResponseId_num",
        "commute_distance_km",
        "give_up_parking_num",
        "car_av",
        "pr_av",
        "vanpool_av",
        "pt_av",
        "bike_av",
        "car.parking_cost",
        "car.parking_reservation",
        "parkride.pr_reward",
        "vanpool.vp_taxi_guarantee",
        "vanpool.vp_departures_per_hour",
        "parking_guaranteed"
    ]
]

print("New dataset ""choice_data"" created for Biogeme use...")

# Create the Biogeme database and expressions.
database = db.Database("mnl_data", choice_data)

print("Created a Biogeme database object from ""choice_data...")
print("=" * 50)

CHOICE = Variable("give_up_parking_num")

print("Choice variable defined (give_up_parking)...")

parking_cost = Variable("car.parking_cost")
pr_reward = Variable("parkride.pr_reward")
vp_taxi = Variable("vanpool.vp_taxi_guarantee")
vp_freq = Variable("vanpool.vp_departures_per_hour")
parking_guaranteed = Variable("parking_guaranteed")

print("Explanatory variables defined (the policy levers)...")

ASC_YES = Beta("ASC_YES", 0, None, None, 0)
ASC_NO = Beta("ASC_NO", 0, None, None, 1)

B_PARK_COST = Beta("B_PARK_COST", 0, None, None, 0)
B_PARK_GUAR = Beta("B_PARK_GUAR", 0, None, None, 0)
B_PR_REWARD = Beta("B_PR_REWARD", 0, None, None, 0)
B_VP_TAXI = Beta("B_VP_TAXI", 0, None, None, 0)
B_VP_FREQ = Beta("B_VP_FREQ", 0, None, None, 0)

print("ASC's and coefficients to estimate defined...")

# Coding verification note.
# The original script maps Yes to 1 and No to 0, while the parameterised
# utility below is assigned to alternative 0 and labelled Prob_yes later.
# This specification is preserved to avoid changing the reported analysis.
# Verify the alternative coding before using the script for re-estimation.
V = {
    0: (
        ASC_YES
        + B_PARK_COST * parking_cost
        + B_PARK_GUAR * parking_guaranteed
        + B_PR_REWARD * pr_reward
        + B_VP_TAXI * vp_taxi
        + B_VP_FREQ * vp_freq
    ),
    1: 0,
}

print("Utility function defined...")

AV = {
    0: 1,
    1: 1,
}

print("Availability conditions defined...")
print("=" * 50)

# Estimate the binary logit model.
logprob = models.loglogit(V, AV, CHOICE)

biogeme = bio.BIOGEME(database, logprob)
biogeme.model_name = "Give Up Parking Binary Logit"

print("MNL and biogeme model object defined...")

results = biogeme.estimate()

print("Model parameters estimated...")
print("=" * 50)

print(results.short_summary())

estimated_parameters = get_pandas_estimated_parameters(
    estimation_results=results
)
print("Estimation results of parameters:")
print(estimated_parameters)

# Calculate fitted probabilities using the original alternative labels.
simulate = {
    "Prob_yes": models.logit(V, AV, 0),
    "Prob_no": models.logit(V, AV, 1),
}

biogeme_simulate = bio.BIOGEME(database, simulate)
simulated_values = biogeme_simulate.simulate(results.get_beta_values())

simulated_values["experiment"] = data["experiment"].values

average_probs = simulated_values[[
    "Prob_yes",
    "Prob_no"
]].mean()

print("\n=== Overall average probabilities ===")
print(average_probs)

print("\n=== Average parking-rights probabilities per experiment")

average_probs_experiment = (
    simulated_values.groupby("experiment")[[
        "Prob_yes",
        "Prob_no"
    ]]
    .mean()
)
print(average_probs_experiment)

# Reuse the estimated parameters for counterfactual policy scenarios.
def simulate_scenario(choice_data, V, AV, results, scenario, label):
    """Simulate average parking-rights probabilities for one scenario."""

    print("\n------------------------------------------------------------")
    print(f"Simulating scenario: {label}")
    print("Applied attribute values:")
    for k, v in scenario.items():
        print(f"  - {k}: {v}")

    scenario_data = choice_data.copy()

    for col, val in scenario.items():
        scenario_data[col] = val

    database_scenario = db.Database("scenario", scenario_data)

    simulate = {
        "Prob_yes": models.logit(V, AV, 0),
        "Prob_no": models.logit(V, AV, 1),
    }

    biogeme_sim = bio.BIOGEME(database_scenario, simulate)
    probs = biogeme_sim.simulate(results.get_beta_values())

    avg_probs = probs.mean()

    print("Average predicted choice probabilities:")
    print(avg_probs)

    return avg_probs

print("\n==================== BASE CASE SCENARIO ====================")

# Define the common reference scenario.
base_case = {
    "car.parking_cost": 0,
    "parking_guaranteed": 1,
    "parkride.pr_reward": 0,
    "vanpool.vp_taxi_guarantee": 0,
    "vanpool.vp_departures_per_hour": 1,
}

base_probs = simulate_scenario(
    choice_data=choice_data,
    V=V,
    AV=AV,
    results=results,
    scenario=base_case,
    label="Base case: all attributes = 0"
)

base_df = pd.DataFrame([base_probs])
print("\nBASE CASE SUMMARY")
print(base_df)

print("\n==================== PARKING COST SCENARIOS ====================")

# Simulate the tested parking-payment levels.
parking_cost_values = [0, 1.5, 3]

results_list = []

for cost in parking_cost_values:

    scenario = base_case.copy()
    scenario["car.parking_cost"] = cost

    probs = simulate_scenario(
        choice_data=choice_data,
        V=V,
        AV=AV,
        results=results,
        scenario=scenario,
        label=f"Parking cost = {cost}"
    )

    probs_dict = probs.to_dict()
    probs_dict["parking_cost"] = cost
    results_list.append(probs_dict)

parking_scenarios_df = pd.DataFrame(results_list)

print("\nPARKING COST SCENARIOS SUMMARY")
print(parking_scenarios_df)

print("\n==================== PARKING GUARANTEED SCENARIOS ====================")

# Simulate parking without and with a guarantee.
parking_guaranteed_values = [0, 1]

results_list = []

for guar in parking_guaranteed_values:

    scenario = base_case.copy()
    scenario["parking_guaranteed"] = guar

    probs = simulate_scenario(
        choice_data=choice_data,
        V=V,
        AV=AV,
        results=results,
        scenario=scenario,
        label=f"Parking guaranteed = {guar}"
    )

    probs_dict = probs.to_dict()
    probs_dict["parking_guaranteed"] = guar
    results_list.append(probs_dict)

parking_guaranteed_df = pd.DataFrame(results_list)

print("\nPARKING GUARANTEED SCENARIOS SUMMARY")
print(parking_guaranteed_df)

print("\n==================== P+R REWARD SCENARIOS ====================")

# Simulate the tested P&R reward levels.
pr_reward_values = [0, 1.5, 3]

results_list = []

for reward in pr_reward_values:

    scenario = base_case.copy()
    scenario["parkride.pr_reward"] = reward

    probs = simulate_scenario(
        choice_data=choice_data,
        V=V,
        AV=AV,
        results=results,
        scenario=scenario,
        label=f"P+R reward = {reward}"
    )

    probs_dict = probs.to_dict()
    probs_dict["pr_reward"] = reward
    results_list.append(probs_dict)

pr_reward_df = pd.DataFrame(results_list)

print("\nP+R REWARD SCENARIOS SUMMARY")
print(pr_reward_df)
