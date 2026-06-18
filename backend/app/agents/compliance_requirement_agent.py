import re


MANDATORY_PATTERNS = [
    r"\bmust\b",
    r"\bshall\b",
    r"\brequired\b",
    r"\bmandatory\b",
    r"\bnon-responsive\b",
    r"\bdisqualified\b",
    r"\bfailure to\b",
]


def extract_compliance_requirements(text: str):

    requirements = []

    lines = text.split("\n")

    for line in lines:

        line = line.strip()

        if len(line) < 15:
            continue

        lower = line.lower()

        if any(
            re.search(pattern, lower)
            for pattern in MANDATORY_PATTERNS
        ):
            requirements.append(line)

    return list(set(requirements))