"""
Claude/Anthropic Service
Handles social media derivation and content strategy recommendations.
Content generation (brief → article) was removed in v4 — writing happens in Claude Projects.
"""

import logging
from anthropic import Anthropic
from config import Config
from prompts import (
    LINKEDIN_DERIVATION_PROMPT, INSTAGRAM_CAPTION_PROMPT
)

logger = logging.getLogger(__name__)


class ClaudeService:
    def __init__(self):
        self.client = Anthropic(api_key=Config.ANTHROPIC_API_KEY)
        self.model = Config.CLAUDE_MODEL

    def generate_social_post(self, content, client, platform, guidelines=None):
        """
        Generate social media post from existing content.
        
        Args:
            content: Content object (source material)
            client: Client object
            platform: 'linkedin' or 'instagram'
            guidelines: Optional platform-specific guidelines
        """
        if platform == 'linkedin':
            base_prompt = LINKEDIN_POST_PROMPT
            default_guidelines = client.linkedin_guidelines or "Distill the insight, don't summarize. Lead with the hook."
        else:
            base_prompt = INSTAGRAM_CAPTION_PROMPT
            default_guidelines = client.instagram_guidelines or "One key insight. Conversational tone."
        
        system_prompt = f"""{base_prompt}

=== BRAND VOICE ===
{client.get_brand_voice_section()}

=== PLATFORM GUIDELINES ===
{guidelines or default_guidelines}
"""
        
        user_prompt = f"""Create a {platform} post based on this content:

**Title:** {content.meta_title or content.h1}

**Content:**
{content.body[:3000]}

---
Generate the {platform} post now.
"""
        
        try:
            response = self.client.messages.create(
                model=self.model,
                max_tokens=1024,
                system=system_prompt,
                messages=[
                    {"role": "user", "content": user_prompt}
                ]
            )
            
            return response.content[0].text.strip()
            
        except Exception as e:
            logger.error(f"Claude API error generating social post: {e}")
            raise
