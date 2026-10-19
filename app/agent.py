"""
Top-level agent entrypoint. Wires together:
  intent_parser.parse_intent() -> planner.build_plan() -> tools.*
routes.py should only ever need to call run_agent(query).
"""

from typing import Dict, Any
from . import intent_parser
from . import planner
from . import tools


def greeting_tool(**kwargs) -> Dict[str, Any]:
    return {
        "message": (
            "Hello! I am your retail banking intelligence assistant. "
            "I can analyze customer segments, explain individual customer cluster assignments, "
            "identify at-risk customers needing retention, provide exploratory data metrics, "
            "and explain our ML feature engineering pipeline."
        ),
        "suggestions": [
            "Why is customer 104 in this cluster?",
            "Show segments overview and average balance",
            "Show at-risk customers needing retention in cluster 1",
            "How was the data prepared for clustering?",
        ],
    }


def help_tool(**kwargs) -> Dict[str, Any]:
    return greeting_tool(**kwargs)


TOOL_DISPATCH = {
    "greeting": greeting_tool,
    "help": help_tool,
    "explain": tools.explainability_tool,
    "lookup": tools.get_customer_segment,
    "retention": tools.retention_tool,
    "eda": tools.eda_tool,
    "segment": tools.segmentation_tool,
    "feature_engineering": tools.feature_engineering_tool,
}


def run_agent(query: str) -> dict:
    parsed = intent_parser.parse_intent(query)
    plan = planner.build_plan(parsed)

    if not plan["ready"]:
        return {
            "status": "needs_clarification",
            "message": plan["clarification"],
            "parsed_intent": parsed,
            "plan": plan,
        }

    tool_fn = TOOL_DISPATCH.get(plan["tool"])
    if tool_fn is None:
        return {
            "status": "error",
            "message": f"No tool wired up for action '{plan['tool']}'.",
            "parsed_intent": parsed,
            "plan": plan,
        }

    try:
        result = tool_fn(**plan["args"])
    except Exception as e:
        return {
            "status": "error",
            "message": f"Tool '{plan['tool']}' failed: {e}",
            "parsed_intent": parsed,
            "plan": plan,
        }

    if isinstance(result, dict) and "error" in result:
        return {
            "status": "error",
            "message": result["error"],
            "parsed_intent": parsed,
            "plan": plan,
        }

    return {
        "status": "ok",
        "action": plan["tool"],
        "result": result,
        "parsed_intent": parsed,
        "plan": plan,
    }


def _synthesize_natural_language(action: str, result: Any) -> str:
    """
    Transforms structured tool dictionaries into human-readable,
    professional natural language formatted in markdown.
    """
    if not isinstance(result, dict):
        return str(result)

    if action in ("greeting", "help"):
        suggestions = "\n".join(f"- {s}" for s in result.get("suggestions", []))
        return (
            f"{result.get('message', 'Hello!')}\n\n"
            f"**You can ask me questions such as:**\n{suggestions}"
        )

    if action == "explain":
        c_id = result.get("customer_id")
        cluster = result.get("cluster")
        persona = result.get("persona", "Unknown")
        explanations = result.get("explanation", [])

        lines = [
            f"**Customer #{c_id}** is assigned to **Segment {cluster} ({persona})**.",
            "",
            "**Key reasons for this segment assignment:**",
        ]
        if explanations:
            for exp in explanations:
                lines.append(f"- {exp}")
        else:
            lines.append("- Customer attributes align closely with the segment centroid.")
        return "\n".join(lines)

    if action == "lookup":
        c_id = result.get("customer_id")
        cluster = result.get("cluster")
        persona = result.get("persona", "Unknown")
        profile = result.get("profile", {})
        recs = result.get("recommendations", [])

        balance = profile.get("account_balance", 0)
        income = profile.get("annual_income", 0)
        credit = profile.get("credit_score", "N/A")
        age = profile.get("age", "N/A")
        job = profile.get("job", "N/A")
        tx = profile.get("monthly_transactions", "N/A")
        digital = profile.get("digital_banking_score", "N/A")

        lines = [
            f"**Customer Profile: #{c_id}**",
            f"- **Segment**: Cluster {cluster} ({persona})",
            f"- **Demographics**: Age {age}, Job: {job}",
            f"- **Financials**: Balance ${balance:,.2f} | Annual Income ${income:,.2f} | Credit Score {credit}",
            f"- **Activity**: {tx} monthly transactions | Digital Banking Score {digital}/100",
        ]
        if recs:
            lines.append("")
            lines.append("**Recommended Banking Products:**")
            for r in recs:
                lines.append(f"- {r}")
        return "\n".join(lines)

    if action == "segment":
        segments = result.get("segments", [])
        num_segments = result.get("number_of_segments", len(segments))
        lines = [
            f"Found **{num_segments} customer segments** identified by K-Means clustering:\n"
        ]
        for s in segments:
            c_num = s.get("cluster")
            p_name = s.get("persona")
            c_count = s.get("customer_count", 0)
            pct = s.get("percentage", 0.0)
            bal = s.get("average_balance", 0.0)
            inc = s.get("average_income", 0.0)
            chars = s.get("characteristics", "")
            recs = s.get("recommended_products", [])
            recs_str = ", ".join(recs) if recs else "Standard retail services"

            lines.append(f"- **Segment {c_num}: {p_name}** ({c_count:,} customers, {pct:.1f}% of total)")
            lines.append(f"  - **Financials**: Avg Balance ${bal:,.0f} | Avg Income ${inc:,.0f}")
            if chars:
                lines.append(f"  - **Profile**: {chars}")
            lines.append(f"  - **Recommended Products**: {recs_str}\n")
        return "\n".join(lines).strip()

    if action == "retention":
        scope = result.get("scope", "all customers")
        total = result.get("customers_analyzed", 0)
        high_risk = result.get("high_risk_customers", 0)
        strategies = result.get("customer_strategies", [])

        lines = [
            f"**Customer Strategy & Retention Analysis ({scope})**",
            f"Analyzed {total} customer records. Detected **{high_risk} customers at elevated retention risk**.\n",
        ]
        sample = [s for s in strategies if s.get("risk_level") == "High"][:4]
        if not sample:
            sample = strategies[:4]

        if sample:
            lines.append("**Sample Account Review & Recommended Interventions:**")
            for s in sample:
                cid = s.get("customer_id")
                risk = s.get("risk_level", "Medium")
                reasons = "; ".join(s.get("reasons", []))
                actions = "; ".join(s.get("next_best_actions", []))
                lines.append(f"- **Customer #{cid}** [{risk} Risk]: {reasons}")
                lines.append(f"  -> Action: {actions}")

        return "\n".join(lines)

    if action == "eda":
        scope = result.get("scope", "all customers")
        rows = result.get("row_count", 0)
        stats = result.get("summary_stats", {})

        lines = [
            f"**Exploratory Data Analysis ({scope})**",
            f"- **Total Records**: {rows:,} customers analyzed",
        ]
        if "account_balance" in stats and "mean" in stats["account_balance"]:
            bal_mean = stats["account_balance"]["mean"]
            lines.append(f"- **Average Account Balance**: ${bal_mean:,.2f}")
        if "annual_income" in stats and "mean" in stats["annual_income"]:
            inc_mean = stats["annual_income"]["mean"]
            lines.append(f"- **Average Annual Income**: ${inc_mean:,.2f}")
        if "credit_score" in stats and "mean" in stats["credit_score"]:
            credit_mean = stats["credit_score"]["mean"]
            lines.append(f"- **Average Credit Score**: {credit_mean:.0f}")
        if "digital_banking_score" in stats and "mean" in stats["digital_banking_score"]:
            dig_mean = stats["digital_banking_score"]["mean"]
            lines.append(f"- **Average Digital Score**: {dig_mean:.1f}/100")
        lines.append("- **Data Quality**: Zero null values detected in active clustering set.")
        return "\n".join(lines)

    if action == "feature_engineering":
        features = result.get("input_features", [])
        trans = result.get("transformations", [])
        output = result.get("output", "")
        lines = [
            "**Feature Engineering & Model Pipeline Architecture**\n",
            f"- **Input Features**: {', '.join(features)}",
            "- **Data Transformations**:",
        ]
        for t in trans:
            lines.append(f"  - {t}")
        if output:
            lines.append(f"\n- **Model Pipeline**: {output}")
        return "\n".join(lines)

    return f"Completed analysis using the {action} tool."


def to_chat_response(agent_result: dict) -> dict:
    """
    Formats a run_agent() result into the shape ChatResponse expects
    (response / execution_plan / results). Shared by routes.py's pure
    rule-based path and groq_service.py's fallback path.
    """
    execution_plan = [
        f"Parsed query -> action: {agent_result['parsed_intent'].get('action') or 'unclear'}"
    ]

    if agent_result["parsed_intent"].get("customer_id") is not None:
        execution_plan.append(
            f"Extracted customer_id={agent_result['parsed_intent']['customer_id']}"
        )
    if agent_result["parsed_intent"].get("cluster") is not None:
        execution_plan.append(
            f"Extracted cluster={agent_result['parsed_intent']['cluster']}"
        )

    if agent_result["status"] == "ok":
        execution_plan.append(f"Called tool: {agent_result['action']}")
        natural_response = _synthesize_natural_language(
            agent_result["action"], agent_result["result"]
        )
        return {
            "response": natural_response,
            "execution_plan": execution_plan,
            "results": agent_result["result"],
        }

    elif agent_result["status"] == "needs_clarification":
        execution_plan.append("Requested clarification from user")
        return {
            "response": agent_result["message"],
            "execution_plan": execution_plan,
            "results": {},
        }

    else:  # error
        execution_plan.append(f"Tool error: {agent_result['message']}")
        return {
            "response": f"Something went wrong: {agent_result['message']}",
            "execution_plan": execution_plan,
            "results": {},
        }