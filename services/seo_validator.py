import re

class SEOValidator:
    """Validates content for SEO and LLM optimization."""
    
    @staticmethod
    def check_keyword_in_h1(content, brief):
        """Check if primary keyword is in H1."""
        if not content.h1 or not brief.primary_keyword:
            return {'passed': False, 'reason': 'Missing H1 or keyword'}
        
        keyword_lower = brief.primary_keyword.lower()
        h1_lower = content.h1.lower()
        
        return {
            'passed': keyword_lower in h1_lower,
            'h1': content.h1,
            'keyword': brief.primary_keyword
        }
    
    @staticmethod
    def check_keyword_in_first_100_words(content, brief):
        """Check if primary keyword appears in first 100 words."""
        if not content.body or not brief.primary_keyword:
            return {'passed': False, 'reason': 'Missing content or keyword'}
        
        words = content.body.split()[:100]
        first_100 = ' '.join(words).lower()
        keyword_lower = brief.primary_keyword.lower()
        
        return {
            'passed': keyword_lower in first_100,
            'keyword': brief.primary_keyword
        }
    
    @staticmethod
    def check_meta_title_length(content):
        """Check meta title length (50-60 characters ideal)."""
        if not content.meta_title:
            return {'passed': False, 'length': 0, 'reason': 'Missing meta title'}
        
        length = len(content.meta_title)
        return {
            'passed': 50 <= length <= 60,
            'length': length,
            'ideal_range': '50-60 characters'
        }
    
    @staticmethod
    def check_meta_description_length(content):
        """Check meta description length (150-160 characters ideal)."""
        if not content.meta_description:
            return {'passed': False, 'length': 0, 'reason': 'Missing meta description'}
        
        length = len(content.meta_description)
        return {
            'passed': 150 <= length <= 160,
            'length': length,
            'ideal_range': '150-160 characters'
        }
    
    @staticmethod
    def check_h2_count(content):
        """Check number of H2 headings (3-6 ideal for most articles)."""
        if not content.body:
            return {'passed': False, 'count': 0}
        
        h2_count = len(re.findall(r'^##\s+[^#]', content.body, re.MULTILINE))
        return {
            'passed': 3 <= h2_count <= 8,
            'count': h2_count,
            'ideal_range': '3-8 headings'
        }
    
    @staticmethod
    def check_forbidden_words(content, client):
        """Check if content contains forbidden words."""
        if not content.body or not client.forbidden_words:
            return {'passed': True, 'found': []}
        
        body_lower = content.body.lower()
        found_words = []
        
        for word in client.forbidden_words:
            if word.lower() in body_lower:
                found_words.append(word)
        
        return {
            'passed': len(found_words) == 0,
            'found': found_words
        }
    
    @staticmethod
    def check_word_count(content, brief):
        """Check if word count is near target."""
        if not content.body:
            return {'passed': False, 'count': 0}
        
        word_count = len(content.body.split())
        target = brief.word_count_target or 1500
        
        # Allow 20% variance
        min_count = int(target * 0.8)
        max_count = int(target * 1.2)
        
        return {
            'passed': min_count <= word_count <= max_count,
            'count': word_count,
            'target': target,
            'range': f'{min_count}-{max_count}'
        }
    
    @staticmethod
    def check_has_faq_section(content):
        """Check if content has FAQ section."""
        if not content.body:
            return {'passed': False, 'count': 0}
        
        body_lower = content.body.lower()
        
        # Check for FAQ markers
        has_faq_header = any(marker in body_lower for marker in [
            'veelgestelde vragen', 'frequently asked', 'faq', 
            'veel gestelde vragen', 'common questions'
        ])
        
        # Count Q&A pairs
        qa_count = len(re.findall(r'\*\*vraag:|question:', body_lower))
        
        return {
            'passed': has_faq_header and qa_count >= 3,
            'count': qa_count,
            'has_header': has_faq_header
        }
    
    @staticmethod
    def check_ai_answerable_paragraph(content, brief):
        """Check if first 200 words contain clear, citeable answer."""
        if not content.body or not brief.primary_keyword:
            return {'passed': False, 'reason': 'Missing content or keyword'}
        
        # Get first 200 words
        words = content.body.split()
        first_200 = ' '.join(words[:200]).lower()
        
        # Check if primary keyword is present
        has_keyword = brief.primary_keyword.lower() in first_200
        
        # Check for answer indicators
        answer_indicators = ['is', 'zijn', 'betekent', 'houdt in', 'refers to', 'means', 'allows', 'enables', 'provides']
        has_answer_structure = any(indicator in first_200 for indicator in answer_indicators)
        
        return {
            'passed': has_keyword and has_answer_structure,
            'has_keyword': has_keyword,
            'has_answer_structure': has_answer_structure
        }
    
    @staticmethod
    def check_citeable_soundbite(content):
        """Check for presence of quotable/distinctive insight."""
        if not content.body:
            return {'passed': False}
        
        body = content.body
        
        # Heuristic patterns for distinctive statements
        indicators = [
            '—',  # em-dash
            'the key is',
            'de sleutel is',
            'what most people miss',
            'wat de meeste mensen missen',
            'the real question',
            'de echte vraag',
            'fundamentally',
            'fundamenteel',
            'the difference between',
            'het verschil tussen',
            'unlike',
            'in tegenstelling tot'
        ]
        
        has_soundbite = any(indicator.lower() in body.lower() for indicator in indicators)
        
        return {'passed': has_soundbite}
    
    @staticmethod
    def run_all_checks(content, brief, client):
        """Run all SEO checks and return results."""
        checks = {}
        
        # Traditional SEO Checks
        h1_result = SEOValidator.check_keyword_in_h1(content, brief)
        checks['keyword_in_h1'] = {
            'name': 'Keyword in H1',
            'description': f'Primary keyword "{brief.primary_keyword}" in heading',
            'passed': h1_result['passed'],
            'severity': 'error'
        }
        
        first_100_result = SEOValidator.check_keyword_in_first_100_words(content, brief)
        checks['keyword_in_first_100'] = {
            'name': 'Keyword in First 100 Words',
            'description': 'Primary keyword appears early in content',
            'passed': first_100_result['passed'],
            'severity': 'warning'
        }
        
        meta_title_result = SEOValidator.check_meta_title_length(content)
        checks['meta_title_length'] = {
            'name': 'Meta Title Length',
            'description': f'{meta_title_result.get("length", 0)} characters (ideal: 50-60)',
            'passed': meta_title_result['passed'],
            'severity': 'warning'
        }
        
        meta_desc_result = SEOValidator.check_meta_description_length(content)
        checks['meta_description_length'] = {
            'name': 'Meta Description Length',
            'description': f'{meta_desc_result.get("length", 0)} characters (ideal: 150-160)',
            'passed': meta_desc_result['passed'],
            'severity': 'warning'
        }
        
        h2_result = SEOValidator.check_h2_count(content)
        checks['h2_count'] = {
            'name': 'H2 Subheadings',
            'description': f'{h2_result["count"]} headings found',
            'passed': h2_result['passed'],
            'severity': 'info'
        }
        
        forbidden_result = SEOValidator.check_forbidden_words(content, client)
        checks['forbidden_words'] = {
            'name': 'Forbidden Words',
            'description': f'Found: {", ".join(forbidden_result["found"])}' if forbidden_result["found"] else 'None found',
            'passed': forbidden_result['passed'],
            'severity': 'error'
        }
        
        word_count_result = SEOValidator.check_word_count(content, brief)
        checks['word_count'] = {
            'name': 'Word Count',
            'description': f'{word_count_result["count"]} words (target: {brief.word_count_target or 1500})',
            'passed': word_count_result['passed'],
            'severity': 'info'
        }
        
        # LLM SEO Checks
        faq_result = SEOValidator.check_has_faq_section(content)
        checks['has_faq_section'] = {
            'name': 'FAQ Section',
            'description': f'{faq_result["count"]} Q&As found',
            'passed': faq_result['passed'],
            'severity': 'warning'
        }
        
        ai_answer_result = SEOValidator.check_ai_answerable_paragraph(content, brief)
        checks['ai_answerable'] = {
            'name': 'AI-Answerable Paragraph',
            'description': 'First 200 words contain clear, citeable answer',
            'passed': ai_answer_result['passed'],
            'severity': 'warning'
        }
        
        soundbite_result = SEOValidator.check_citeable_soundbite(content)
        checks['citeable_soundbite'] = {
            'name': 'Citeable Soundbite',
            'description': 'Contains distinctive, quotable insight',
            'passed': soundbite_result['passed'],
            'severity': 'info'
        }
        
        return checks
