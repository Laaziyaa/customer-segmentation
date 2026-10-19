from pathlib import Path
import pandas as pd


class PersonaGenerator:

    def __init__(self):

        self.project_root = Path(__file__).resolve().parents[2]

        self.output_dir = (
            self.project_root
            / "data"
            / "processed"
        )

    def generate(self, summary):

        personas = []

        for cluster in summary.index:

            row = summary.loc[cluster]

            if (
                row["average_income"] > 120000
                and row["average_products"] >= 4
            ):

                persona = "Premium Wealth Customers"

            elif (
                row["average_digital_score"] >= 70
            ):

                persona = "Digital Professionals"

            elif (
                row["average_income"] < 50000
                and row["average_products"] < 2
            ):

                persona = "Emerging Customers"

            else:

                persona = "Traditional Banking Customers"

            personas.append(
                {
                    "cluster": cluster,
                    "persona": persona
                }
            )

        persona_df = pd.DataFrame(personas)

        output_path = (
            self.output_dir
            / "customer_personas.csv"
        )

        persona_df.to_csv(
            output_path,
            index=False
        )

        print("\nGenerated Customer Personas\n")
        print(persona_df)

        print(f"\nSaved to:\n{output_path}")

        return persona_df