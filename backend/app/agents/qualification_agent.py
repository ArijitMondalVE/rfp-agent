import re


QUALIFICATION_PATTERNS = [

    r"minimum.*experience",
    r"years of experience",
    r"licensed",
    r"license",
    r"certification",
    r"certified",
    r"past performance",
    r"references",
    r"business tax receipt",
    r"bonded",
    r"insurance",
    r"background check",
]



def extract_qualifications(text: str):

    findings = []

    lines = text.split("\n")

    for line in lines:

        line = line.strip()

        if len(line) < 15:
            continue

        lower = line.lower()

        if any(
            re.search(pattern, lower)
            for pattern in QUALIFICATION_PATTERNS
        ):
            findings.append(line)

    return list(set(findings))