# SEO Operator — Role Spec

**Purpose:** source-of-truth definition of what SuperStories wants and needs from the remote SEO specialist role. Feeds the OnlineJobs.ph job ad and the test-assignment design.
**Audience:** Peter van Rhoon (primary) · candidates under evaluation (secondary, selectively shared) · the hired operator once onboarded.
**Status:** Living document · v1.0 · 2026-04-18.
**Companion doc:** `seo-operator-guide.md` (working guide for the hired operator).

---

## The role in one sentence

A remote **SEO + Analytics + Attribution operator** who owns the content-performance loop across all SuperStories clients — weekly GSC/GA4 review, keyword targeting, brief creation in contenttracker, UTM + GHL attribution hygiene, monthly client reporting — and who brings conceptual SEO thinking, not checklist execution.

---

## 1. Who SuperStories is + who we serve

- Small Amsterdam-based content + SEO practice run by Peter van Rhoon.
- Clients are small: individual experts, coaches, training practices, small B2B companies. Typical monthly revenue per client in the low thousands, not tens of thousands. **Enterprise playbooks do not apply.**
- Active clients as of 2026-04-18: **ANLP** (Connirae Andreas / owner-managed GHL), **Denim City (DC)** (SuperStories-managed GHL), **WholenessWork** (new build coming online). Expect 1–3 new clients/year.
- Stack across clients: **Webflow + GoHighLevel (GHL) + GA4 + GSC + contenttracker** (SuperStories' internal tool).
- Peter is non-technical. Explains things in plain language and expects the same back.

---

## 2. Why this role exists

Peter is not an SEO expert and does not want to become one. The clients are too small to afford a traditional agency, and too serious to survive on freelance gig-work. The role exists to bring **conceptual SEO ownership** — someone who understands how content becomes traffic becomes leads becomes revenue, and can operate that loop across multiple small clients simultaneously using SuperStories' internal pipeline (contenttracker + the attribution stack).

This is **not** an execution-only role. It's not "run these 50 tasks I hand you each week." It's "own the content engine across our book of clients, flag problems, propose improvements, run the rhythm yourself."

---

## 3. What the operator owns

### Per-client, weekly
- Review GSC dashboard: impressions, positions, anomalies, Zone 3 quick-win opportunities.
- Review GA4: conversions per page, conversion value (when GHL Phase 1 lands, revenue per page).
- Create 1–2 content briefs in contenttracker (one Zone 3 push, one Zone 2 expansion).
- Close last week's loop: mark published pieces as published; enter URLs in contenttracker.

### Per-client, monthly
- Take a GSC snapshot (historical record).
- Run contenttracker's AI strategy recommendations; validate and commit to next month's content plan.
- Audit keyword targets (retire won, promote climbing, remove stale).
- Export dashboards to Markdown + Excel (contenttracker supports both — **never export as CSV**, Peter's preference).
- Produce a client-facing monthly report from the exports.
- Review ad-spend vs organic; flag if paid per-acquisition isn't trending down.

### Per-client, quarterly
- ICP review — which audience actually converts? Rewrite the content plan if reality differs from assumptions.
- Content freshness audit — flag 6+ month-old pieces declining by >30%.
- Brief template iteration — encode what's working.

### Across the agency (ongoing)
- **UTM + GHL attribution hygiene** — make sure every client's setup follows the SuperStories UTM convention (3 params: source/medium/campaign, `utm_campaign = content slug`). Send the GHL briefing doc (`docs/ghl-attribution-setup-brief.md`) to each client's GHL admin. Run the verify procedure yourself on new forms.
- **GA4 installation on GHL funnels** — every new training funnel gets the client's GA4 measurement ID added inside GHL (not just inherited from Webflow). Known failure mode: ANLP's CTF Mar 2026 funnel launched without this; the whole funnel is invisible to GA4 today.
- **Client team briefings** — when a client's marketing or email staff is doing UTM tagging, brief them clearly. Assume they don't have context; don't assume they have it.
- **Monthly cross-domain check** for clients in multi-domain ecosystems (WholenessWork lives in a 5-domain ecosystem — cross-links follow a specific matrix, documented in the WW kickoff brief).
- **Content calendar** — maintain a rolling 60-day view of what's being published across clients; flag capacity issues to Peter.

### Product contribution to contenttracker
- Propose and spec improvements. Specifically: ship 1 of the top-3 improvements (freshness flags · per-brief retrospective · auto-generated monthly reports) within first 6 months. Details in the operator guide §8.
- Propose tool additions when the starter stack isn't enough (operator is empowered; see operator guide §7 for the "make the case" framework).

---

## 4. What the operator does NOT own

- **Writing content.** Briefs happen in contenttracker; drafts are produced via Claude Projects where each client's voice + brand is encoded. The operator creates briefs and may review drafts, but isn't the writer.
- **Technical SEO execution** (Core Web Vitals fixes, schema implementation, crawl error remediation). Flag these; the dev team handles them. Schema generation is already automated in contenttracker.
- **contenttracker development.** Peter owns the tool's code. The operator requests features + specs improvements; Peter builds.
- **Keyword discovery tooling decisions beyond the starter stack.** Peter approves new subscriptions after the operator makes the case (see operator guide §7).
- **Long-form competitive / backlink strategy.** Out of scope for content-led programs at this scale. Handled ad-hoc when relevant.

---

## 5. Required skills + traits

### Technical / tactical
- Hands-on proficiency with **Google Analytics 4** (property setup, event configuration, conversion setup, audience definition, reporting).
- Hands-on proficiency with **Google Search Console** (property verification, coverage/indexing review, performance analysis, sitemap submission).
- Deep understanding of **UTM parameters + attribution models** — can explain the difference between first-touch and last-touch and why it matters.
- Experience with a **CRM** — GoHighLevel ideal; HubSpot / ActiveCampaign / Close / Pipedrive acceptable.
- Comfortable with **basic JavaScript snippets** (reading + installing in Webflow / GTM — not writing from scratch).
- Fluent with **Google Tag Manager** OR willing to learn in first 30 days.

### Conceptual
- Understands **how SEO actually drives business outcomes** — not rankings for rankings' sake.
- Can think in **funnels and journeys**, not just keywords.
- Understands the difference between **search intent types** (informational / navigational / transactional / commercial) and why content has to match.
- Familiar with **LLM SEO / citation optimization** — the shift from ranking in Google to being cited by ChatGPT / Claude / Perplexity.

### Communication + working style
- Fluent written + spoken English. Writes clearly for non-technical audiences.
- Client-facing experience — has been on calls with business owners, not just project managers.
- Comfortable with **small-client scrappiness** — no enterprise tooling, budget constraints, building from scratch.
- Curious about AI-assisted content workflows; willing to use Claude Projects + contenttracker daily.
- **Ownership mindset.** Doesn't need daily direction. Shows up Monday and knows what to do.

---

## 6. Nice-to-have skills

- **Webflow** — multiple clients run on it.
- **GoHighLevel specifically** — reduces onboarding time significantly.
- Familiarity with **lean SEO tools** (Mangools, LowFruits, DataForSEO) — not the Ahrefs / Semrush enterprise stack.
- Basic **schema.org / structured data** literacy.
- Experience with **content migration** (301 redirect mapping, content pruning decisions) — WholenessWork involves migrating a 10-year-old site.
- Exposure to **multi-domain / multi-brand ecosystems** — WW operates inside a 5-domain Andreas-family ecosystem with strategic cross-linking requirements.

---

## 7. How we work together

- **Employment type:** full-time, 40 hrs/week, remote.
- **Platform:** hired via **OnlineJobs.ph** (Philippines-based talent pool assumed).
- **Timezone:** Philippines hours fine for most work; need ~3 hrs overlap with Amsterdam (CET/CEST) for weekly sync + occasional client calls.
- **Probation:** 3 months. Long-term role after.
- **Weekly 1:1** with Peter (30–45 min, Amsterdam afternoon = Manila evening).
- **Async-first** outside the sync.
- **Tools:** Slack / Notion / whatever Peter uses; clarify on day 1.

---

## 8. Compensation

- **USD $1,200 – $2,000 / month** full-time, depending on experience and skill coverage across the required buckets.
- Upper tier is for candidates with **GHL hands-on + GA4/GTM expert-level + fluent client-facing English + prior content-SEO ownership at a small agency**.
- Lower tier is for candidates strong in one or two buckets with demonstrated ability to grow into the others.
- Below $1,200/month will almost certainly yield execution-only people; not the hire we want.
- Paid monthly via [payment method — confirm: Wise / PayPal / Deel / OnlineJobs direct].
- **Paid leave + sick days** per OnlineJobs.ph norms.

---

## 9. What success looks like (by milestone)

| By end of... | What's true |
|---|---|
| **Week 2** | Onboarded into contenttracker. Has reviewed all current clients' data. Can articulate the UTM convention + why it matters. |
| **Month 1** | Running the weekly rhythm on at least one client independently. First monthly client report shipped. Has read and internalized all docs in `contenttracker/docs/`. |
| **Month 3** | Running weekly rhythm on all clients. Has proposed at least one contenttracker improvement (written spec). Has made or declined at least one tool upgrade recommendation with reasoning. |
| **Month 6** | One of the top-3 contenttracker improvements shipped (freshness flags · per-brief retrospective · auto monthly reports). At least one client's content→revenue attribution (via GHL Phase 1/2) demonstrably working. |
| **Month 12** | Clear pattern match across clients on what works. Peter trusts operator to lead intake calls with new clients. Has grown into an ownership role for the content-engine function across SuperStories. |

---

## 10. Who NOT to hire (red flags)

- **Execution-only checklist SEO.** Runs through audits, doesn't know why the boxes exist.
- **Enterprise-only mindset.** Thinks nothing can be done without Ahrefs + Semrush + Clearscope + SurferSEO. Overspends reflexively.
- **Writing-focused.** Sees themselves as the content writer. We don't need that; Claude Projects does writing.
- **Backlink-heavy specialist.** Link building isn't our game at this scale.
- **Ego that can't take direction from a non-technical founder.** Peter sets product and strategy; the operator owns execution within that frame.
- **Over-promising on first call.** Good operators ask questions on the test assignment; bad ones tell you everything is easy.
- **Vague on GA4.** Anyone who says "SEO isn't about GA4" doesn't understand the modern funnel.
- **Can't articulate *why* behind their recommendations.** Every suggestion needs a reasoning chain, not "best practice says so."

---

## 11. Hiring process

1. **Job ad** posted on OnlineJobs.ph (written separately in Claude Cowork, PRD lives in this repo).
2. **Screening questions** in the ad:
   - Describe a time you set up GA4 + attribution for a small business from scratch. What did you do first? What went wrong?
   - If a client's UTM tagging is a mess, what's your step-by-step approach to fix it without breaking historical data?
   - What's one SEO belief you hold that most SEO people get wrong? Why?
3. **Loom video** — 60 seconds introducing themselves. Tests spoken English fluency + filters low-effort applicants.
4. **Test assignments** — 2–3 paid short tasks (~2 hours each) sent to the 2–3 shortlisted candidates. Designed to simultaneously test (a) conceptual thinking, (b) hands-on GA4/GHL literacy, (c) written clarity. Test assignments documented separately when ready to send.
5. **Final interview** (30–45 min) with Peter.
6. **Trial month** — paid first month works as mutual evaluation.

---

## 12. Where this role sits long-term

Within 12 months, this person is SuperStories' **head of content operations** in everything but title. They own the delivery machine across clients; Peter owns product (contenttracker), sales, and strategy. If the role works, it may grow into hiring a second operator (e.g., for content writing in specific language niches) or scale sideways into other agency functions.

If the role doesn't work, we catch it in the first 3 months via the probation period + the milestone table in §9.

---

## 13. Change log

| Date | Version | Change |
|---|---|---|
| 2026-04-18 | 1.0 | Initial spec — replaces the earlier PRD drafted during the contenttracker / WholenessWork session. Incorporates: small-client scale reality, WholenessWork as primary incoming project, 5-domain ecosystem, GHL integration trajectory, tool budget + upgrade philosophy, milestones, red flags. |
