# GHL Attribution Setup — Team Brief

**Version:** 1.0 · Last updated 2026-04-18
**For:** GoHighLevel administrators on client accounts managed with SuperStories
**Purpose:** One-time setup + ongoing hygiene so content-to-revenue attribution works
**Status:** Living document — expect updates as we learn what breaks in the wild

---

## Why this matters (30 seconds)

When someone reads a blog post, clicks through to a training registration, and buys — we want to know *which article* earned that sale. Not "organic search drove £X" but "this specific post → this lead → this £2,400 sale."

Today that data doesn't connect. Blog traffic lives in Google Analytics; sales live in GHL; there's no join between them. This brief fixes the GHL side.

The full pipeline has three parts:

1. **Website (Webflow)** — outbound links auto-tagged with UTM parameters by a JavaScript snippet. *(Someone else sets this up.)*
2. **GHL (you)** — captures those UTM tags on the contact record when they submit a form. **← this brief.**
3. **Content Tracker** — joins GHL revenue to the content piece that earned it, via the `utm_campaign` field.

Your job is part 2. Without it, parts 1 and 3 are useless.

---

## Quick reference

Four custom fields to create on the **Contact** object in GHL, all type **Text**:

```
utm_source
utm_medium
utm_campaign
utm_content
```

Field names must match exactly — lowercase, underscore between words. The Content Tracker queries by these exact names.

Example tagged URL (what visitors click):

```
https://example.com/register?utm_source=website&utm_medium=content&utm_campaign=core-transformation-process
```

When a visitor with that URL fills out a form, the GHL contact record should have:

| Field | Value |
|---|---|
| `utm_source` | `website` |
| `utm_medium` | `content` |
| `utm_campaign` | `core-transformation-process` |

---

## One-time setup

### Step 1 — Create the four custom fields

1. Settings → Custom Fields → **Contact**
2. Click **Add Field**
3. Create each as type **Text**:
   - [ ] `utm_source`
   - [ ] `utm_medium`
   - [ ] `utm_campaign`
   - [ ] `utm_content`
4. Save.

### Step 2 — Map UTM parameters on every form

For *every* form that creates or updates a contact — contact forms, funnel opt-ins, application forms, checkout pages, webinar registrations:

1. Open the form in GHL.
2. Under form settings → **URL Parameters** (sometimes called Query Parameters), add four mappings:
   - URL param `utm_source` → Contact field `utm_source`
   - URL param `utm_medium` → Contact field `utm_medium`
   - URL param `utm_campaign` → Contact field `utm_campaign`
   - URL param `utm_content` → Contact field `utm_content`
3. Save.

Repeat for every existing form. This is the tedious part — but it's once per form, forever.

### Step 3 — Do NOT use GHL's built-in "Attribution Source"

GHL has a native "Attribution Source" field. **We do not use it.** Reasons:
- Hard to query consistently via API.
- Overwrites silently, mixing first-touch and last-touch.
- Behaves differently across funnel versions.

Leave it alone. Rely only on the four custom fields above.

---

## How to verify setup is working

Run this test *after* Step 2 on each new form:

1. Open an incognito browser window.
2. Visit the form using a tagged URL — paste this in the address bar (swap the real form URL):

   ```
   https://{form-url}?utm_source=test&utm_medium=test&utm_campaign=test-article&utm_content=test-cta
   ```

3. Fill out the form and submit.
4. Open the new contact in GHL.
5. Scroll to custom fields. You should see all four fields populated with `test` / `test` / `test-article` / `test-cta`.
6. If any field is blank → the mapping on that form is wrong. Fix and re-test.
7. Delete the test contact when done.

**5 minutes of testing per form prevents weeks of missing data.**

---

## Ongoing workflow

### When you build a new form or funnel

Before going live:
- [ ] Add the four UTM parameter mappings (Step 2 above)
- [ ] Run the verify test (above)
- [ ] Only then publish

### When you edit or duplicate an existing form

- Duplicating a form in GHL sometimes does NOT carry over URL parameter mappings. **Always re-check after duplicating.**
- Don't delete UTM mappings. They're invisible to visitors — only contact records see them.

### When you notice contacts without UTM values

If a chunk of new contacts suddenly has blank UTM fields, something broke. Common causes:
- A new form was built without UTM mappings.
- A form was duplicated and the mappings were lost.
- A link was shared somewhere without UTM tags (check where traffic is coming from).
- The Webflow snippet broke and stopped tagging outbound links.

Flag to SuperStories immediately (peter@superstories.com). Blank attribution is useless; partial attribution is misleading.

### Monthly check (5 minutes)

Once a month, sanity-check:
- [ ] Pull a report of contacts created in the last 30 days.
- [ ] Spot-check 5 random contacts for UTM values.
- [ ] If >10% of contacts have blank UTMs → investigate.

---

## What NOT to do

- **Don't rename the custom fields.** The Content Tracker queries by exact name — renaming breaks attribution silently.
- **Don't add extra UTM fields** like `utm_term` unless SuperStories asks. Four fields is the convention.
- **Don't manually edit UTM values** on contact records. The URL is the source of truth.
- **Don't skip the verify test** after adding mappings to a new form.
- **Don't rely on GHL's "Attribution Source"** as a substitute. It isn't one.

---

## Getting help

Anything that doesn't fit the pattern above — message Peter (peter@superstories.com) before improvising. Most edge cases have already come up; there's usually an answer.

For non-urgent questions, log them and batch into the monthly sync.

---

## Change log

| Date | Version | Change |
|---|---|---|
| 2026-04-18 | 1.0 | Initial brief |
