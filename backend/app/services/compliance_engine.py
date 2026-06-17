def determine_severity(category):

    if category == "Disqualifier":
        return "Critical"

    if category in [
        "Insurance",
        "License",
        "Deadline"
    ]:
        return "High"

    return "Medium"


def generate_compliance_matrix(procurement_kb):

    matrix = []

    # Forms
    for item in procurement_kb.get("forms", []):

        matrix.append({
            "category": "Forms",
            "requirement": item.get("form"),
            "mandatory": item.get("required", True),
            "page": item.get("page"),
            "severity": determine_severity("Forms"),
            "risk": "Non-responsive submission"
        })

    # Deadlines
    for item in procurement_kb.get("deadlines", []):

        matrix.append({
            "category": "Deadline",
            "requirement": item.get("event"),
            "mandatory": True,
            "page": item.get("page"),
            "severity": determine_severity("Deadline"),
            "risk": "Late submission"
        })

    # Insurance
    for item in procurement_kb.get("insurance", []):

        matrix.append({
            "category": "Insurance",
            "requirement": item.get("coverage"),
            "mandatory": True,
            "page": item.get("page"),
            "severity": determine_severity("Insurance"),
            "risk": "Contract award risk"
        })

    # Staffing
    for item in procurement_kb.get("staffing", []):

        matrix.append({
            "category": "Staffing",
            "requirement": item.get("requirement"),
            "mandatory": True,
            "page": item.get("page"),
            "severity": determine_severity("Staffing"),
            "risk": "Proposal weakness"
        })

    # Disqualifiers
    for item in procurement_kb.get("disqualifiers", []):

        matrix.append({
            "category": "Disqualifier",
            "requirement": item.get("requirement"),
            "mandatory": True,
            "page": item.get("page"),
            "severity": determine_severity("Disqualifier"),
            "risk": item.get("reason")
        })

    return matrix