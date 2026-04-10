# SuperStories Content Engine v3

AI-powered B2B content generation platform using **Claude** for content and **OpenAI** for RAG embeddings.

## Wat is nieuw in v3

| Feature | Beschrijving |
|---------|-------------|
| **Claude API** | Content generatie via Claude (Anthropic) i.p.v. OpenAI |
| **Twee Content Tracks** | SEO Content vs Thought Leadership / Substack |
| **Answer Target** | Specifieke vraag die content moet beantwoorden (LLM citability) |
| **Citability Checks** | 4 nieuwe checks voor LLM-citatie optimalisatie |
| **Strategy Documents** | Upload SEO strategie, RAG verbindt automatisch |
| **Content Track Filter** | Documents filteren per track (SEO / Thought Leadership / Both) |
| **Quotable Snippet** | Automatisch gegenereerde citeerbare snippet |
| **Author Attribution** | Client-level auteur voor E-E-A-T signalen |

## Installatie in Replit

### 1. Upload & Extract

```bash
unzip superstories-v3.zip
mv superstories-v3/* .
rm -rf superstories-v3 superstories-v3.zip
```

### 2. Secrets Configureren

In Replit → Tools → Secrets:

| Key | Value | Verplicht |
|-----|-------|-----------|
| ANTHROPIC_API_KEY | Je Claude API key | ✅ |
| OPENAI_API_KEY | Je OpenAI key (voor embeddings) | ✅ voor RAG |
| SECRET_KEY | Random string | ✅ |
| GOOGLE_CLIENT_ID | Uit Google Cloud Console | ❌ optioneel |
| GOOGLE_CLIENT_SECRET | Uit Google Cloud Console | ❌ optioneel |

### 3. Run

```bash
python app.py
```

## Content Tracks

**SEO Track:** Geoptimaliseerd voor zoekmachines en LLM citatie
- Velden: Answer Target, Primary Keyword, Search Intent
- Output: FAQ sectie, Schema JSON-LD, Citability checks

**Thought Leadership Track:** Persoonlijk, opiniërend, insight-driven  
- Velden: Core Thesis, Contrarian Angle, Personal Story
- Output: Flowing prose, quotable snippet

## Document Types

- `knowledge` - Feiten, methodes, informatie
- `style` - Schrijfvoorbeelden om te matchen
- `strategy` - SEO strategie documenten
- `both` - Knowledge + Style

## API Keys nodig

| Service | Waarvoor | Model |
|---------|----------|-------|
| Anthropic | Content generatie | claude-sonnet-4-20250514 |
| OpenAI | RAG embeddings | text-embedding-3-small |
| Google | Docs, Search Console, Analytics | (optioneel) |
