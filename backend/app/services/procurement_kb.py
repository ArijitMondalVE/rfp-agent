from app.agents.deadline_agent import extract_deadlines
from app.agents.forms_agent import extract_forms
from app.agents.insurance_agent import extract_insurance
from app.agents.staffing_agent import extract_staffing
from app.agents.evaluation_agent import extract_evaluation
from app.agents.contract_agent import extract_contract_terms
from app.agents.disqualifier_agent import extract_disqualifiers


def clean_empty(value):

    if value is None:
        return None

    if isinstance(value, str):
        value = value.strip()

        if (
            value == ""
            or value.lower() == "not specified"
            or value.lower() == "n/a"
        ):
            return None

    return value


def build_procurement_kb(
    text: str,
    structured_data: dict,
    classification: dict,
    strategy: dict,
):

    kb = {

        # Core Opportunity Information
        "agency":
            structured_data.get("agency"),

        "solicitation_number":
            structured_data.get("solicitation_number"),

        "solicitation_type":
            classification.get("solicitation_type"),

        "contract_term":
            structured_data.get("contract_term"),

        # Specialized Agent Outputs
        "deadlines":
            extract_deadlines(text),

        "forms":
            extract_forms(text),

        "insurance":
            extract_insurance(text),

        "staffing":
            extract_staffing(text),

        "evaluation":
            extract_evaluation(text),

        "contract":
            extract_contract_terms(text),

        "disqualifiers":
            extract_disqualifiers(text),

        # Existing Strategy Data
        "bid_recommendation":
            strategy.get("bid_recommendation"),

        "win_themes":
            strategy.get("win_themes", []),

        "risks":
            strategy.get("risks", []),

        "critical_items":
            strategy.get("critical_items", [])
    }

    # Remove empty values
    kb = {
        k: clean_empty(v)
        for k, v in kb.items()
    }

    # Useful dashboard statistics
    kb["stats"] = {

        "deadline_count":
            len(kb.get("deadlines", [])),

        "form_count":
            len(kb.get("forms", [])),

        "insurance_count":
            len(kb.get("insurance", [])),

        "staffing_count":
            len(kb.get("staffing", [])),

        "evaluation_count":
            len(kb.get("evaluation", [])),

        "disqualifier_count":
            len(kb.get("disqualifiers", [])),

        "risk_count":
            len(kb.get("risks", [])),

        "critical_item_count":
            len(kb.get("critical_items", [])),
    }

    return kb