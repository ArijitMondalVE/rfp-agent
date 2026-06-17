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

        # Hard timeouts to prevent background jobs from hanging forever
        # (LLM calls are network-bound; we cap wall time.)
        TIMEOUT_S = 180

        def _wait(fut, name: str):
            try:
                return fut.result(timeout=TIMEOUT_S)
            except Exception as e:
                # Always return a safe fallback so the upload job can finish gracefully.
                print(f"[Analysis] {name} failed/timed out: {e}")
                return {"status": "failed", "message": str(e)}

        return {
            "classification": _wait(classification_future, "classification"),
            "strategy": _wait(strategy_future, "strategy"),
            "compliance": _wait(compliance_future, "compliance"),
        }

