INSTAGRAM_CAPTION_PROMPT = """
You are extracting a single-sentence insight from content for {client_name}'s Instagram.

## CLIENT-SPECIFIC INSTAGRAM GUIDELINES
{instagram_guidelines}

## STYLE EXAMPLES
These are examples of successful Instagram posts for this client:
{style_examples}

## THE SOURCE CONTENT
{essay_content}

## OUTPUT
Write exactly one sentence. Nothing else. No quotation marks.
"""

# Default guidelines if client hasn't configured their own
DEFAULT_INSTAGRAM_GUIDELINES = """
The sentence must:
- Stand completely alone without context
- Name a specific mechanism, benefit, or insight in plain language
- Create a moment of recognition
- Reframe a familiar situation without blame
- Be exactly ONE sentence

The sentence must NOT:
- Explain or teach anything
- Reference the source content or method
- Include a call-to-action
- Sound like a motivational quote
- Use jargon or technical terms
"""
