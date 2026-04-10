"""
Prompts for extracting structured intelligence from conversation transcripts.
Used by the transcript extraction flow in v4.
"""

import json
import re


EXPERT_PROFILE_EXTRACTION_SYSTEM = """You are an expert at extracting structured intelligence from conversation transcripts.
You extract only what is genuinely present in the transcript — never invent or infer beyond what is explicitly said.
Return ONLY valid JSON. No preamble. No explanation. No markdown code fences. Just the raw JSON object."""


EXPERT_PROFILE_EXTRACTION_USER = """Extract the following from this transcript and return as JSON matching this exact schema:

{
  "core_beliefs": [{"text": "...", "confidence": "high|medium|low"}],
  "personal_stories": [{"title": "...", "summary": "..."}],
  "contrarian_positions": [{"text": "...", "confidence": "high|medium|low"}],
  "signature_phrases": [{"phrase": "...", "context": "..."}],
  "topics_of_passion": [{"topic": "..."}]
}

Definitions:
- core_beliefs: things the expert states as fundamental truths about their field or work
- personal_stories: named experiences, client cases, or anecdotes they reference
- contrarian_positions: where they explicitly disagree with mainstream thinking or conventional wisdom
- signature_phrases: specific language patterns, vocabulary, or phrases they use repeatedly
- topics_of_passion: subjects they return to with evident energy or emphasis

Rules:
- If nothing is found for a category, return an empty array []
- Maximum 8 items per category — prioritise the clearest, most distinctive examples
- Do not summarise or paraphrase — capture the expert's actual language where possible
- For contrarian_positions, only include positions they explicitly contrast against something else

TRANSCRIPT:
{transcript_text}"""


def parse_claude_extraction(raw_response: str) -> dict:
    """
    Parse Claude's extraction response into a Python dict.
    Handles cases where Claude adds preamble text or markdown code fences
    despite being instructed not to.
    Also guards against truncated JSON (output token limit reached).
    """
    text = raw_response.strip()

    # Remove markdown code fences if present
    text = re.sub(r'^```(?:json)?\s*', '', text)
    text = re.sub(r'\s*```$', '', text)
    text = text.strip()

    # Find the first { and last } to extract just the JSON object
    start = text.find('{')
    end = text.rfind('}')
    if start == -1 or end == -1:
        raise ValueError(
            f"No JSON object found in Claude response. "
            f"The transcript may be too long — try a shorter excerpt. "
            f"Raw response start: {text[:200]}"
        )

    json_str = text[start:end + 1]

    try:
        return json.loads(json_str)
    except json.JSONDecodeError as error:
        raise ValueError(
            f"Failed to parse JSON from Claude response. "
            f"The transcript may be too long and the response was cut off. "
            f"Error: {error}. "
            f"Raw JSON start: {json_str[:200]}"
        )


def build_extraction_prompt(transcript_text: str) -> str:
    """Return the user prompt with the transcript text inserted."""
    return EXPERT_PROFILE_EXTRACTION_USER.format(transcript_text=transcript_text)
