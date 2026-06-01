def remove_duplicates(items):

    unique = []

    seen = set()

    for item in items:

        item_str = str(item).lower().strip()

        if item_str not in seen:

            seen.add(item_str)

            unique.append(item)

    return unique


def merge_results(results):

    merged = {
        "scope": [],
        "deliverables": [],
        "objectives": [],
        "deadlines": [],
        "staffing": [],
        "pricing": [],
        "compliance": []
    }

    # Merge all chunk outputs
    for result in results:

        if "scope" in result:
            merged["scope"].extend(result["scope"])

        if "deliverables" in result:
            merged["deliverables"].extend(result["deliverables"])

        if "objectives" in result:
            merged["objectives"].extend(result["objectives"])

        if "deadlines" in result:
            merged["deadlines"].extend(result["deadlines"])

        if "staffing" in result:
            merged["staffing"].extend(result["staffing"])

        if "pricing" in result:
            merged["pricing"].extend(result["pricing"])

        if "compliance" in result:
            merged["compliance"].extend(result["compliance"])

    # Remove duplicate entries
    merged["scope"] = remove_duplicates(
        merged["scope"]
    )

    merged["deliverables"] = remove_duplicates(
        merged["deliverables"]
    )

    merged["objectives"] = remove_duplicates(
        merged["objectives"]
    )

    merged["deadlines"] = remove_duplicates(
        merged["deadlines"]
    )

    merged["staffing"] = remove_duplicates(
        merged["staffing"]
    )

    merged["pricing"] = remove_duplicates(
        merged["pricing"]
    )

    merged["compliance"] = remove_duplicates(
        merged["compliance"]
    )

    return merged