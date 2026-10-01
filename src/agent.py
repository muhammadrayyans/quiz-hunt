import time
from typing import Protocol


DEFAULT_REQUEST_INTERVAL_SECONDS = 2.5


class FormBrowser(Protocol):
	def get_questions(self) -> list[dict]: ...

	def select_option(self, question_index: int, option_index: int) -> None: ...

	def click_next(self) -> bool: ...

	def submit(self) -> None: ...


class AnswerSolver(Protocol):
	def choose_option(self, question: str, options: list[dict]) -> int: ...


def _log(message: str) -> None:
	print(message, flush=True)


def complete_quiz(
	browser: FormBrowser,
	solver: AnswerSolver,
	request_interval_seconds: float = DEFAULT_REQUEST_INTERVAL_SECONDS,
) -> None:
	if request_interval_seconds < 0:
		raise ValueError("Request interval cannot be negative.")

	last_request_started_at: float | None = None
	page_number = 0
	while True:
		page_number += 1
		try:
			questions = browser.get_questions()
		except Exception as exc:
			_log(f"[Page {page_number}] Failed to read questions: {exc}")
			raise

		if not questions:
			_log(f"[Page {page_number}] No multiple-choice questions found.")
			raise RuntimeError("No multiple-choice questions found on this page.")

		_log(f"[Page {page_number}] Read {len(questions)} question(s).")
		for question_index, question in enumerate(questions):
			question_label = f"[Page {page_number}, Q{question_index + 1}]"
			_log(f"{question_label} {question['question']}")
			for option in question["options"]:
				option_text = option.get("text") or option.get("identifier") or ""
				_log(f"{question_label} Option {option['index']}: {option_text}")

			if last_request_started_at is not None:
				elapsed = time.monotonic() - last_request_started_at
				wait_seconds = request_interval_seconds - elapsed
				if wait_seconds > 0:
					_log(
						f"{question_label} Waiting {wait_seconds:.1f}s to maintain "
						f"a {request_interval_seconds:g}s Gemini request interval."
					)
					time.sleep(wait_seconds)

			last_request_started_at = time.monotonic()
			_log(f"{question_label} Gemini is thinking...")
			try:
				option_index = solver.choose_option(
					question["question"], question["options"]
				)
			except Exception as exc:
				_log(f"{question_label} Gemini request/response failed: {exc}")
				raise

			valid_indices = {
				option["index"] for option in question["options"]
			}
			if option_index not in valid_indices:
				_log(
					f"{question_label} Gemini returned invalid option index "
					f"{option_index}; nothing was selected."
				)
				raise ValueError(
					f"Solver selected {option_index}, which is not a valid option "
					f"for question {question_index}."
				)

			selected_option = next(
				option for option in question["options"]
				if option["index"] == option_index
			)
			option_text = (
				selected_option.get("text")
				or selected_option.get("identifier")
				or ""
			)
			_log(f"{question_label} Gemini chose option {option_index}: {option_text}")
			try:
				browser.select_option(question_index, option_index)
			except Exception as exc:
				_log(f"{question_label} Failed to select the answer: {exc}")
				raise
			_log(f"{question_label} Answer selected.")

		try:
			moved_to_next_page = browser.click_next()
		except Exception as exc:
			_log(f"[Page {page_number}] Failed to click Next: {exc}")
			raise

		if moved_to_next_page:
			_log(f"[Page {page_number}] Moving to the next page.")
			continue

		_log("No next page found. Submitting the form...")
		try:
			browser.submit()
		except Exception as exc:
			_log(f"Form submission failed: {exc}")
			raise
		_log("Form submitted successfully.")
		return
