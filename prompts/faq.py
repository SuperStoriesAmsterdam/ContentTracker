FAQ_PROMPT = """
You are creating an FAQ section for {client_name}'s website.

## BRAND VOICE
{brand_voice_section}

## STYLE EXAMPLES
{style_examples}

{voice_material_section}

## ASSIGNMENT
Create a comprehensive FAQ section in {language}.

Topic/Page: {primary_keyword}
Target Audience: {target_icp}
Number of Questions: {faq_count}

## REQUIREMENTS

1. **Question Format**
   - Write questions as real people would ask them
   - Use natural search query language
   - Mix "what", "how", "why", "when" questions
   - Include long-tail question phrases

2. **Answer Format**
   - Direct answer in first sentence
   - Supporting detail in 2-3 additional sentences
   - Avoid marketing fluff
   - Include specific details where possible

3. **LLM Optimization**
   - Each Q&A should be independently citeable
   - Answers should be factual and specific
   - Include numbers, timeframes, or specifics where relevant
   - Answers should work as standalone responses to voice search

4. **Question Categories to Cover**
   - What questions (definitions, explanations)
   - How questions (process, methods)
   - Why questions (benefits, reasons)
   - When/Where questions (timing, availability)
   - Cost/Price questions if relevant
   - Comparison questions if relevant

## OUTPUT FORMAT
Provide exactly {faq_count} Q&As in this format:

**Vraag: [Question]**
[Answer - 2-4 sentences, direct and specific]

**Vraag: [Question]**
[Answer]

[Continue for all questions]

---

SCHEMA_READY: true
"""
