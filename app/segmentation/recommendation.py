from pathlib import Path
import pandas as pd


class RecommendationEngine:

    def __init__(self):

        self.project_root = Path(__file__).resolve().parents[2]

        self.output_dir = (
            self.project_root
            / "data"
            / "processed"
        )

        self.recommendations = {

            "Premium Wealth Customers": [
                "Premium Savings Account",
                "Wealth Management",
                "Mutual Funds",
                "Platinum Credit Card",
                "Dedicated Relationship Manager"
            ],

            "Digital Professionals": [
                "Digital Savings Account",
                "UPI Cashback Rewards",
                "Travel Credit Card",
                "SIP Investment Plan",
                "Mobile Banking Premium"
            ],

            "Emerging Customers": [
                "Basic Savings Account",
                "Micro Personal Loan",
                "Debit Card Cashback",
                "Financial Literacy Program",
                "Goal-Based Savings Plan"
            ],

            "Traditional Banking Customers": [
                "Fixed Deposit",
                "Senior Citizen Benefits",
                "Home Loan",
                "Insurance Plans",
                "Branch Banking Assistance"
            ]
        }

    def generate(self, persona_df):

        recommendation_list = []

        for _, row in persona_df.iterrows():

            recommendation_list.append({

                "cluster": row["cluster"],

                "persona": row["persona"],

                "recommended_products": ", ".join(
                    self.recommendations[row["persona"]]
                )
            })

        recommendation_df = pd.DataFrame(recommendation_list)

        output_path = (
            self.output_dir
            / "customer_recommendations.csv"
        )

        recommendation_df.to_csv(
            output_path,
            index=False
        )

        print("\nCustomer Recommendations\n")

        print(recommendation_df)

        print(f"\nSaved to:\n{output_path}")

        return recommendation_df