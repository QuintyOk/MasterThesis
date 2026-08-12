"""Estimate the SCE base-choice multinomial logit model.

The script prepares the task-level SCE data for Biogeme, estimates the base-
choice model, reports average predicted probabilities, and simulates the
individual parking and P&R policies and their full scenario grid.

Model specification and scenario logic are preserved from the final analysis."""

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

# Prepare the choice and availability variables required by Biogeme.
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

data["base_choice_num"] = data["base_choice"].map(choice_map).astype(int)

print("=" * 50)
print("Data has been processed for Biogeme use...")

data["car_av"] = (data["car_available"] != "No, (almost) never").astype(int)
data["bike_av"] = (data["bike_available"] == "Yes").astype(int)
data["vanpool_av"] = (data["vanpool_available"] == "Yes").astype(int)
data["pt_av"] = 1
data["pr_av"] = data["car_av"]

print("Availability variables created...")
print("=" * 50)

# Keep the variables used in the model specification.
choice_data = data[
    [
        "ResponseId_num",
        "commute_distance_km",
        "base_choice_num",
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

# Create the Biogeme database and model expressions.
database = db.Database("mnl_data", choice_data)

print("Created a Biogeme database object from ""choice_data...")
print("=" * 50)

CHOICE = Variable("base_choice_num")

print("Choice variable defined (base_choice)...")

parking_cost = Variable("car.parking_cost")
pr_reward = Variable("parkride.pr_reward")
vp_taxi = Variable("vanpool.vp_taxi_guarantee")
vp_freq = Variable("vanpool.vp_departures_per_hour")
parking_guaranteed = Variable("parking_guaranteed")
commute_distance = Variable("commute_distance_km")

print("Explanatory variables defined (the policy levers)...")

ASC_CAR = Beta("ASC_CAR", 0, None, None, 1)
ASC_PR = Beta("ASC_PR", 0, None, None, 0)
ASC_VP = Beta("ASC_VP", 0, None, None, 0)
ASC_PT = Beta("ASC_PT", 0, None, None, 0)
ASC_BIKE = Beta("ASC_BIKE", 0, None, None, 0)

B_PARK_COST = Beta("B_PARK_COST", 0, None, None, 0)
B_PARK_GUAR = Beta("B_PARK_GUAR", 0, None, None, 0)
B_PR_REWARD = Beta("B_PR_REWARD", 0, None, None, 0)
B_VP_TAXI = Beta("B_VP_TAXI", 0, None, None, 0)
B_VP_FREQ = Beta("B_VP_FREQ", 0, None, None, 0)
B_DISTANCE = Beta("B_DISTANCE", 0, None, None, 0)

print("ASC's and coefficients to estimate defined...")

# Specify alternative utilities. Direct car is the ASC reference.
V = {
    1: ASC_CAR + B_PARK_COST * parking_cost + B_PARK_GUAR * parking_guaranteed,
    2: ASC_PR + B_PR_REWARD * pr_reward,
    3: ASC_VP + B_VP_TAXI * vp_taxi + B_VP_FREQ * vp_freq,
    4: ASC_PT,
    5: ASC_BIKE,
}

print("Utility function defined...")

car_av = Variable("car_av")
pr_av = car_av
vanpool_av = Variable("vanpool_av")
pt_av = 1
bike_av = Variable("bike_av")

AV = {
    1: car_av,
    2: pr_av,
    3: vanpool_av,
    4: pt_av,
    5: bike_av,
}

print("Availability conditions defined...")
print("=" * 50)

# Estimate the multinomial logit model.
logprob = models.loglogit(V, AV, CHOICE)

biogeme = bio.BIOGEME(database, logprob)
biogeme.model_name = "Base Choice MNL Model"

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

# Calculate fitted choice probabilities for the observed tasks.
simulate = {
    "Prob_car": models.logit(V, AV, 1),
    "Prob_pr": models.logit(V, AV, 2),
    "Prob_vp": models.logit(V, AV, 3),
    "Prob_pt": models.logit(V, AV, 4),
    "Prob_bike": models.logit(V, AV, 5),
}

biogeme_simulate = bio.BIOGEME(database, simulate)
simulated_values = biogeme_simulate.simulate(results.get_beta_values())

simulated_values["experiment"] = data["experiment"].values

average_probs = simulated_values[[
    "Prob_car",
    "Prob_pr",
    "Prob_vp",
    "Prob_pt",
    "Prob_bike"
]].mean()

print("\n=== Overall average probabilities ===")
print(average_probs)

print("\n=== Average probabilities per experiment (base choice)")

average_probs_experiment = (
    simulated_values.groupby("experiment")[[
        "Prob_car",
        "Prob_pr",
        "Prob_vp",
        "Prob_pt",
        "Prob_bike"
    ]]
    .mean()
)
print(average_probs_experiment)

# Reuse the estimated parameters for counterfactual policy scenarios.
def simulate_scenario(choice_data, V, AV, results, scenario, label):
    """Simulate average choice probabilities for one policy scenario."""

    print("\n------------------------------------------------------------")
    print(f"Simulating scenario: {label}")
    print("Applied attribute values:")
    for k, v in scenario.items():
        print(f"  - {k}: {v}")

    scenario_data = choice_data.copy()

    for col, val in scenario.items():
        if callable(val):
            scenario_data[col] = val(scenario_data)
        else:
            scenario_data[col] = val

    database_scenario = db.Database("scenario", scenario_data)

    simulate = {
        "Prob_car": models.logit(V, AV, 1),
        "Prob_pr": models.logit(V, AV, 2),
        "Prob_vp": models.logit(V, AV, 3),
        "Prob_pt": models.logit(V, AV, 4),
        "Prob_bike": models.logit(V, AV, 5),
    }

    biogeme_sim = bio.BIOGEME(database_scenario, simulate)
    probs = biogeme_sim.simulate(results.get_beta_values())

    avg_probs = probs.mean()
    if "parking_guaranteed" in scenario:
        print("Parking-guarantee distribution in this scenario:")
        print(scenario_data["parking_guaranteed"].value_counts())

    print("Average predicted choice probabilities:")
    print(avg_probs)

    return avg_probs

print("\n==================== BASE CASE SCENARIO ====================")

# Define the common reference scenario used throughout the simulations.
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

# Simulate each tested parking-payment level.
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

# Simulate no reservation, standard reservation, and distance priority.
priority_rule = lambda df: (df["commute_distance_km"] > 20).astype(int)

scenarios = [
    ("no_reservation", 0),
    ("standard_reservation", 1),
    ("priority_reservation", priority_rule)
]

results_list = []

for label, guar in scenarios:
    scenario = base_case.copy()
    scenario["parking_guaranteed"] = guar

    probs = simulate_scenario(
        choice_data=choice_data,
        V=V,
        AV=AV,
        results=results,
        scenario=scenario,
        label=label
    )

    probs_dict = probs.to_dict()
    probs_dict["scenario"] = label
    results_list.append(probs_dict)

parking_guaranteed_df = pd.DataFrame(results_list)

print("\nPARKING GUARANTEED SCENARIOS SUMMARY")
print(parking_guaranteed_df)

print("\n==================== P+R REWARD SCENARIOS ====================")

# Simulate each tested P&R reward level.
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

print("\n==================== PERCENTAGE CHANGE ====================")

base_dict = base_probs.to_dict()

# Express each modal probability relative to the base case.
def compute_pct_change(df, scenario_col):
    """Add relative percentage changes from the base case."""
    df_pct = df.copy()

    for mode in ["Prob_car", "Prob_pr", "Prob_vp", "Prob_pt", "Prob_bike"]:
        base_val = base_dict[mode]

        if base_val != 0:
            df_pct[f"{mode}_pct_change"] = (df_pct[mode] - base_val) / base_val * 100
        else:
            df_pct[f"{mode}_pct_change"] = None

    return df_pct

parking_cost_pct = compute_pct_change(parking_scenarios_df, "parking_cost")
parking_guaranteed_pct = compute_pct_change(parking_guaranteed_df, "parking_guaranteed")
pr_reward_pct = compute_pct_change(pr_reward_df, "pr_reward")

print("\n--- Parking Cost (% change vs base) ---")
print(parking_cost_pct)

print("\n--- Parking Guaranteed (% change vs base) ---")
print(parking_guaranteed_pct)

print("\n--- P+R Reward (% change vs base) ---")
print(pr_reward_pct)

print("\n==================== FULL SCENARIO GRID ====================")

import itertools

parking_cost_values = [0, 1.5, 3]
# Evaluate every parking-payment, reservation, and P&R combination.
parking_guaranteed_values = [
    ("no_reservation", 0),
    ("standard", 1),
    ("priority", priority_rule)
]
pr_reward_values = [0, 1.5, 3]

base_dict = base_probs.to_dict()

results_list = []

for cost, (guar_label, guar), reward in itertools.product(
    parking_cost_values,
    parking_guaranteed_values,
    pr_reward_values
):
    scenario = base_case.copy()
    scenario["car.parking_cost"] = cost
    scenario["parking_guaranteed"] = guar
    scenario["parkride.pr_reward"] = reward

    probs = simulate_scenario(
        choice_data=choice_data,
        V=V,
        AV=AV,
        results=results,
        scenario=scenario,
        label=f"cost={cost}, guar={guar_label}, reward={reward}"
    )

    probs_dict = probs.to_dict()

    base_car = base_dict["Prob_car"]
    scen_car = probs_dict["Prob_car"]

    if base_car != 0:
        pct_change_car = (scen_car - base_car) * 100
    else:
        pct_change_car = None

    results_list.append({
        "Scenario": f"cost={cost}, guar={guar}, reward={reward}",
        "parking_cost": cost,
        "parking_guaranteed": guar_label,
        "pr_reward": reward,
        "pp_change_car": pct_change_car
    })

scenario_grid_df = pd.DataFrame(results_list)

scenario_grid_df = scenario_grid_df.sort_values("pp_change_car")

print("\nRANKED SCENARIO RESULTS (CAR % CHANGE)")
print(scenario_grid_df)
