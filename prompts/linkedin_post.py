LINKEDIN_DERIVATION_PROMPT = """
You are deriving a LinkedIn post from a long-form essay for {client_name}.

## CONTEXT
Author: {author_name}
Author positioning: {author_positioning}

## CLIENT-SPECIFIC LINKEDIN GUIDELINES
{linkedin_guidelines}

## STYLE EXAMPLES
These are examples of successful LinkedIn posts for this client:
{style_examples}

## THE SOURCE CONTENT
{essay_content}

{voice_material_section}

## CONSTRAINTS
- No external links
- No hashtags
- No emojis
- No call-to-action
- Maximum 200 words

## OUTPUT
Write the LinkedIn post now. Nothing else.
"""

# Default guidelines if client hasn't configured their own
DEFAULT_LINKEDIN_GUIDELINES = """
A post works when it:
- Makes one clear distinction relevant to professional/relational life
- Starts close to a concrete moment (workplace, decision, tension)
- Uses everyday language, not jargon
- Leaves the reader with a felt re-orientation, not advice

A post fails when it:
- Summarizes the essay instead of distilling it
- Explains methods or names frameworks
- Sounds motivational, inspirational, or instructional
- Attempts to persuade or close

Structure:
- 1-2 sentence situational hook
- One sharp distinction or reframing
- One brief lived example
- Soft closing line that invites reflection
"""
