THOUGHT_LEADERSHIP_PROMPT = """
You are writing a thought leadership essay for {client_name}.

## BRAND VOICE
{brand_voice_section}

## STYLE EXAMPLES
{style_examples}

{voice_material_section}

## ASSIGNMENT
Write a thought leadership essay in {language}.

Topic: {primary_keyword}
Target Reader: {target_icp}
Target Word Count: {word_count}

## SPECIAL INSTRUCTIONS
Must include:
{must_include}

Must avoid:
{must_avoid}

Additional notes:
{special_instructions}

## THOUGHT LEADERSHIP REQUIREMENTS

### Core Principles
- Lead with insight, not information
- Make one clear distinction that reframes how readers think
- Use specific moments and examples, not generalizations
- Write from lived experience, not theory
- Challenge conventional thinking without being contrarian

### Structure
1. **Opening** (1-2 paragraphs)
   - Start close to a moment, situation, or tension
   - Create immediate recognition ("this is about me")
   - Don't explain what you're going to say

2. **Distinction** (1-2 paragraphs)
   - Make the core reframe or insight explicit
   - Use contrast: "most people think X, but actually Y"
   - Be specific about the shift in perspective

3. **Exploration** (2-4 paragraphs)
   - Develop the insight with examples
   - Show, don't tell
   - Include lived experience where relevant
   - Let complexity exist without resolving it

4. **Implications** (1-2 paragraphs)
   - What does this mean for the reader?
   - Practical applications without being prescriptive
   - Leave space for reader's own reflection

5. **Closing** (1 paragraph)
   - Land softly
   - Don't summarize or conclude definitively
   - Leave the reader thinking

### Voice Guidelines
- Conversational but not casual
- Confident but not arrogant
- Direct but not abrupt
- Reflective but not indulgent
- Avoid: motivational speak, jargon, prescriptive advice

### What Makes It Thought Leadership
- Original insight based on experience
- Challenges assumptions
- Creates new vocabulary or framing
- Respects the reader's intelligence
- Invites rather than instructs

## OUTPUT FORMAT
META_TITLE: [50-60 characters, intriguing]
META_DESCRIPTION: [150-155 characters, captures the core insight]

---

# [Title - intriguing, not explanatory]

[Essay body - no subheadings unless truly necessary]
"""
