import pandas as pd

from app.config import RAW_DATA_PATH

# Read the dataset
df = pd.read_csv(
    RAW_DATA_PATH,
    sep=";"
)

print("=" * 50)
print("Dataset Shape")
print("=" * 50)
print(df.shape)

print()

print("=" * 50)
print("Columns")
print("=" * 50)
print(df.columns.tolist())

print()

print("=" * 50)
print("First Five Rows")
print("=" * 50)
print(df.head())

print()

print("=" * 50)
print("Data Types")
print("=" * 50)
print(df.dtypes)

print()

print("=" * 50)
print("Missing Values")
print("=" * 50)
print(df.isnull().sum())

print()

print("=" * 50)
print("Unknown Values")
print("=" * 50)

for column in df.columns:

    if df[column].dtype == "object":

        unknown = (df[column] == "unknown").sum()

        print(f"{column:20} {unknown}")