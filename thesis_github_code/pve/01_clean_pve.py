"""Clean the raw Participatory Value Evaluation (PVE) Qualtrics export.

The script removes unused Qualtrics metadata, preview responses, responses
outside the fieldwork period, incomplete surveys, and respondents outside the
selected campus. It preserves the Qualtrics label row and writes the cleaned
PVE Excel file used by the remaining scripts.

The raw survey data are confidential and are not included in the repository."""

import pandas as pd

# Load the raw PVE and acceptability survey export.
raw_data = pd.read_excel(
    r"data\Access & Mobility Survey Acceptability Raw Data.xlsx", engine="openpyxl"
)

pd.set_option('display.max_rows', None)

pd.set_option('display.max_columns', None)

pd.set_option('display.max_colwidth', None)

pd.set_option('display.width', None)

print("raw qualtrics", len(raw_data))

print("\n" + "=" * 80)

print("Raw columns:")
print(list(raw_data.columns))
print("Number of respondents:", raw_data.shape)

# Remove metadata that is not used in the analysis.
columns_to_drop = [
    "RecipientLastName",
    "RecipientFirstName",
    "RecipientEmail",
    "ExternalReference",
    "LocationLatitude",
    "LocationLongitude",
    "UserLanguage",
    "IPAddress",
    "Status"
]

clean_data = raw_data.drop(columns=columns_to_drop)

print("Clean columns:")
print(list(clean_data.columns))

print("Number of respondents:", clean_data.shape)

# Store the Qualtrics question-label row before filtering respondents.
label_row = clean_data.iloc[[0]]

clean_data = clean_data.iloc[1:].copy()

print("\n" + "=" * 80)

# Parse the Qualtrics timestamp fields.
date_columns = ["StartDate", "EndDate", "RecordedDate"]

print(clean_data.columns)

for col in date_columns:
    clean_data[col] = pd.to_datetime(
        clean_data[col],
        format="%m/%d/%Y %I:%M:%S %p",
    )

print(
    "The types of date columns:",
    clean_data[["StartDate", "EndDate", "RecordedDate"]].dtypes,
)

print("Number of respondents:", clean_data.shape)

print("Clean columns:")
print(list(clean_data.columns))

clean_data = clean_data.convert_dtypes()
print(clean_data.dtypes)

print("\n" + "=" * 80)

print(
    "Types of distribution channels: ",
    clean_data["DistributionChannel"].value_counts(dropna=False),
)

# Keep anonymous field responses and remove survey previews.
clean_data = clean_data.loc[clean_data["DistributionChannel"] == "anonymous"].copy()

print(
    "Verifying check that all previews are gone: ",
    clean_data["DistributionChannel"].value_counts(),
)
print("Number of respondents:", clean_data.shape)

print("\n" + "=" * 80)

# Exclude responses recorded before the official fieldwork start.
cutoff_datetime = pd.Timestamp("2026-06-10 14:00:00")
print("Before cutoff time:", clean_data["RecordedDate"].min())
print(
    "Timestamps \n :",
    clean_data["RecordedDate"].dt.date.value_counts().sort_index(),
)
print(clean_data["RecordedDate"].dtype)

clean_data = clean_data[
    clean_data["RecordedDate"] >= cutoff_datetime
].reset_index(drop=True)

print("Minimum timestamp in data")
print(clean_data["RecordedDate"].min())
print("Number of respondents after time cutoff:", clean_data.shape)

print("\n" + "=" * 80)

# Retain fully completed surveys.
clean_data["Finished"] = clean_data["Finished"].map({"True": True, "False": False})
clean_data["Progress"] = clean_data["Progress"].astype(int)

print(
    "Types of Finished values:",
    clean_data["Finished"].value_counts(dropna=False),
)

unfinished_df = clean_data.loc[
    clean_data["Finished"] == False,
    ["ResponseId", "Finished", "Progress"],
]
print(unfinished_df)

clean_data = clean_data.loc[clean_data["Progress"] >= 100].copy()

print(clean_data["Progress"].value_counts())
print("Number of respondents after progress cutoff:", clean_data.shape)

print("\n" + "=" * 80)

# Inspect completion times without excluding respondents on duration alone.
print("Duration descriptive statistics: ")
print(
    clean_data.loc[
        clean_data["Progress"] == 100, "Duration (in seconds)"
    ].describe()
)

print("People that took longer than 1 hour to complete survey: ")
print(
    clean_data.loc[
        (clean_data["Progress"] == 100)
        & (clean_data["Duration (in seconds)"] > 3600),
        ["ResponseId", "Duration (in seconds)"],
    ]
)

print("People that took less than 5 minutes to complete survey: ")
print(
    clean_data.loc[
        (clean_data["Progress"] == 100)
        & (clean_data["Duration (in seconds)"] < 300),
        ["ResponseId", "Duration (in seconds)"],
    ]
)

print("\n" + "=" * 80)

print("Number of people that work on campus")
print(clean_data["Q19"].value_counts(dropna=False))

# Restrict the sample to employees working at De Run 6000/1000.
clean_data = clean_data[clean_data["Q19"] == "On campus (De Run 6000/1000)"].copy()

print(clean_data["Q19"].value_counts())

print("Final Number of respondents:", clean_data.shape)

print("\n" + "=" * 80)

# Restore the Qualtrics label row for compatibility with later scripts.
clean_data = pd.concat([label_row, clean_data], ignore_index=True)

# Save the cleaned PVE dataset.
clean_data.to_excel(
    r"data\Access & Mobility Survey Acceptability Clean Data.xlsx",
    index=False
)
