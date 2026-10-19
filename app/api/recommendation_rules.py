def add_recommendation(recommendations, title, category, reason):
    recommendations.append({
        "title": title,
        "category": category,
        "reason": reason
    })


def get_personalized_recommendations(customer):

    recommendations = []
    warnings = []

    # Student
    if customer["job"] == "student":

        add_recommendation(
            recommendations,
            "Student Savings Account",
            "Banking",
            "Designed for students with zero or low minimum balance requirements."
        )

        add_recommendation(
            recommendations,
            "Zero Balance Account",
            "Banking",
            "Allows students to bank without maintaining a minimum balance."
        )

        add_recommendation(
            recommendations,
            "Education Loan",
            "Loan",
            "Provides financial support for higher education."
        )

        add_recommendation(
            recommendations,
            "Build Credit History",
            "Credit",
            "Start building a healthy credit profile early."
        )

    # Low Credit Score
    if customer["credit_score"] < 650:

        add_recommendation(
            recommendations,
            "Secured Credit Card",
            "Credit",
            "Helps improve your credit score with responsible usage."
        )

        add_recommendation(
            recommendations,
            "Credit Score Improvement Program",
            "Financial Wellness",
            "Provides guidance on improving your credit profile."
        )

        warnings.append(
            "Premium credit card approval may be difficult until your credit score improves."
        )

    # Excellent Credit Score
    elif customer["credit_score"] >= 800:

        add_recommendation(
            recommendations,
            "Platinum Credit Card",
            "Credit",
            "You qualify for premium credit card benefits."
        )

        add_recommendation(
            recommendations,
            "Instant Personal Loan",
            "Loan",
            "Excellent credit score increases loan approval chances."
        )

    # High Income
    if customer["annual_income"] >= 150000:

        add_recommendation(
            recommendations,
            "Wealth Management",
            "Investment",
            "Professional portfolio management for high-income customers."
        )

        add_recommendation(
            recommendations,
            "Tax Saving Investments",
            "Investment",
            "Optimize your taxes through investment planning."
        )

        add_recommendation(
            recommendations,
            "Relationship Manager",
            "Premium Banking",
            "Dedicated banking support for premium customers."
        )

    # Low Balance
    if customer["account_balance"] < 10000:

        add_recommendation(
            recommendations,
            "Emergency Savings Plan",
            "Savings",
            "Build an emergency fund for unexpected expenses."
        )

        add_recommendation(
            recommendations,
            "Budget Tracking",
            "Financial Wellness",
            "Track spending to improve financial stability."
        )

    # High Digital Banking Usage
    if customer["digital_banking_score"] >= 80:

        add_recommendation(
            recommendations,
            "UPI Cashback Rewards",
            "Digital Banking",
            "Earn cashback on frequent digital transactions."
        )

        add_recommendation(
            recommendations,
            "Mobile Banking Premium",
            "Digital Banking",
            "Unlock premium digital banking features."
        )

    # Low Digital Banking Usage
    elif customer["digital_banking_score"] < 40:

        add_recommendation(
            recommendations,
            "Branch Banking Assistance",
            "Customer Support",
            "Personal assistance for your banking needs."
        )

        add_recommendation(
            recommendations,
            "SMS Banking Alerts",
            "Digital Banking",
            "Receive account updates without using mobile banking."
        )

    # Long Relationship
    if customer["account_tenure"] >= 10:

        add_recommendation(
            recommendations,
            "Loyal Customer Benefits",
            "Rewards",
            "Exclusive rewards for long-term customers."
        )

    # Cross Selling
    if customer["number_of_products"] <= 1:

        add_recommendation(
            recommendations,
            "Credit Card",
            "Cross Sell",
            "Expand your banking services with a credit card."
        )

        add_recommendation(
            recommendations,
            "Insurance",
            "Cross Sell",
            "Protect yourself and your family with insurance products."
        )

        add_recommendation(
            recommendations,
            "Fixed Deposit",
            "Investment",
            "Grow your savings through fixed deposits."
        )

    # Remove duplicate recommendations
    seen = set()
    unique_recommendations = []

    for recommendation in recommendations:
        if recommendation["title"] not in seen:
            seen.add(recommendation["title"])
            unique_recommendations.append(recommendation)

    return {
        "personalized_recommendations": unique_recommendations,
        "warnings": warnings
    }