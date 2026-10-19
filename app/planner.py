"""
Turns a parsed intent (from intent_parser.py) into a concrete execution plan:
which tool function to call, and with what arguments.
Also catches missing required info so agent.py can ask a clarifying question
instead of calling a tool with bad args.
"""

REQUIRED_FIELDS = {
    "greeting": [],
    "help": [],
    "explain": ["customer_id"],
    "lookup": ["customer_id"],
    "retention": [],
    "eda": [],
    "segment": [],
    "feature_engineering": [],
}

CLARIFICATION_PROMPTS = {
    "customer_id": "Which customer are you asking about? Please give me a customer ID (e.g., 'explain customer 104').",
}


def build_plan(parsed_intent: dict) -> dict:
    action = parsed_intent.get("action")
    customer_id = parsed_intent.get("customer_id")
    cluster = parsed_intent.get("cluster")

    if action is None or parsed_intent.get("needs_clarification"):
        return {
            "tool": None,
            "args": {},
            "ready": False,
            "clarification": (
                "I'm not sure what you're asking. Try asking:\n"
                "• 'Why is customer 104 in this cluster?'\n"
                "• 'Show segments overview and average balance'\n"
                "• 'Show at-risk customers needing retention in cluster 1'\n"
                "• 'How was the data prepared for clustering?'"
            ),
        }

    missing = [
        field for field in REQUIRED_FIELDS.get(action, [])
        if parsed_intent.get(field) is None
    ]
    if missing:
        return {
            "tool": action,
            "args": {},
            "ready": False,
            "clarification": CLARIFICATION_PROMPTS.get(
                missing[0], f"I need more info: {missing[0]}"
            ),
        }

    args_by_action = {
        "greeting": {},
        "help": {},
        "explain": {"customer_id": customer_id},
        "lookup": {"customer_id": customer_id},
        "retention": {"cluster": cluster},
        "eda": {"cluster": cluster},
        "segment": {},
        "feature_engineering": {},
    }

    return {
        "tool": action,
        "args": args_by_action.get(action, {}),
        "ready": True,
        "clarification": None,
    }