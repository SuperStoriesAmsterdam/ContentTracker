# contenttracker for SEO operators — working guide

**Purpose:** onboarding + ongoing reference for the SuperStories SEO + Analytics operator role.
**Audience:** the hired SEO operator (primary) · Peter van Rhoon and candidates being evaluated (secondary).
**Status:** Living document · v1.0 · 2026-04-18.

---

## How to use this guide

Read top to bottom once during onboarding. Refer back to §5–§7 weekly. Use §7 when you want to make the case for a new tool. Update this doc whenever you learn something an incoming operator should know — same living-doc conventions as the rest of the SuperStories tooling.

---

## 1. What contenttracker is

contenttracker is SuperStories' internal **content decision + measurement tool** — a multi-tenant Flask app where each agency client has their own workspace. It exists to answer one question every week for every client: **what should we write next, and did what we wrote before work?**

### What it does

- Pulls performance data from **Google Search Console** (impressions, clicks, CTR, position) and **GA4** (pageviews, users, conversions, conversion value).
- Tracks keyword targets per client in a **three-zone system**:
  - **Zone 1** — flagship terms the brand must own (founder name, method name, core positioning)
  - **Zone 2** — page-2 keywords (position 5–10) that need a push
  - **Zone 3** — quick wins (position 11–20) where minor updates move the needle
- Creates structured **briefs** — primary keyword, secondary keywords, search intent, word count, voice rules, forbidden words, target ICP.
- Generates content via Claude from briefs (meta title, meta description, H1, body, JSON-LD schema, quotable LLM citation snippets).
- Derives social posts per platform from each long-form piece.
- Surfaces opportunities weekly — Zone 3 candidates, content gaps via AI recommendations.
- Snapshots GSC over time so keyword trajectories are visible (position 47 → 23 → 12 → 7).
- Aggregates multi-site performance when a client has multiple domains.
- Tracks ad spend (manual) alongside organic for apples-to-apples comparison.
- Exports every dashboard to **Markdown + Excel** (shipped 2026-04-18).
- **Coming:** GHL integration — joins revenue from GoHighLevel contacts/opportunities back to specific content pieces via UTM parameters.

### What it explicitly does NOT do

- No keyword research — users add targets after discovery elsewhere.
- No competitive domain analysis.
- No technical SEO audits (no CWV, no crawl reports).
- No scraped SERP rank tracking — only what GSC shows.
- No writing in a void — actual writing happens in Claude Projects where client voice lives.

## 2. Why it's built this way

The tool is deliberately a **pipeline + decision tool, not a research tool.** It pairs with:

- External tools for keyword discovery + technical audits (§6)
- Claude Projects for actual writing
- GSC + GA4 for measurement
- GHL (coming) for revenue attribution

Trying to be everything would mean doing nothing well. This constraint is a feature. Your job as operator is to be fluent across the external tools and use contenttracker as the central pipeline.

---

## 3. Working rhythms

### Weekly (operational)

- **Monday:** scan GSC dashboard. Impressions trend, moved positions, anomalies. A sudden drop usually = competitor stepped up; a climb = Google re-indexed a refresh.
- **Review Zone 3 opportunities** — highest ROI moves; minor updates push page-2 terms into top 10.
- **Review conversions dashboard.** A page ranking high but not converting is a CTA/intent-mismatch problem, not an SEO problem.
- **Create 1–2 briefs:** one Zone 3 push (optimize existing), one Zone 2 expansion (new piece targeting adjacent term).
- **Mark last week's publications as published** (enter URL). Closes the loop so contenttracker tracks that URL in GSC.

### Monthly (strategic)

- Run AI content strategy recommendations. Treat as input, not orders.
- Take a GSC snapshot (the historical record).
- Audit keyword targets — remove stale, promote Zone 3 → Zone 2 as they climb, retire won Zone 1s.
- Export dashboards to Excel → feeds the client's monthly report.
- Check ad-spend vs organic — if the engine's working, paid per-acquisition trends down while organic conversions trend up.

### Quarterly (meta)

- **ICP review:** which audience actually converts? Rewrites the next quarter's plan.
- **Content freshness audit:** 6+ month-old pieces trending down → refresh candidates.
- **Cross-domain review** for multi-site clients.
- **Brief template iteration** — encode what's producing high-ranking content.

---

## 4. Scale of SuperStories clients

Clients are small. This matters for every tool + workflow decision in this doc. You are not running an enterprise content program with a $10k/month tool stack — you're running focused content programs for experts and small businesses where a $15–65/month tool stack needs to deliver results.

When a tool costs more than a client's average weekly revenue from content, the tool probably isn't the answer. Build the operator stack to match.

---

## 5. The starter stack (under $15/month, fully operational)

| Tool | Monthly | What it does |
|---|---|---|
| Google Search Console | **FREE** | Keyword discovery via "Queries" report · position + click + impression data per URL. Most underused discovery tool. |
| Google Keyword Planner | **FREE** | Real search volume. Needs Google Ads account, no active spend required. |
| Google Trends + PAA + Autocomplete | **FREE** | Seasonality + question-shaped keywords via manual browsing. |
| AnswerThePublic (free tier) | **FREE** | Question visualization around a topic. |
| Reddit + niche forums | **FREE** | Real language your ICP uses. Often better than keyword tools for content framing. |
| Claude (via Claude Projects) | included | Generate candidate keywords, write content, brainstorm angles. |
| Keywords Everywhere | **~$12** | Browser extension; volume/CPC inline on every Google search. Credit-based; $12 = ~100k credits. |
| **Starter total** | **~$12** | complete operating stack for small-client work |

This stack gets you 80% of what Ahrefs or Semrush would. Start here. Prove value. Earn the budget for §7 upgrades.

---

## 6. What about the stuff contenttracker doesn't cover

### Keyword discovery
Covered by the starter stack. GSC's "Queries where your site appears at position 20+" is a goldmine — those are terms Google thinks you're relevant for but you haven't prioritized. Pull 50 of them per client per month, filter by impressions, assign Zones.

### Competitive audits
**Mostly skip at small-client scale.** The "quarterly audit of 3–5 competitors" pattern is for agencies fighting over enterprise head terms. Your clients live in voice territories, not head-term battlegrounds.

Keep it ad-hoc instead:
- When writing a high-stakes piece — 10 minutes of "who else covers this, what angles have they taken" to sharpen your own.
- When a competitor suddenly outranks a client on something important — diagnostic, not routine.
- When a client asks "why is X ahead of us?" — probably once per quarter, handle then.

### Technical SEO
Not your job to execute; your job to **surface issues to the dev/Webflow team** when they matter for content performance. Contenttracker doesn't do tech audits today — but a future feature (see §8) could surface weekly Core Web Vitals + indexing issues using free Google APIs. Until then: if a client's content is ranking low for odd reasons, run [Google PageSpeed Insights](https://pagespeed.web.dev/) and check GSC's Coverage report manually.

### SERP features (featured snippets, AI Overviews, FAQ rich results)
Not visible without a SERP API. See §7 DataForSEO upgrade trigger.

### Seasonality + trends
Google Trends, free. Check when planning publication timing for seasonal topics.

### Backlinks
Underused at this scale. **GSC's Links report is free and enough for monthly check-ins.** Spot-check 1–2× per quarter. Paid backlink tools become relevant only when a client has a digital PR push or link-building project on the calendar.

---

## 7. When to recommend upgrading the stack

**The principle: start lean. Prove value. Earn the budget.**

Peter's default posture is minimalist — spend nothing until there's a clear case. Your job as operator is to make the clear case when you see one. You are empowered to recommend tool additions. The expectation is that recommendations come after you've been in the role long enough to know what question the tool would answer.

### Making the case

Write your recommendation directly in this doc (§10 change log + a short paragraph above it) before requesting the subscription. The case needs:

1. **What gap the tool closes** — what signal are you missing today?
2. **What decisions the tool would improve** — what will you do differently with it?
3. **Expected ROI window** — when will the monthly cost pay back?

Discuss with Peter in your next sync. If approved, add the tool to §5 or mark it in §7 as "adopted on YYYY-MM-DD."

### Candidate upgrades + trigger signals

#### Mangools ($29–49/month, bundle: KWFinder + SERPChecker + SiteProfiler + LinkMiner + SERPWatcher)
A genuinely useful all-in-one at a fraction of Ahrefs / Semrush price. Most likely first upgrade.

**Trigger signals:**
- You've exhausted GSC's built-in keyword discovery and can't find fresh Zone 2/3 candidates.
- You need keyword difficulty scores to prioritize between two otherwise-equal candidates.
- A client is asking "why are we ranked below X?" and you want backlink data to answer properly.
- You've been in the role 2+ months and have a concrete list of workflows Mangools would unblock.

**Default: recommend adopting in month 3–4 if the above signals have shown up.**

#### DataForSEO SERP API (~$3–5/month when routed via contenttracker)
Cheapest route to actual SERP feature monitoring. Pay-per-query, no minimum.

**Trigger signals:**
- Zone 1 keywords exist where SERP presence (featured snippets, AI Overviews) matters beyond raw rank.
- A client specifically wants competitive SERP monitoring for their brand terms.
- You've spec'd a "SERP monitoring" feature for contenttracker and need the data layer.

**Prerequisite:** requires contenttracker engineering work to integrate. Make the case *before* doing the scoping.

#### LowFruits ($15–30/month)
Dedicated low-competition keyword finder. Narrower than Mangools but sometimes sharper for content-led SEO.

**Trigger signals:**
- The starter stack isn't surfacing enough Zone 3 candidates to keep the content pipeline full.
- You're manually spending hours per week on long-tail keyword research.
- Your clients serve niche audiences where "difficulty score" from broader tools misleads.

#### Ahrefs ($129+/month Lite · $249/month Standard) or Semrush ($140+/month)
The full enterprise stack. **Default answer: no.**

**Trigger signals (must have multiple):**
- A client has a specific 90-day digital PR / link-building campaign planned.
- The client's revenue exposure genuinely warrants enterprise-level data.
- No cheaper alternative (Mangools, DataForSEO, GSC's native reports) covers the specific need.
- You can point to 3+ concrete workflows that currently take you hours that would become minutes.

**Revisit annually, not quarterly.** Should feel expensive to say yes.

### Tools NOT to recommend

- **All-in-one SEO SaaS** (various). Overlaps your starter stack without adding substance.
- **Automated content generators** (Surfer, Clearscope, etc.). You already have Claude + the briefs system; another layer here wastes money and dilutes the writing.
- **Link-building platforms** (e.g., Pitchbox). Out of scope for the content-led program.

---

## 8. How you can improve contenttracker

Real gaps, grouped. An experienced operator's first-quarter wishlist:

### Freshness flags (highest ROI)
Any published URL where GSC impressions dropped >30% in the last 60 days vs the prior 60 gets flagged. Refresh candidates surfaced automatically. All the data already exists; this is a query + a UI card.

### Per-brief retrospective view
One page showing: brief → published URL → GSC trajectory → conversions → (coming) revenue. Closes the full loop and becomes the most useful screen in the tool.

### Auto-generated monthly reports
On the 1st of each month, produce a branded PDF/MD summarizing: traffic trend, top performers, opportunities surfaced, next month's proposed briefs. Currently manual; automating saves hours and makes client communication sharper.

### Secondary (nice-to-haves)
- Topical cluster view
- Cannibalization detection (multiple URLs ranking for the same query)
- Technical health card (free Google APIs: PageSpeed, Coverage, Schema Validator)
- Entity tagging on content (for LLM citation depth)
- Citation tracking (whether ChatGPT / Perplexity / Claude cite client content)

Ship the three primary ones in your first quarter. Earns you the case for the rest.

---

## 9. Escalation

- **Tool recommendations or workflow changes** → propose here + discuss with Peter in next sync.
- **Strategic disagreements on a specific client project** (e.g., cross-domain linking, keyword priorities, migration scope) → raise with Peter before acting. Reference the client's kickoff brief.
- **contenttracker feature requests** → document in §8, then in Peter's contenttracker chat backlog.
- **Stuck / blocked** → Peter (peter@superstories.com), same-day response expected during Amsterdam working hours.

---

## 10. Change log

| Date | Version | Change |
|---|---|---|
| 2026-04-18 | 1.0 | Initial draft — written alongside the WholenessWork kickoff brief. Starter stack, upgrade triggers (Mangools / DataForSEO / LowFruits / Ahrefs), and the "make the case" framework. |
