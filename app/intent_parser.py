import re

ACTION_KEYWORDS = {
    "greeting": ["hello", "hi", "hey", "greetings", "good morning", "good afternoon", "good evening", "howdy", "sup"],
    "help": ["help", "what can you do", "who are you", "what are your capabilities", "how do i use", "options", "commands"],
    "explain": ["why", "explain", "basis", "reason", "criteria", "how were", "on what basis", "upgrade", "next best action"],
    "retention": ["at risk", "at-risk", "retention", "churn", "disengag", "convert", "conversion", "dormant", "re-engage"],
    "eda": ["average", "distribution", "missing values", "missing data", "correlation", "how many", "count", "data overview", "profile the data", "explore the data"],
    "segment": [
        "segments overview", "segment overview", "show segments", "describe segments", "describe cluster",
        "customer segments", "customer segmentation", "business segments",
        "segment", "segments", "cluster", "clusters", "persona", "personas",
        "customer groups", "group customers", "priority customers", "regular customers", "dormant customers", "young professionals"
    ],
    "lookup": ["is customer", "customer id", "customer #", "lookup customer", "find customer"],
    "feature_engineering": [
        "how was the data prepared", "how was the data processed", "what features were used",
        "feature engineering", "feature selection", "selected features",
        "data preprocessing", "data preparation", "feature transformation",
        "preprocessing", "pre processing", "transformations", "scaling",
        "standardization", "normalization", "engineered features"
    ],
}


def _load_persona_lookup():
    from app.services.data_manager import data_manager
    if data_manager.personas is not None and not data_manager.personas.empty:
        return {str(row["persona"]).lower(): int(row["cluster"]) for _, row in data_manager.personas.iterrows()}
    return {}


def _extract_customer_id(query: str):
    match = re.search(r"customer\s*(?:id)?\s*#?\s*(\d+)", query, re.IGNORECASE)
    if match:
        return int(match.group(1))
    return None


def _extract_cluster(query: str):
    match = re.search(r"cluster\s*(\d+)", query, re.IGNORECASE)
    if match:
        return int(match.group(1))

    persona_lookup = _load_persona_lookup()
    query_lower = query.lower()
    for persona_name, cluster_num in persona_lookup.items():
        if persona_name in query_lower:
            return cluster_num

    return None


def _detect_action(query: str):
    query_lower = query.lower()

    segment_creation_phrases = ["segment customers into", "cluster customers into", "group customers into"]
    for phrase in segment_creation_phrases:
        if phrase in query_lower:
            return "segment"

    # Match domain actions using longest phrase match first
    matches = []
    domain_actions = ["feature_engineering", "retention", "explain", "segment", "lookup", "eda"]
    for action in domain_actions:
        for keyword in ACTION_KEYWORDS[action]:
            if " " in keyword:
                if keyword in query_lower:
                    matches.append((len(keyword), action))
            else:
                if re.search(rf"\b{re.escape(keyword)}\b", query_lower):
                    matches.append((len(keyword), action))

    if matches:
        matches.sort(key=lambda x: x[0], reverse=True)
        return matches[0][1]

    # Check greeting and help
    for action in ["greeting", "help"]:
        for keyword in ACTION_KEYWORDS[action]:
            if re.search(rf"\b{re.escape(keyword)}\b", query_lower):
                return action

    return None


def parse_intent(query: str):
    customer_id = _extract_customer_id(query)
    cluster = _extract_cluster(query)
    action = _detect_action(query)

    if action is None and customer_id is not None:
        action = "lookup"

    needs_clarification = action is None

    return {
        "raw_query": query,
        "action": action,
        "customer_id": customer_id,
        "cluster": cluster,
        "needs_clarification": needs_clarification
    }