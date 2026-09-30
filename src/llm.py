import json
import os
import re

from google import genai
from google.genai import types


DEFAULT_MODEL = "gemini-3.5-flash"


def _parse_option_index(answer: str, valid_indices: set[int]) -> int:
	answer = answer.strip()
	if re.fullmatch(r"\d+", answer) is None:
		raise ValueError(
			f"Gemini returned {answer!r}; expected only an option index."
		)

	option_index = int(answer)
	if option_index not in valid_indices:
		raise ValueError(
			f"Gemini selected {option_index}, which is not a valid option."
		)
	return option_index


class GeminiQuizSolver:
	def __init__(self, api_key: str | None = None, model: str | None = None):
		api_key = api_key or os.getenv("GEMINI_API_KEY") or os.getenv("GOOGLE_API_KEY")
		if not api_key:
			raise RuntimeError(
				"Set GEMINI_API_KEY or GOOGLE_API_KEY before running the agent."
			)

		self.client = genai.Client(api_key=api_key)
		self.model = model or os.getenv("GEMINI_MODEL", DEFAULT_MODEL)

	def choose_option(self, question: str, options: list[dict]) -> int:
		if not options:
			raise ValueError("Cannot solve a question without answer options.")

		choices = [
			{
				"index": option["index"],
				"text": option.get("text") or option.get("identifier") or "",
			}
			for option in options
		]
		if any(not choice["text"] for choice in choices):
			raise ValueError("Every answer option must have readable text.")

		response = self.client.models.generate_content(
			model=self.model,
			contents=json.dumps(
				{"question": question, "options": choices},
				ensure_ascii=False,
			),
			config=types.GenerateContentConfig(
				system_instruction=(
					"Choose the correct answer using only the supplied question "
					"and options. Return only the zero-based option index as an "
					"integer. Do not include explanation or punctuation."
				),
				temperature=0,
			),
		)

		return _parse_option_index(
			response.text or "", {choice["index"] for choice in choices}
		)
