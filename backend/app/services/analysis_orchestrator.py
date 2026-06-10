from concurrent.futures import ThreadPoolExecutor

from app.services.solicitation_classifier import classify_solicitation
from app.services.proposal_strategy import generate_strategy
from app.services.compliance_matrix import generate_compliance_matrix


def run_analysis(text):

    with ThreadPoolExecutor(max_workers=3) as executor:

        classification_future = executor.submit(
            classify_solicitation,
            text
        )

        strategy_future = executor.submit(
            generate_strategy,
            text
        )

        compliance_future = executor.submit(
            generate_compliance_matrix,
            text
        )

        return {
            "classification":
                classification_future.result(),

            "strategy":
                strategy_future.result(),

            "compliance":
                compliance_future.result()
        }