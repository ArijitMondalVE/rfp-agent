REQUIRED_COMPLIANCE_ITEMS = [
    "ISO 27001",
    "GDPR",
    "Cyber Insurance",
    "NDA",
    "SOC 2"
]


def check_compliance(text: str):

    findings = []

    for item in REQUIRED_COMPLIANCE_ITEMS:

        if item.lower() in text.lower():

            findings.append({
                "clause": item,
                "status": "FOUND",
                "risk": "LOW"
            })

        else:

            findings.append({
                "clause": item,
                "status": "MISSING",
                "risk": "HIGH"
            })

    return findings