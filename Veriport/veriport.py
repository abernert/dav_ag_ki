#!/usr/bin/env python3
# SPDX-License-Identifier: GPL-3.0-or-later
# Copyright (C) 2025 Alexander Bernert
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <https://www.gnu.org/licenses/>.

"""
VeriPort: Single-file CrewAI-based code converter with reviewer loop.

Run as a script:
    python veriport.py <path/to/source> [options]

This module provides a CLI and all functionality to:
  - Convert a source file into another language (default: Python)
  - Review the conversion for syntactic correctness and functional equivalence
  - Iterate until the reviewer approves, then write the output to disk

See the project root LICENSE file for Apache 2.0 terms.
"""

from __future__ import annotations

import argparse
import json
import os
import re
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, Optional, Literal, Tuple

from pydantic import BaseModel

# Load environment variables from .env if present
try:  # pragma: no cover
    from dotenv import load_dotenv  # type: ignore

    load_dotenv()
except Exception:
    pass

__version__ = "0.1.0"

__all__ = [
    "__version__",
    "ConverterPipeline",
    "resolve_output_path",
    "main",
    "ReviewVerdict",
]


# --- LLM and CrewAI helpers -------------------------------------------------

def _build_llm(model: str) -> Any:
    """Build an LLM compatible with CrewAI Agents.

    Tries CrewAI's native LLM wrapper, falling back to LangChain's ChatOpenAI.
    """
    # Try CrewAI LLM
    try:
        from crewai import LLM as CrewAILLM  # type: ignore

        return CrewAILLM(model=model)
    except Exception:
        # Maybe older import path
        try:
            from crewai.llm import LLM as CrewAILLM  # type: ignore

            return CrewAILLM(model=model)
        except Exception:
            pass

    # Fallback to LangChain OpenAI Chat
    try:
        from langchain_openai import ChatOpenAI  # type: ignore

        # Uses OPENAI_API_KEY from environment
        return ChatOpenAI(model=model)
    except Exception as e:  # pragma: no cover - guidance for missing deps
        raise RuntimeError(
            "Unable to construct an LLM. Please install one of: "
            "`crewai` (preferred) or `langchain-openai` and set OPENAI_API_KEY."
        ) from e


def _safe_json_extract(s: str) -> Optional[Dict[str, Any]]:
    """Extract the first JSON object from a string, forgiving code fences.

    Returns None if no valid JSON object can be parsed.
    """
    if not isinstance(s, str):
        return None

    # Remove code fences if present
    cleaned = re.sub(r"^```.*?\n|```$", "", s.strip(), flags=re.DOTALL | re.MULTILINE)

    # Try direct parse first
    try:
        return json.loads(cleaned)
    except Exception:
        pass

    # Fallback: find first {...}
    m = re.search(r"\{[\s\S]*\}", cleaned)
    if m:
        try:
            return json.loads(m.group(0))
        except Exception:
            return None
    return None


def _extract_verdict_feedback(payload: Dict[str, Any]) -> Tuple[str, str]:
    """Return verdict/feedback from various CrewAI payload shapes."""

    def _from_dict(d: Dict[str, Any]) -> Tuple[str, str]:
        verdict_val = str(d.get("verdict", "")).strip().lower()
        feedback_val = str(d.get("feedback", "")).strip()
        return verdict_val, feedback_val

    if not isinstance(payload, dict):
        return "", ""

    candidates: list[Dict[str, Any]] = [payload]
    json_dict = payload.get("json_dict")
    if isinstance(json_dict, dict):
        candidates.append(json_dict)
    raw_text = payload.get("raw")
    if isinstance(raw_text, str):
        raw_json = _safe_json_extract(raw_text)
        if isinstance(raw_json, dict):
            candidates.append(raw_json)

    for candidate in candidates:
        verdict_val, feedback_val = _from_dict(candidate)
        if verdict_val:
            return verdict_val, feedback_val
    return _from_dict(payload)


def _normalize_task_output(result: Any) -> str:
    """Flatten CrewAI outputs (dict/BaseModel) down to a meaningful string."""
    if result is None:
        return ""

    if isinstance(result, BaseModel):
        return _normalize_task_output(result.model_dump())

    if isinstance(result, dict):
        json_dict = result.get("json_dict")
        if isinstance(json_dict, dict):
            return json.dumps(json_dict)
        raw_text = result.get("raw")
        if isinstance(raw_text, str):
            parsed = _safe_json_extract(raw_text)
            if parsed is not None:
                return json.dumps(parsed)
            return raw_text.strip()
        if len(result) == 1:
            return _normalize_task_output(next(iter(result.values())))
        return json.dumps(result)

    if isinstance(result, list):
        return json.dumps(result)

    if isinstance(result, str):
        parsed = _safe_json_extract(result)
        if parsed is not None:
            return _normalize_task_output(parsed)
        return result.strip()

    return str(result).strip()


def _detect_ext_from_language(lang: str) -> str:
    mapping = {
        "python": "py",
        "javascript": "js",
        "typescript": "ts",
        "java": "java",
        "c": "c",
        "c++": "cpp",
        "cpp": "cpp",
        "c#": "cs",
        "go": "go",
        "rust": "rs",
        "ruby": "rb",
        "php": "php",
        "kotlin": "kt",
        "swift": "swift",
        "scala": "scala",
        "cobol": "cbl",
    }
    return mapping.get(lang.lower(), "py")


class ReviewVerdict(BaseModel):
    verdict: Literal["approve", "revise"]
    feedback: str = ""


# --- Agents -----------------------------------------------------------------

def _import_crewai():
    """Import CrewAI components lazily to avoid import-time failures.

    Returns the tuple (Agent, Crew, Process, Task) or raises a helpful error.
    """
    try:  # type: ignore
        from crewai import Agent, Crew, Process, Task  # type: ignore

        return Agent, Crew, Process, Task
    except Exception as e:  # pragma: no cover - import-time guidance
        raise ImportError(
            "crewai is required at runtime. Install with `pip install crewai`."
        ) from e


def _make_converter_agent(llm: Any, target_language: str, verbose: bool = False) -> Any:
    Agent, _, _, _ = _import_crewai()
    return Agent(
        role="Code Converter",
        goal=(
            f"Convert the provided source code into high-quality {target_language} code "
            "that is functionally equivalent, idiomatic, and complete."
        ),
        backstory=(
            "You are a seasoned polyglot software engineer with deep expertise in "
            "translating codebases across languages while preserving functionality, "
            "error handling, and edge cases. You produce clean, runnable code only."
        ),
        verbose=verbose,
        allow_delegation=False,
        llm=llm,
    )


def _make_reviewer_agent(llm: Any, target_language: str, verbose: bool = False) -> Any:
    Agent, _, _, _ = _import_crewai()
    return Agent(
        role="Conversion Reviewer",
        goal=(
            "Ensure the conversion is syntactically valid, complete, and functionally "
            f"equivalent to the original. Approve only if the {target_language} output "
            "is ready to run without missing logic."
        ),
        backstory=(
            "You are a meticulous software reviewer. You deeply compare algorithms, "
            "data structures, side-effects, I/O, error handling, and edge cases. You "
            "return a strict JSON verdict for automation."
        ),
        verbose=verbose,
        allow_delegation=False,
        llm=llm,
    )


# --- Pipeline ---------------------------------------------------------------

@dataclass
class ConversionResult:
    approved: bool
    attempt: int
    converted_code: Optional[str]
    review_feedback: Optional[str]
    verdict: Optional[str]


class ConverterPipeline:
    """Coordinates the converter and reviewer agents in an iterative loop."""

    def __init__(
        self,
        model: str = "gpt-5",
        target_language: str = "python",
        target_ext: Optional[str] = None,
        verbose: bool = False,
        max_iters: int = 3,
    ) -> None:
        api_key = os.getenv("OPENAI_API_KEY")
        if not api_key or api_key.strip().lower() == "your_openai_api_key_here":
            # Don't fail hard; some environments may use local keys or config providers.
            # Still warn for usability.
            print(
                "[veriport] Warning: OPENAI_API_KEY is missing or a placeholder. "
                "Set a valid key in your environment or .env file."
            )

        self.model = model
        self.target_language = target_language
        self.target_ext = target_ext or _detect_ext_from_language(target_language)
        self.verbose = verbose
        self.max_iters = max_iters

        self.llm = _build_llm(model=self.model)

    def _make_conversion_task(self, agent: Any) -> Any:
        _, _, _, Task = _import_crewai()
        return Task(
            description=(
                "You are given: (1) Original source file name `{filename}` and its code, "
                "(2) The target language `{target_language}`, and (3) Context about any "
                "previous attempt and reviewer feedback.\n\n"
                "Tasks:\n"
                "- Convert the original code to {target_language}.\n"
                "- Preserve functionality, behavior, I/O, and error handling.\n"
                "- Translate constructs idiomatically to the target language.\n"
                "- Incorporate reviewer feedback (if provided).\n\n"
                "Constraints:\n"
                "- Output ONLY the full converted code, with no explanations.\n"
                "- Do not wrap in code fences.\n\n"
                "Context for this attempt (may be empty):\n"
                "Previous attempt code (if any):\n{previous_converted}\n\n"
                "Reviewer feedback (if any):\n{review_feedback}\n\n"
                "Original `{filename}` code:\n"
                "<ORIGINAL_CODE>\n{original_code}\n</ORIGINAL_CODE>\n"
            ),
            expected_output=(
                "Only the converted source code in the target language, no prose."
            ),
            agent=agent,
        )

    def _make_review_task(self, agent: Any) -> Any:
        _, _, _, Task = _import_crewai()
        return Task(
            description=(
                "Compare the original code and the converted code.\n\n"
                "Return a STRICT JSON object with keys: \n"
                "- verdict: one of ['approve', 'revise']\n"
                "- feedback: short but concrete instructions for revision (if any)\n\n"
                "Criteria:\n"
                "- Syntactic correctness of converted code in {target_language}.\n"
                "- Completeness and functional equivalence, including error handling and edge cases.\n"
                "- Equivalent data flows, side-effects, and I/O behavior.\n\n"
                "Response format must be ONLY JSON, no code fences, no commentary.\n\n"
                "Original `{filename}` code:\n<ORIGINAL_CODE>\n{original_code}\n</ORIGINAL_CODE>\n\n"
                "Converted code candidate:\n<CONVERTED_CODE>\n{converted_code}\n</CONVERTED_CODE>\n"
            ),
            expected_output=(
                '{"verdict":"approve"|"revise","feedback":"..."}'
            ),
            agent=agent,
            output_json=ReviewVerdict,
        )

    def _run_single_task(self, agent: Any, task: Any, inputs: Dict[str, Any]) -> str:
        _, Crew, Process, _ = _import_crewai()
        crew = Crew(agents=[agent], tasks=[task], process=Process.sequential, verbose=self.verbose)
        result = crew.kickoff(inputs=inputs)
        return _normalize_task_output(result)

    def iterate(self, filename: str, original_code: str) -> ConversionResult:
        converter_agent = _make_converter_agent(self.llm, self.target_language, self.verbose)
        reviewer_agent = _make_reviewer_agent(self.llm, self.target_language, self.verbose)

        previous_converted = ""
        review_feedback = ""

        for attempt in range(1, self.max_iters + 1):
            # Run conversion
            convert_task = self._make_conversion_task(converter_agent)
            converted_code = self._run_single_task(
                converter_agent,
                convert_task,
                inputs={
                    "filename": filename,
                    "target_language": self.target_language,
                    "original_code": original_code,
                    "previous_converted": previous_converted,
                    "review_feedback": review_feedback,
                },
            )

            # Run review
            review_task = self._make_review_task(reviewer_agent)
            review_raw = self._run_single_task(
                reviewer_agent,
                review_task,
                inputs={
                    "filename": filename,
                    "target_language": self.target_language,
                    "original_code": original_code,
                    "converted_code": converted_code,
                },
            )

            review_json = _safe_json_extract(review_raw) or {}
            verdict, feedback = _extract_verdict_feedback(review_json)

            if verdict == "approve":
                return ConversionResult(
                    approved=True,
                    attempt=attempt,
                    converted_code=converted_code,
                    review_feedback=feedback,
                    verdict=verdict,
                )

            # Prepare next iteration
            previous_converted = converted_code
            review_feedback = feedback or review_raw

        # If we exhaust iterations without approval
        return ConversionResult(
            approved=False,
            attempt=self.max_iters,
            converted_code=previous_converted or None,
            review_feedback=review_feedback or None,
            verdict="revise",
        )


def resolve_output_path(input_path: Path, target_ext: str) -> Path:
    """Compute output file path based on input, swapping extension to target_ext.

    If the extension equals the original one, append ".converted" before extension.
    """

    stem = input_path.stem
    parent = input_path.parent
    orig_ext = input_path.suffix.lstrip(".")

    if orig_ext.lower() == target_ext.lower():
        return parent / f"{stem}.converted.{target_ext}"
    return parent / f"{stem}.{target_ext}"


# --- CLI --------------------------------------------------------------------

def _parse_args(argv: list[str]) -> argparse.Namespace:
    p = argparse.ArgumentParser(
        prog="veriport",
        description=(
            "Convert a source file into another language using a CrewAI converter "
            "and reviewer with iterative refinement."
        ),
        epilog="Author: Alexander Bernert",
    )
    p.add_argument("input", help="Path to the source code file to convert")
    p.add_argument(
        "--target-lang",
        "-l",
        default="python",
        help="Target language name (default: python)",
    )
    p.add_argument(
        "--ext",
        help=(
            "Override output file extension (e.g., py, js). "
            "If omitted, inferred from --target-lang."
        ),
    )
    p.add_argument(
        "--model",
        "-m",
        default="gpt-5",
        help="OpenAI model name to use (default: gpt-5)",
    )
    p.add_argument(
        "--max-iters",
        type=int,
        default=3,
        help="Maximum number of conversion-review iterations (default: 3)",
    )
    p.add_argument(
        "--verbose",
        "-v",
        action="store_true",
        help="Enable verbose agent output",
    )
    p.add_argument(
        "--dry-run",
        action="store_true",
        help="Don't write files; print verdict and summary only",
    )
    return p.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    ns = _parse_args(argv or sys.argv[1:])

    input_path = Path(ns.input)
    if not input_path.exists() or not input_path.is_file():
        print(f"[veriport] Input not found: {input_path}")
        return 2

    try:
        original_code = input_path.read_text(encoding="utf-8")
    except Exception as e:
        print(f"[veriport] Failed to read input file: {e}")
        return 2

    pipeline = ConverterPipeline(
        model=ns.model,
        target_language=ns.target_lang,
        target_ext=ns.ext,
        verbose=ns.verbose,
        max_iters=ns.max_iters,
    )

    try:
        result = pipeline.iterate(filename=input_path.name, original_code=original_code)
    except Exception as e:
        print(f"[veriport] LLM execution failed: {e}")
        return 4

    if result.approved and result.converted_code:
        out_path = resolve_output_path(input_path, pipeline.target_ext)
        if ns.dry_run:
            print("[veriport] Approved. Would write output to:", out_path)
            print(f"[veriport] Attempts: {result.attempt}")
            return 0

        try:
            out_path.write_text(result.converted_code, encoding="utf-8")
        except Exception as e:
            print(f"[veriport] Failed to write output file: {e}")
            return 3

        print(f"[veriport] Conversion approved after {result.attempt} attempt(s)")
        print(f"[veriport] Wrote: {out_path}")
        return 0

    # Not approved
    print(
        f"[veriport] Conversion not approved after {result.attempt} attempt(s).\n"
        "[veriport] Last reviewer feedback follows:\n"
        f"{(result.review_feedback or '').strip()}"
    )
    return 1


if __name__ == "__main__":  # pragma: no cover
    raise SystemExit(main())
