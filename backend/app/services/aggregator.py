from app.schemas.rfp_schema import RFPExtraction


def aggregate_results(merged_results):

    final_output = RFPExtraction(

        scope_of_work=merged_results.get("scope", []),

        deadlines=merged_results.get("deadlines", []),

        staffing_requirements=merged_results.get("staffing", []),

        compliance_items=merged_results.get("compliance", [])

    )

    result = final_output.model_dump()

    # Add additional fields not in schema
    result["deliverables"] = merged_results.get("deliverables", [])

    result["objectives"] = merged_results.get("objectives", [])

    return result