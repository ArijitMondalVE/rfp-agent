from app.agents.deadline_agent import extract_deadlines
from app.agents.forms_agent import extract_forms
from app.agents.insurance_agent import extract_insurance
from app.agents.staffing_agent import extract_staffing
from app.agents.evaluation_agent import extract_evaluation
from app.agents.contract_agent import extract_contract_terms
from app.agents.disqualifier_agent import extract_disqualifiers
from app.agents.compliance_requirement_agent import (
    extract_compliance_requirements
)
from app.agents.qualification_agent import (
    extract_qualifications
)



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
    chunks,
    structured_data: dict,
    classification: dict,
    strategy: dict,
):


    full_text = "\n\n".join(
    chunk.page_content
    for chunk in chunks
    )   


    deadline_text = get_relevant_text(
    chunks,
    [
        "deadline",
        "due date",
        "submission",
        "schedule",
        "timeline",
        "pre-bid",
        "questions due"
    ]
    )

    forms_text = get_relevant_text(
    chunks,
    [
        "form",
        "affidavit",
        "attachment",
        "exhibit",
        "certification",
        "questionnaire"
    ]
    )

    insurance_text = get_relevant_text(
    chunks,
    [
        "insurance",
        "coverage",
        "liability",
        "workers compensation"
    ]
        )

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
            extract_deadlines(deadline_text),

        "forms":
            extract_forms(forms_text),

        "insurance":
            extract_insurance(insurance_text),

        "staffing":
            extract_staffing(full_text),

        "evaluation":
            extract_evaluation(full_text),

        "contract":
            extract_contract_terms(full_text),

        "disqualifiers":
            extract_disqualifiers(full_text),

        # Existing Strategy Data
        "bid_recommendation":
            strategy.get("bid_recommendation"),

        "win_themes":
            strategy.get("win_themes", []),

        "risks":
            strategy.get("risks", []),

        "critical_items":
            strategy.get("critical_items", []),

        "compliance_requirements":
            extract_compliance_requirements(full_text),

        "qualifications":
            extract_qualifications(full_text),  
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

        "compliance_count":
            len(kb.get("compliance_requirements", [])),

        "qualification_count":
            len(kb.get("qualifications", [])),   
    }

    return kb


def get_relevant_text(chunks, keywords):

    selected = []

    for chunk in chunks:

        content = chunk.page_content.lower()

        if any(
            keyword.lower() in content
            for keyword in keywords
        ):
            selected.append(chunk.page_content)

    return "\n\n".join(selected)