import os
import re

from google import genai
from google.genai import types


DEFAULT_MODEL = "gemini-3.5-flash"
MAX_ANSWER_TOKENS = 64


def _parse_option_index(answer: str, valid_indices: set[int]) -> int:
	answer = answer.strip()
	if re.fullmatch(r"\d+", answer):
		option_index = int(answer)
	else:
		final_line = answer.splitlines()[-1] if answer else ""
		answer_patterns = (
			r"(?i)(?:the\s+)?(?:final\s+)?(?:correct\s+)?answer"
			r"(?:\s+(?:index|number))?\s*(?:is|:|#)\s*(\d+)[.!]?",
			r"(?i)(?:the\s+)?correct\s+(?:option|choice)\s*"
			r"(?:is|:|#)\s*(\d+)[.!]?",
			r"(?i)(?:the\s+)?(?:option|choice)\s*(\d+)\s+"
			r"is\s+(?:the\s+)?correct[.!]?",
		)
		match = next(
			(
				match
				for pattern in answer_patterns
				if (match := re.fullmatch(pattern, final_line.strip()))
			),
			None,
		)
		if match is None:
			preview = answer[:120].replace("\n", "\\n")
			raise ValueError(
				"Gemini did not return a bare index or explicit final answer; "
				f"response starts with {preview!r}."
			)
		option_index = int(match.group(1))

	if option_index not in valid_indices:
		raise ValueError(
			f"Gemini selected {option_index}, which is not a valid option."
		)
	return option_index


class GeminiQuizSolver:
	def __init__(self, api_key: str | None = None, model: str | None = None):
		api_key = (
			api_key
			or os.getenv("GEMINI_API_KEY")
			or os.getenv("GOOGLE_API_KEY")
		)
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

		prompt_lines = [question]
		prompt_lines.extend(
			f"{choice['index']}: {choice['text']}" for choice in choices
		)
		prompt_lines.append("Reply with only the correct option index.")

		response = self.client.models.generate_content(
			model=self.model,
			contents="\n".join(prompt_lines),
			config=types.GenerateContentConfig(
				system_instruction=(
					"Choose the correct option using only the supplied question "
					"and options. Return only its zero-based index."
				),
				temperature=0,
				max_output_tokens=MAX_ANSWER_TOKENS,
				thinking_config=types.ThinkingConfig(
					thinking_level=types.ThinkingLevel.LOW
				),
			),
		)

		answer = response.text or ""
		if not answer.strip():
			candidates = getattr(response, "candidates", None) or []
			reasons = [
				str(getattr(candidate, "finish_reason", "unknown"))
				for candidate in candidates
			]
			reason = ", ".join(reasons) or "not provided"
			raise ValueError(
				"Gemini returned no answer text "
				f"(finish reason: {reason})."
			)

		try:
			return _parse_option_index(
				answer, {choice["index"] for choice in choices}
			)
		except ValueError as exc:
			candidates = getattr(response, "candidates", None) or []
			reasons = [
				str(getattr(candidate, "finish_reason", "unknown"))
				for candidate in candidates
			]
			reason = ", ".join(reasons) or "not provided"
			raise ValueError(f"{exc} (finish reason: {reason}).") from exc
