import re

class ContentParser:
    """Parses generated content into structured parts."""
    
    @staticmethod
    def parse_generated_content(raw_content):
        """Parse raw AI output into structured content."""
        result = {
            'meta_title': None,
            'meta_description': None,
            'h1': None,
            'body': None,
            'internal_links_suggested': []
        }
        
        if not raw_content:
            return result
        
        content = raw_content.strip()
        
        # Extract META_TITLE
        meta_title_match = re.search(r'META_TITLE:\s*(.+?)(?:\n|$)', content)
        if meta_title_match:
            result['meta_title'] = meta_title_match.group(1).strip()
        
        # Extract META_DESCRIPTION
        meta_desc_match = re.search(r'META_DESCRIPTION:\s*(.+?)(?:\n|$)', content)
        if meta_desc_match:
            result['meta_description'] = meta_desc_match.group(1).strip()
        
        # Extract INTERNAL_LINKS_SUGGESTED
        links_match = re.search(r'INTERNAL_LINKS_SUGGESTED:\s*(.+?)(?:\n|$)', content)
        if links_match:
            links_str = links_match.group(1).strip()
            result['internal_links_suggested'] = [
                link.strip() for link in links_str.split(',') if link.strip()
            ]
        
        # Extract H1 (first # heading)
        h1_match = re.search(r'^#\s+(.+?)$', content, re.MULTILINE)
        if h1_match:
            result['h1'] = h1_match.group(1).strip()
        
        # Extract body (content between --- markers, excluding meta info)
        # First, try to find content between --- markers
        body_match = re.search(r'^---\s*\n(.*?)(?:\n---\s*$|\n---\s*\nINTERNAL_LINKS)', content, re.DOTALL | re.MULTILINE)
        
        if body_match:
            body = body_match.group(1).strip()
        else:
            # Fallback: remove meta lines and use rest as body
            body = content
            # Remove META lines
            body = re.sub(r'META_TITLE:\s*.+?\n', '', body)
            body = re.sub(r'META_DESCRIPTION:\s*.+?\n', '', body)
            body = re.sub(r'INTERNAL_LINKS_SUGGESTED:\s*.+?(?:\n|$)', '', body)
            body = re.sub(r'^---\s*$', '', body, flags=re.MULTILINE)
            body = body.strip()
        
        # Clean up the body
        body = re.sub(r'SCHEMA_READY:\s*true\s*', '', body)
        result['body'] = body.strip()
        
        return result
    
    @staticmethod
    def extract_word_count(content):
        """Count words in content body."""
        if not content:
            return 0
        return len(content.split())
    
    @staticmethod
    def markdown_to_html(markdown_text):
        """Convert markdown to basic HTML."""
        if not markdown_text:
            return ""
        
        html = markdown_text
        
        # Headers
        html = re.sub(r'^### (.+)$', r'<h3>\1</h3>', html, flags=re.MULTILINE)
        html = re.sub(r'^## (.+)$', r'<h2>\1</h2>', html, flags=re.MULTILINE)
        html = re.sub(r'^# (.+)$', r'<h1>\1</h1>', html, flags=re.MULTILINE)
        
        # Bold
        html = re.sub(r'\*\*(.+?)\*\*', r'<strong>\1</strong>', html)
        
        # Italic
        html = re.sub(r'\*(.+?)\*', r'<em>\1</em>', html)
        
        # Line breaks to paragraphs
        paragraphs = html.split('\n\n')
        html = ''.join(f'<p>{p.strip()}</p>' for p in paragraphs if p.strip() and not p.strip().startswith('<h'))
        
        # Re-add headers
        for p in paragraphs:
            if p.strip().startswith('<h'):
                html = html.replace(f'<p>{p.strip()}</p>', p.strip())
        
        return html
    
    # Alias for convenience
    def parse(self, raw_content, content_type=None):
        """Alias for parse_generated_content."""
        return self.parse_generated_content(raw_content)
