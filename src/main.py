import argparse
import os
import sys
from pathlib import Path

from dotenv import load_dotenv

if __package__ in (None, ""):
    sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from src.agent import complete_quiz
from src.browser import CDP_URL, GoogleFormBrowser
from src.llm import GeminiQuizSolver


def main() -> None:
    load_dotenv()
    parser = argparse.ArgumentParser(
        description="Answer a Google Form using Gemini and Playwright."
    )
    parser.add_argument(
        "--cdp-url",
        default=CDP_URL,
        help="Chrome remote debugging endpoint (default: %(default)s)",
    )
    parser.add_argument(
        "--request-delay",
        type=float,
        default=float(os.getenv("QUIZ_REQUEST_DELAY_SECONDS", "2")),
        help="Seconds to wait between Gemini questions (default: %(default)s)",
    )
    args = parser.parse_args()

    solver = GeminiQuizSolver()
    browser = GoogleFormBrowser(cdp_url=args.cdp_url)
    try:
        browser.connect()
        complete_quiz(
            browser,
            solver,
            request_delay_seconds=args.request_delay,
        )
        print("Quiz submitted.")
    finally:
        browser.close()


if __name__ == "__main__":
    main()