import pandas as pd
import matplotlib.pyplot as plt

# ==============================
# Load dataset
# ==============================
csv_path = "/Users/tarun/My Files/Projects/VIT_Campus_Hackathon - 1/Customer-Segmentation-Agent/data/processed/clustered_customers.csv"

df = pd.read_csv(csv_path)

# ==============================
# Replace this with your actual cluster column name
# ==============================
cluster_col = "cluster"

# Check required columns
if cluster_col not in df.columns:
    print(f"Error: '{cluster_col}' column not found.")
    print("\nAvailable columns:")
    print(df.columns.tolist())
    exit()

if "investment_amount" not in df.columns:
    print("Error: 'investment_amount' column not found.")
    exit()

# ==============================
# Calculate average investment amount
# ==============================
avg_investment = (
    df.groupby(cluster_col)["investment_amount"]
      .mean()
      .sort_index()
      .reset_index()
)

print(avg_investment)

# ==============================
# Plot
# ==============================
plt.figure(figsize=(8, 5))

bars = plt.bar(
    avg_investment[cluster_col].astype(str),
    avg_investment["investment_amount"],
    color="steelblue",
    edgecolor="black"
)

plt.title("Average Investment Amount by Customer Cluster")
plt.xlabel("Customer Cluster")
plt.ylabel("Average Investment Amount")

# Add values above bars
for bar in bars:
    height = bar.get_height()
    plt.text(
        bar.get_x() + bar.get_width() / 2,
        height,
        f"{height:.2f}",
        ha="center",
        va="bottom",
        fontsize=10
    )

plt.grid(axis="y", linestyle="--", alpha=0.5)

# ==============================
# Save graph
# ==============================
output_path = "/Users/tarun/My Files/Projects/VIT_Campus_Hackathon - 1/Customer-Segmentation-Agent/data/outputs/plots/average_cluster_investment_amount.png"

plt.tight_layout()
plt.savefig(output_path, dpi=300, bbox_inches="tight")

print(f"\nGraph saved successfully to:\n{output_path}")

plt.show()