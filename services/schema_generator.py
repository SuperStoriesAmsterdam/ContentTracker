import json
import re
from datetime import datetime

class SchemaGenerator:
    """Generates JSON-LD schema markup for content."""
    
    @staticmethod
    def generate_article_schema(content, client, brief=None):
        """Generate Article + FAQPage schema."""
        schema = {
            "@context": "https://schema.org",
            "@graph": []
        }
        
        # Article schema
        article = {
            "@type": "Article",
            "headline": content.h1 or content.meta_title,
            "description": content.meta_description,
            "author": {
                "@type": "Organization",
                "name": client.name
            },
            "publisher": {
                "@type": "Organization",
                "name": client.name
            },
            "datePublished": content.created_at if isinstance(content.created_at, str) else datetime.now().isoformat(),
            "dateModified": datetime.now().isoformat()
        }
        
        if brief and brief.primary_keyword:
            article["keywords"] = brief.primary_keyword
        
        schema["@graph"].append(article)
        
        # Extract FAQ and add FAQPage schema
        faq_items = SchemaGenerator._extract_faq_from_content(content.body)
        if faq_items:
            faq_schema = {
                "@type": "FAQPage",
                "mainEntity": [
                    {
                        "@type": "Question",
                        "name": q["question"],
                        "acceptedAnswer": {
                            "@type": "Answer",
                            "text": q["answer"]
                        }
                    }
                    for q in faq_items
                ]
            }
            schema["@graph"].append(faq_schema)
        
        return json.dumps(schema, indent=2, ensure_ascii=False)
    
    @staticmethod
    def generate_faq_schema(content):
        """Generate standalone FAQPage schema."""
        faq_items = SchemaGenerator._extract_faq_from_content(content.body)
        
        schema = {
            "@context": "https://schema.org",
            "@type": "FAQPage",
            "mainEntity": [
                {
                    "@type": "Question",
                    "name": q["question"],
                    "acceptedAnswer": {
                        "@type": "Answer",
                        "text": q["answer"]
                    }
                }
                for q in faq_items
            ]
        }
        
        return json.dumps(schema, indent=2, ensure_ascii=False)
    
    @staticmethod
    def generate_press_release_schema(content, client):
        """Generate NewsArticle schema for press releases."""
        schema = {
            "@context": "https://schema.org",
            "@type": "NewsArticle",
            "headline": content.h1 or content.meta_title,
            "description": content.meta_description,
            "author": {
                "@type": "Organization",
                "name": client.name
            },
            "publisher": {
                "@type": "Organization",
                "name": client.name
            },
            "datePublished": content.created_at if isinstance(content.created_at, str) else datetime.now().isoformat()
        }
        
        return json.dumps(schema, indent=2, ensure_ascii=False)
    
    @staticmethod
    def generate_product_schema(content, client, brief=None):
        """Generate Product schema."""
        schema = {
            "@context": "https://schema.org",
            "@type": "Product",
            "name": content.h1 or brief.primary_keyword if brief else "Product",
            "description": content.meta_description,
            "brand": {
                "@type": "Brand",
                "name": client.name
            }
        }
        
        # Add FAQ if present
        faq_items = SchemaGenerator._extract_faq_from_content(content.body)
        if faq_items:
            schema["mainEntity"] = [
                {
                    "@type": "Question",
                    "name": q["question"],
                    "acceptedAnswer": {
                        "@type": "Answer",
                        "text": q["answer"]
                    }
                }
                for q in faq_items
            ]
        
        return json.dumps(schema, indent=2, ensure_ascii=False)
    
    @staticmethod
    def _extract_faq_from_content(body):
        """Extract Q&A pairs from content body."""
        if not body:
            return []
        
        # Pattern for "**Vraag: question**\nanswer" or "**Question: question**\nanswer"
        pattern = r'\*\*(?:Vraag|Question):\s*([^\*]+)\*\*\s*\n([^\*\n]+(?:\n[^\*\n]+)*)'
        matches = re.findall(pattern, body, re.IGNORECASE)
        
        faq_items = []
        for question, answer in matches:
            # Clean up the answer (remove extra whitespace, limit length)
            answer_clean = ' '.join(answer.split())
            if len(answer_clean) > 500:
                answer_clean = answer_clean[:497] + "..."
            
            faq_items.append({
                "question": question.strip(),
                "answer": answer_clean
            })
        
        return faq_items
    
    @staticmethod
    def generate_for_content(content, client, brief=None):
        """Generate appropriate schema based on content type."""
        content_type = content.content_type
        
        if content_type == 'press_release':
            return SchemaGenerator.generate_press_release_schema(content, client)
        elif content_type == 'faq':
            return SchemaGenerator.generate_faq_schema(content)
        elif content_type == 'product_description':
            return SchemaGenerator.generate_product_schema(content, client, brief)
        else:
            return SchemaGenerator.generate_article_schema(content, client, brief)
    
    # Alias for backward compatibility
    generate_schema = generate_for_content
