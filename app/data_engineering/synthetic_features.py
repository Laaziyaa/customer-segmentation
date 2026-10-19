import random
import numpy as np
import pandas as pd

from .business_rules import (
    JOB_SALARY_RANGE,
    EDUCATION_MULTIPLIER
)


class SyntheticFeatureGenerator:

    def __init__(self):

        random.seed(42)
        np.random.seed(42)

    def generate(self, dataframe):

        df = dataframe.copy()

        df.insert(0, "customer_id", range(1, len(df) + 1))

        # Level 1
        df["annual_income"] = df.apply(
            self.generate_income,
            axis=1
        )

        df["credit_score"] = df.apply(
            self.generate_credit_score,
            axis=1
        )

        # Level 2
        df["account_balance"] = df.apply(
            self.generate_account_balance,
            axis=1
        )

        df["digital_banking_score"] = df.apply(
            self.generate_digital_score,
            axis=1
        )

        # Level 3
        df["monthly_transactions"] = df.apply(
            self.generate_monthly_transactions,
            axis=1
        )

        df["investment_amount"] = df.apply(
            self.generate_investment,
            axis=1
        )

        # Level 4
        df["avg_transaction_amount"] = df.apply(
            self.generate_avg_transaction,
            axis=1
        )

        df["account_tenure"] = df.apply(
            self.generate_tenure,
            axis=1
        )

        df["number_of_products"] = df.apply(
            self.generate_products,
            axis=1
        )

        return df

    def generate_income(self, row):

        job = row["job"]

        if pd.isna(job):
            job = "services"

        low, high = JOB_SALARY_RANGE.get(
            job,
            (400000, 700000)
        )

        income = random.randint(low, high)

        multiplier = EDUCATION_MULTIPLIER.get(
            row["education"],
            1.0
        )

        income *= multiplier

        age = row["age"]

        if age < 25:
            income *= 0.9

        elif age > 45:
            income *= 1.15

        return int(income)

    def generate_credit_score(self, row):

        score = random.randint(620, 760)

        if row["default"] == "yes":
            score -= 120

        if row["housing"] == "yes":
            score -= 15

        if row["loan"] == "yes":
            score -= 20

        education = row["education"]

        if education == "university.degree":
            score += 25

        elif education == "professional.course":
            score += 15

        elif education in ["basic.4y", "basic.6y", "basic.9y"]:
            score -= 20

        age = row["age"]

        if age < 25:
            score -= 10

        elif age > 45:
            score += 10

        job = row["job"]

        if job == "management":
            score += 25

        elif job == "entrepreneur":
            score += 15

        elif job == "unemployed":
            score -= 35

        elif job == "student":
            score -= 20

        return max(300, min(score, 850))

    def generate_account_balance(self, row):

        income = row["annual_income"]

        balance = income * random.uniform(0.30, 1.40)

        if row["credit_score"] > 780:
            balance *= 1.25

        elif row["credit_score"] < 550:
            balance *= 0.75

        if row["age"] > 50:
            balance *= 1.15

        return round(balance, 2)

    def generate_monthly_transactions(self, row):

        base = random.randint(10, 40)

        if row["digital_banking_score"] > 80:
            base += random.randint(20, 35)

        elif row["digital_banking_score"] > 60:
            base += random.randint(10, 20)

        if row["job"] == "management":
            base += 10

        elif row["job"] == "entrepreneur":
            base += 15

        elif row["job"] == "student":
            base += 8

        return base

    def generate_avg_transaction(self, row):

        return round(
            row["account_balance"] /
            row["monthly_transactions"] *
            random.uniform(0.02, 0.06),
            2
        )

    def generate_investment(self, row):

        investment = row["account_balance"] * random.uniform(0.10, 0.50)

        if row["annual_income"] > 100000:
            investment *= 1.3

        return round(investment, 2)

    def generate_digital_score(self, row):

        score = 100 - row["age"]

        if row["education"] == "university.degree":
            score += 12

        elif row["education"] == "professional.course":
            score += 8

        elif row["education"] in [
            "basic.4y",
            "basic.6y",
            "basic.9y"
        ]:
            score -= 10

        return max(0, min(score, 100))

    def generate_tenure(self, row):

        max_tenure = max(1, min(30, row["age"] - 18))

        return random.randint(1, max_tenure)

    def generate_products(self, row):

        products = 1

        if row["annual_income"] > 70000:
            products += 1

        if row["account_balance"] > 60000:
            products += 1

        if row["credit_score"] > 720:
            products += 1

        if row["age"] > 45:
            products += 1

        if row["investment_amount"] > 50000:
            products += 1

        return min(products, 6)