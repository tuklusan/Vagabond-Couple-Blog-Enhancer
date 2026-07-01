# The Vagabond Couple — Google "Crawled But Not Indexed" Fix Workflow — rev-18

**Platform:** Blogger.com (blogspot.com)  
**Applies to:** All overland travel blog posts on thevagabondcouple.blogspot.com  
**Problem:** Google crawls the post but does not index it (Search Console status: "Crawled — currently not indexed")  
**Root cause:** Focus dilution, weak first-screen topical clarity, duplicate URL signal noise (`?m=1`), missing structured route data, and missing author/entity signal in schema

---

## Global Operating Rules

These four rules govern all communication, sequencing, and output quality throughout every phase. They override any default toward verbosity, single-pass confidence, or skipping ahead.

### Rule G1 — Minimum Verbosity

All chat output is kept to the minimum required for the operator to understand status and make decisions. Specifically:

- **Progress indicator only during execution.** While working through phases and steps, the only unprompted output is a single-line phase+step indicator in the format: `▶ Phase 1 / Pass 1A — Fact Check` or `▶ Phase 3 / Step 6 — First Body Paragraph`. No commentary, no narration of what is being done, no interim findings unless a halt condition is triggered.
- **Halt conditions are reported immediately, concisely, and actionably (amended rev-18).** If a hard stop is encountered (missing document, unresolvable fact error, encoding corruption), output: `⛔ HALT — [one-line reason] — Offending item: [specific string / URL / value]. Action required: [one-line instruction].` Naming the specific offending item is mandatory — a halt that only states the category of problem without pointing to the exact text, link, or value forces the operator to go hunting for it, which defeats the purpose of halting immediately. Example: `⛔ HALT — Fact error in 1A — Offending item: "Wuqia elevation 3000m" (actual ~2,900m per reference sources). Action required: correct elevation in the rewritten text.` Nothing else until the operator responds.
- **Phase 4 approval gate is the only full summary.** The complete modification summary (Phase 4 template) is the single comprehensive output before HTML generation. It is presented once, in full, exactly as the template specifies.
- **Deliverables (Phase 6) are presented without preamble.** Output the three deliverables, labelled, with no surrounding explanation unless the operator asks a question.
- **No volunteered status updates between steps.** Do not narrate transitions ("Now I will move on to Step 7…"). Move silently to the next step and update the indicator.
- **Answer operator questions directly and briefly.** If the operator asks a question mid-process, answer it in the fewest words that are complete and accurate, then resume with the current phase+step indicator.

### Rule G2 — Consecutive Verification Passes Before Delivery

Before presenting the Phase 6 deliverables, the Phase 5 sanity checklist must be verified twice, using two different verification methods. Delivery is only permitted after both passes are confirmed clear with zero gaps.

**rev-16 hardening:** Two passes that repeat the same method catch regressions but do not reliably catch errors the first pass was structurally blind to — confirmation bias survives simple repetition if the second pass re-reads the same output with the same expectations formed while drafting it. The procedure below requires the two passes to differ in method, not just in iteration count.

**Procedure:**

1. **Pass 1 — checklist-driven.** Complete the first full pass of the Phase 5 HTML Sanity Checklist, item by item, in checklist order. Record every item result against the actual generated HTML — not against memory of what was intended. If any item fails: fix the issue, then restart the checklist from the beginning. A partial re-check after a fix does not count as a pass.
2. **Pass 2 — adversarial, source-driven, not checklist-driven.** Once Pass 1 is clean, run a second pass that does **not** walk the checklist top-to-bottom from memory of Pass 1. Instead, work backward from each independent source of truth and verify the output matches it, treating the output as guilty until proven compliant:
   - Re-open the Phase 1C inventory and verify the output against it line by line (not "does it look complete" — count and match every entry).
   - Re-open the Phase 1G `?`-audit table and confirm every flagged item's resolution is actually present in the output text, not just recorded as resolved in the audit.
   - Re-open the Phase 1H/1I findings lists and confirm each flagged item's resolution is visible in the output, not assumed from the Step 12 log.
   - Re-apply `english-writing-rules_v2.txt` fresh at this point (from the session-loaded context per rev-18, not from memory of the Pass 1 read — re-read the file itself only if it has changed mid-session) and scan the full output fresh against it.
   - Independently recompute the ETR from the actual final word count rather than trusting the Step 2-F figure.
3. **A gap found during Pass 2 invalidates Pass 1 even if Pass 1 reported clean.** This is expected and not a sign of wasted work — it is the mechanism working. Fix the issue, then restart the full two-pass sequence (Pass 1 *and* Pass 2) from the beginning. The counter resets to zero on any failure at either pass.
4. **If both passes are clean: delivery is permitted.** Proceed to Phase 6.
5. **Do not skip Pass 2's source re-derivation as a shortcut.** Re-confirming "the checklist says it's fine" a second time is not Pass 2; re-deriving the answer from the original source artifacts and comparing is Pass 2. If time pressure tempts a shortcut, that is itself the signal that Pass 2 is most needed.

**Indicator format during verification:**
- `▶ Phase 5 / Verification Pass 1 (checklist) — in progress`
- `▶ Phase 5 / Verification Pass 1 (checklist) — CLEAN. Starting Pass 2 (source re-derivation).`
- `▶ Phase 5 / Verification Pass 2 (source re-derivation) — CLEAN. Two independent-method clean passes confirmed. Proceeding to Phase 6.`
- `▶ Phase 5 / Verification Pass 1 — GAP FOUND: [one-line description]. Fixing. Restarting two-pass sequence.`
- `▶ Phase 5 / Verification Pass 2 — GAP FOUND: [one-line description] (missed at Pass 1). Fixing. Restarting two-pass sequence.`

**Rationale:** A single checklist pass is subject to confirmation bias — the tendency to read what was intended rather than what is actually in the output. Running the same checklist twice in the same way only partially breaks this, since the second read is still anchored to the first read's framing. Requiring the second pass to re-derive from source artifacts rather than re-confirm the checklist closes that gap — it is the difference that has, in practice, caught issues a same-method second pass would not.

### Rule G3 — Exact `href` Preservation

All existing `href` attribute values must be preserved byte-for-byte unless one of the workflow's explicit correction rules requires changing that exact link.

**Default rule:** every original `href="..."` value is copied into the output exactly as found — same URL, same query string, same fragment, same protocol form, same trailing slash, same escaping, and same capitalization.

**Allowed exceptions only:**
- Removing `?m=1` from internal `thevagabondcouple.blogspot.com` links when the workflow explicitly requires canonical internal URLs.
- Correcting an objectively broken link only after it is flagged in Phase 1C and approved in the Phase 4 summary.
- Adding new links during approved content work or Phase 7B cross-linking.

**Forbidden changes:**
- Do not normalize `http` to `https`.
- Do not remove or reorder query parameters.
- Do not remove URL fragments.
- Do not decode or re-encode URL entities.
- Do not shorten URLs.
- Do not replace a source URL with a guessed canonical URL.
- Do not alter external affiliate, map, social, YouTube, Blogger image, or Googleusercontent links.

**Verification requirement:** Phase 1C must inventory every original `href` value and Phase 5 must compare the output against that inventory. Any unapproved `href` difference is a blocking error.

---

### Rule G4 — Hard Step-Entry Gate (rev-17)

**No step or pass may begin until the immediately prior step or pass in the canonical sequence has been confirmed complete.** This is a mechanical gate, run silently as part of the phase+step indicator transition — it is not a narrated checklist and does not add chat output beyond what Rule G1 already permits.

**Canonical sequence this gate enforces (in order):**
`1A → 1B → 1C → 1D → 1E → 1F → 1G → 1H → 1I → Phase 2 → Step 1 → Step 2 → Step 3 → Step 4 → Step 5 → Step 6 → Step 7 → Step 8 → Step 9 → Step 9-F → Step 10 → Step 11 → Step 12 → Step 13 → Step 2-F → Step 14A → Step 14B → Phase 4 → Phase 5 Pass 1 → Phase 5 Pass 2 → Phase 6 → Phase 7A → Phase 7B → Phase 7C` (rev-18: Step 14 split into 14A → 14B)

Phase 8 is excluded from this chain — it is operator-invoked separately and is not a link in the per-post sequence.

**Start of chain:** 1A's "prior step" is the Pre-check itself (Required Project Documents confirmed present, `english-writing-rules_v2.txt` and the reference pre-fold file read in full). 1A may not begin until that pre-check is explicitly confirmed — this is the same hard stop the document already requires, restated here as the first link in the gate.

**What "confirmed complete" means, concretely, for the step about to be entered:**
- The prior step's own stated **Output** (where the step defines one — e.g. 1A's flagged-facts list, 1H's repetition list, Step 12's resolution log) actually exists and is non-empty or explicitly marked NONE FOUND/NONE REQUIRED.
- Any **Halt condition** the prior step defines was either not triggered, or was triggered and has since been resolved — never silently passed over.
- Any **Writing Rules compliance gate** the prior step defines (Steps 6, 7, 8, 9-F, 10, 13, 2-F) was actually run, not assumed.
- For steps with sub-numbered procedures (e.g. Step 9's zero-H2 procedure, Rule G2's Pass 1/Pass 2 sequence), every sub-item completed — not just the step's final line.

**Procedure at the start of every step:**
1. Before emitting the new phase+step indicator, silently check the immediately prior step in the canonical sequence against the criteria above.
2. **If confirmed complete:** proceed normally — emit the indicator for the new step and begin it. No extra chat output; this is silent per Rule G1.
3. **If not confirmed — output not found, a halt was left unresolved, or a compliance gate was skipped:** do not enter the new step. Halt instead, using Rule G1's amended halt format: `⛔ HALT — Step [N] entry blocked: prior step [N-1] incomplete — Offending item: [the specific missing output, unresolved ⚠️/❌ item, or skipped gate, named exactly]. Action required: complete [N-1] before proceeding.` Example: `⛔ HALT — Step 12 entry blocked: prior step 1I incomplete — Offending item: 🟠 voice-exception candidate "Naturally, the visa office was closed" (Section: Border Crossing) has no logged operator decision. Action required: resolve at Phase 4 or fix per Step 12 default.`
4. **Never backfill silently.** If a gap is found, it must be closed by actually executing the missed step's substance — re-running the scan, resolving the halt, running the compliance check — not by retroactively writing "PASS" into a summary without having done the underlying work.
5. **This gate also applies across a session break.** If the operator resumes a post mid-workflow (new message, after a pause, after answering a question), re-confirm the most recently completed step before resuming forward — do not assume context was retained correctly just because the conversation continued.

**Special cases in the sequence:**
- **Phase 2 (URL Stub Lock)** has no per-step Output artifact of its own; "confirmed complete" means the stub was explicitly checked and confirmed unchanged before Step 1 begins.
- **Step 9-F** cannot be entered until Step 9's heading cleanup *and* its summary-block re-sync are both done — Step 9-F depends on the final H2 structure, so entering it against a not-yet-finalized heading set is itself a gate failure, not just a sequencing nicety.
- **Step 2-F** cannot be entered until Step 13 (the last body-content step) is complete, since its word count depends on every prior step's additions.
- **Phase 5 Pass 2** cannot be entered until Phase 5 Pass 1 is fully clean — this duplicates Rule G2's own restart logic and is not a separate failure mode, but G4 is the reason Pass 2 can never be started speculatively "in parallel" with finishing Pass 1.
- **Phase 4** cannot be entered until Step 14's **14A (Mechanical Cohesion)** has explicitly returned PASS *and* **14B (Holistic Read-Through)** has explicitly returned PASS (or either sub-phase returned issues that were then fixed and re-verified) — a read-through that surfaced problems still left unresolved is not a completed Step 14. The two sub-phases are sequential: 14A is a pre-requisite for 14B, and Phase 4 depends on both.

**Rationale:** The workflow's value depends on every pass and step actually running in full, in order — a skipped pass doesn't announce itself, it just leaves a gap that later phases have no mechanism to notice unless something explicitly checks for the gap's absence. G4 makes "did the prior step actually happen" a condition of starting the next one, rather than an assumption.

---

## Required Project Documents — Hard Stop

Verify all six documents are present in project knowledge **before starting any post**. If any is missing, stop and add it. Do not guess at templates, class names, CSS variables, or writing rules.

| Document | Purpose | Hard stop if missing? |
|---|---|---|
| Blogger theme XML (`vg-blog-theme-live-*.xml`) | CSS variables, image table classes, iframe rules, dark mode | **YES** |
| `TRAVELACTION-ld_json-SCHEMA-EXAMPLE.txt` | Schema field names and structure | **YES** |
| `YOUTUBE-VIDEO-EMBED-FOR-BLOGGER.txt` | Authoritative YouTube embed template | **YES** |
| `english-writing-rules_v2.txt` | Forbidden words, forbidden phrases, narrator rules, register constraints — governs the entire post body, original prose and newly written text alike (rev-15) | **YES** |
| `TVC-reference-prefold-turkmenistan-part1.html` | Canonical correct pre-fold zone: hero image, intro paragraphs, summary block CSS, ld+json schema, `<!--more-->` — ground truth for Step 3 and Phase 1F | **YES** |
| This workflow document | Processing rules | **YES** |

**rev-14 note:** `TRAVELACTION-ld_json-SCHEMA-EXAMPLE.txt` and the embedded schema inside `TVC-reference-prefold-turkmenistan-part1.html` both predate the Step 4 `author` field requirement and do not yet show it. Apply the `author` field per Step 4 regardless of what either example file shows; update both files the next time either is edited so they stay in sync.

**rev-15 note:** English Writing Rules no longer apply only to newly written text. There is no longer a separate exemption for original author prose. The entire post body — unmodified source prose and freshly drafted text alike — must comply with `english-writing-rules_v2.txt` (forbidden words, forbidden phrases, structural tics, narrator rules, repetition). The only standing exemption is *voice and tone*: the author's sentence-level style and sense of humor are preserved, not normalized into a uniform house style. New Phase 1I (Writing Rules Audit — Existing Prose) and the broadened Step 12 implement this. See Step 12 for the voice-exception override procedure when a flagged word/phrase/tic is doing genuine comedic or stylistic work.

**Before reading any text in Phase 1 or writing any new text in Phase 3:** read `english-writing-rules_v2.txt` in full. Do not apply the rules from memory — load the file and apply it actively. This applies equally to auditing existing prose (Phase 1I) and to drafting new text (Phase 3 Steps 6, 7, 8, 10, 13, 2-F).

**rev-18 note — session-scoped loading:** `english-writing-rules_v2.txt` is read in full **once per session**, at the first post processed in that session, and stays active in context for every subsequent post processed in the same session — it is not re-read from the project file for each new post. This is a token-efficiency change only: it removes the redundant re-read of an unchanged file, not the rule itself. Every post still undergoes the full Phase 1I audit and every Phase 3 writing-rules compliance gate, checked against the rules as loaded — full-body coverage (rev-15) is unaffected. If the operator indicates `english-writing-rules_v2.txt` has been updated mid-session, or a new session begins, re-read the file in full before continuing — do not carry forward a stale load across an actual file change.

**For Step 3 (summary block) and Phase 1F (summary block audit):** read `TVC-reference-prefold-turkmenistan-part1.html` and compare the source post's summary block against it. The reference file is the ground truth for correct CSS, correct header row structure, correct data row format, and correct single-column descriptor layout. If the source post's summary block deviates from the reference in any CSS property, strip and reapply the canonical template.

**rev-18 note — session-scoped loading applies here too:** `TVC-reference-prefold-turkmenistan-part1.html` is likewise read once per session and reused as the structural ground truth for every post in that session, not re-read per post. Re-read it if it changes mid-session or a new session begins.

---

## Why Google Skips These Posts

1. **Focus dilution** — The URL slug, title, and body each cover many micro-topics. Google cannot identify a single clean query target.
2. **Weak topical entry** — The first 100–150 words of the clickthrough body establish voice and atmosphere before naming the route.
3. **Duplicate URL split** — `?m=1` mobile variants split page signals with the clean canonical URL.
4. **Missing structured route data** — Without a valid `TravelAction` schema, Google has no machine-readable signal for route, locations, or themed content.
5. **Missing author/entity signal (rev-14)** — Without an `author` field in the schema, Google has no consistent entity to associate with the post during quality and trust evaluation.

---

## Canonical Document Structure

Every processed post must follow this exact structure. Memorize it — all phase rules derive from it.

```
[Hero image — tr-caption-container table]
[1–2 intro/context paragraphs — link from prior part, set scene]
[Summary block — brand-styled, pre-fold, series standard]
[TravelAction ld+json schema — <script> block]
<!--more-->
[Map embed — if present; otherwise omit]
[First body paragraph — route-first rewrite, Google's topical entry point]
[tvc-route-summary box]
[Route at a Glance — H2 + <ol>]
[Post body sections — H2/H3/H4 headings, images, paragraphs, embeds]
[Journey significance paragraph]
[Next Stop outro]
```

---

## PHASE 1 — Scan and Analyze

Run all eight passes on the **original source post** before changing anything. Document all findings. Nothing is edited during Phase 1.

---

### 1A — Travel Guide Fact & Sanity Check

Verify every factual claim against reliable reference sources. Repeated at Phase 5 to confirm no errors were introduced during rewrite.

**Check:**
- Named places exist and are correctly described (geography, elevation, character, spelling)
- Historical and religious claims are accurate and dated correctly
- Distances, durations, and elevations are plausible and internally consistent
- Named entities — businesses, roads, attractions, vehicles, people — are real and correctly spelled
- Route geography is coherent: stops appear in correct geographic and narrative sequence
- Practical travel details are accurate (crossing logistics, service availability, permit requirements)

**Output:** Flagged-facts list. Mark each: ✅ confirmed / ⚠️ acceptable rounding / ❌ error requiring correction.

**Halt condition:** Correct all ❌ errors before proceeding. Do not publish misinformation.

---

### 1B — Human Readability Pass

Read as a first-time visitor who has not read any earlier posts in the series.

**Check the original source for:**
- Assumed context: Are key characters and vehicles introduced on first mention? (Shehzadi = 2024 Toyota Tundra; Chetak = Toyota Hilux Invincible-X of Odyssean Journey — confirm each is clear at first use in the body)
- Pronoun or reference confusion when multiple vehicles or travelers appear
- Jokes or cultural references that require prior-post knowledge — flag for inline gloss
- Paragraphs that run past their informational or comedic value
- Narrative gaps or abrupt transitions between stops
- Clarity of the existing summary block if present (label accuracy, narrative accuracy, table row accuracy)

**Output:** Short list of readability issues to fix during Phase 3. Do not alter voice, tone, or humor — structural and clarity fixes only. Note: Route at a Glance and the rewritten body paragraph do not exist yet; they will be reviewed for clarity at the Phase 4 approval gate before generation.

---

### 1C — Media, Links, and Embeds Inventory

**Zero-tolerance rule: Every item in this inventory must be present and functional in the output HTML.** Build this inventory before any editing. It becomes the Phase 5 verification checklist.

**Blogger image-caption tables:** All photographs use Blogger's native image-caption table structure. The theme CSS targets these classes for layout and dark mode. This structure must be preserved exactly — never convert to `<figure>/<figcaption>` or any other format.

Correct preserved structure:
```html
<table align="center" cellpadding="0" cellspacing="0" class="tr-caption-container">
  <tbody>
    <tr>
      <td><a href="[FULL-RES-URL]"><img alt="[Description]" height="480"
          src="[THUMB-URL]" title="[Tooltip]" width="640" /></a></td>
    </tr>
    <tr>
      <td class="tr-caption">[Caption text]</td>
    </tr>
  </tbody>
</table>
```

Note: `title=` on `<img>` is a tooltip attribute, not CSS — keep it if present. `alt=` must be present and descriptive on every image.

**Inventory checklist:**

- [ ] **Photograph images:** count [N], list each `src` URL and `alt` text  
  Each photograph must be in a `tr-caption-container` table. YouTube embeds use a `<p class="tr-caption">` caption — these are not counted here.
- [ ] **`tr-caption-container` tables:** count [N] — must equal photograph count
- [ ] **Consecutive image pairs:** scan the full body for any two `tr-caption-container` tables that are adjacent with no intervening `<p>` element between them (whitespace-only text nodes and `.separator` divs do not count as separators). List each pair by position: image N followed immediately by image N+1. These are flagged for Step 13 separator insertion. Mark NONE if all images are already separated.
- [ ] **Internal links** (`thevagabondcouple.blogspot.com`): count [N], list each exact `href` value byte-for-byte — verify no `?m=1` unless it is being explicitly corrected under Rule G3
- [ ] **External links:** count [N], list each exact `href` value byte-for-byte — verify original `rel=` and `target=` attributes; no URL normalization, query-string change, fragment removal, or entity re-encoding
- [ ] **YouTube embeds:** count [N], list each video ID and caption context
- [ ] **Google Maps / OpenStreetMap / other map iframes:** count [N], list each `src` URL
- [ ] **Other iframes or embeds:** count [N], describe each
- [ ] **`<!--more-->` tag:** present (Y/N); if present, record current line position
- [ ] **Summary block:** present (Y/N); record structure (see 1F)

**Phase 5 check:** Every item above must appear in the output. Any discrepancy blocks delivery.

---

### 1D — Inline CSS Audit and Theme Compatibility

The post body HTML is injected into the Blogger theme template — it has no `<head>` of its own. All styling must come from the theme's CSS classes and custom properties, or from structurally neutral HTML attributes.

**Theme CSS variables confirmed from theme XML:**

| Variable | Light value | Use for |
|---|---|---|
| `--text` | `#343434` | Body text |
| `--heading` | `#303030` | Headings |
| `--accent` | `#DAB264` | Accent borders, highlights |
| `--link` | `#3367D6` (dark: `#DAB264`) | Links |
| `--surface-soft` | `#f7f7f7` | Subtle backgrounds |
| `--line` | `#e8e8e8` | Borders |
| `--text-soft` | `#777` | Captions, secondary text |

**Strip from post body — all inline `style=` attributes matching these patterns:**

| Pattern | Action |
|---|---|
| `style="margin-left: auto; margin-right: auto;"` on `<table>` | Remove — theme handles `.tr-caption-container` centering |
| `style="text-align: center;"` on `<td>` | Remove — theme handles via `.tr-caption` |
| `style="margin-left: auto; margin-right: auto;"` on `<a>` wrapping images | Remove |
| `style="text-align: left;"` on `<p>` | Remove — theme default |
| `style="clear: both; text-align: center;"` on `.separator` div | Remove |
| `style="color: #0000ee; ..."` or any hardcoded color on body elements | Remove — breaks dark mode |
| `style="text-align: left;"` on any heading tag | Remove — redundant |
| Any `style=` on `<a>` tags wrapping images inside heading tags | Remove (and move the image out of the heading — see Phase 3 Step 5) |

**Keep — structural HTML attributes, not CSS:**
- `height=` and `width=` on `<img>` — dimension hints for layout reservation
- `title=` on `<img>` — tooltip attribute, not CSS
- `border="0"` on `<img>` — harmless legacy
- `data-original-height` / `data-original-width` — Blogger lightbox hooks
- `align="center"` on `<table>` — legacy HTML attribute (not CSS), keep for Blogger compatibility
- `cellpadding="0" cellspacing="0"` — keep for Blogger compatibility
- All `class=` attributes — theme hooks, keep all

**Exemptions from the strip rule — inline styles that must be reapplied to canonical form:**

1. **The summary block** — uses hardcoded colors (`#fdf8f2`, `saddlebrown`, `rgb(139, 69, 19)`). This is the established series brand pattern and is exempt from the general strip rule. **However, do not blindly preserve whatever inline CSS the source post happens to have.** Source posts may have divergent styling (different font sizes, missing `border-radius`, missing `font-family`, or a dark header-row background that makes header text unreadable). Instead: **strip all existing inline CSS from the entire summary block and reapply the canonical template CSS exactly as specified in Step 3.** The theme's dark mode override (`html[data-theme="dark"] [style*="background"]`, `[style*="color"]`) provides partial mitigation for the outer container, but the header row must use `color: saddlebrown` on `<td>` elements — never a dark `background` on the `<tr>` — to remain readable in both light and dark modes. Do not convert the block to `tvc-route-summary`.

2. **YouTube embed wrapper divs** — the project template (`YOUTUBE-VIDEO-EMBED-FOR-BLOGGER.txt`) uses structural inline styles (`position: relative`, `padding-bottom: 56.25%`, etc.) that are required for responsive layout. These are exempt. Do not strip them.

**New CSS for newly added elements:** Use the `tvc-route-summary` class with no inline color styles. Add this rule **once** to the Blogger theme stylesheet (Theme → Edit HTML → before `</b:skin>`). On subsequent posts, verify the class already exists before adding it again:
```css
.tvc-route-summary {
  border-left: 4px solid var(--accent);
  background: var(--surface-soft);
  color: var(--text);
  padding: 12px 16px;
  margin: 1.5em 0;
  font-size: 0.95em;
  line-height: 1.7;
}
```
If theme stylesheet editing is not possible: use `<blockquote>` with no inline styles.

**Forbidden in any new elements:** hardcoded hex colors, named colors, `style="background:..."`, `style="color:..."`, `style="border: ... #hex"`.

---

### 1E — YouTube Embed Template Confirmation

Read `YOUTUBE-VIDEO-EMBED-FOR-BLOGGER.txt` from project files. Do not use a cached version or derive the format from memory or theme CSS.

The authoritative template as of last project file update:
```html
<div style="max-width: 760px; margin: 1.5em auto;">
  <div style="position: relative; padding-bottom: 56.25%; height: 0; overflow: hidden;">
    <iframe
      allow="accelerometer; autoplay; clipboard-write; encrypted-media; gyroscope; picture-in-picture; web-share"
      allowfullscreen
      frameborder="0"
      src="https://www.youtube.com/embed/[VIDEO_ID]"
      style="position: absolute; top: 0; left: 0; width: 100%; height: 100%;"
      title="[VIDEO TITLE]">
    </iframe>
  </div>
  <p class="tr-caption" style="text-align: center;">[CAPTION TEXT]</p>
</div>
```

Substitutions: `[VIDEO_ID]` = 11-character YouTube video ID; `[VIDEO TITLE]` = descriptive accessibility title; `[CAPTION TEXT]` = caption prose.

**All YouTube embeds in the output — both pre-existing and any new ones — must use this template format.** If a source post has YouTube embeds in a different format, re-emit them using this template, preserving the original video ID and caption text.

If the project file is updated, re-read it before processing the next post.

---

### 1F — Summary Block Audit

The series uses an established pre-fold summary pattern. **This block is a hard requirement in every post.** Audit the source post to determine whether it exists and whether it is accurate.

**The summary block has three parts in this exact sequence:**

1. **Label** — small-caps styled line identifying the post (e.g. "China Overland PART 5 Summary" or "[Post title] Summary")
2. **Narrative paragraph** — one paragraph in the author's voice describing the full route arc of this post: where it starts, where it ends, what is encountered along the way
3. **"What's Covered" table** — a two-column `<table>` (not a `<ul>`) with `▸` markers in the left cell and bold section name + brief descriptor phrase in the right cell. **One row per top-level H2 section (or per day/leg grouping) in the post body.** H3 and H4 sub-sections are not listed as separate rows.

**Expected position in document:** after the intro/context paragraphs, before the ld+json schema block, above `<!--more-->`.

**Distinction from Route at a Glance (Phase 3 Step 7):**
- Summary block "What's Covered" table: pre-fold, seen by index-page visitors, one row per major section, uses descriptor phrases written in the author's voice
- Route at a Glance `<ol>`: in the post body after `<!--more-->`, navigational aid for readers who clicked through, one item per named stop or location in travel order

They overlap in content but serve different audiences and must both be present.

**Audit checklist:**
- [ ] Summary block present in source post (Y/N)
- [ ] If present: label text matches this post's part number/destination
- [ ] If present: narrative paragraph accurately describes the full route arc
- [ ] If present: table rows match the actual top-level H2 sections in the post body — no phantom rows, no missing rows
- [ ] If present: block is positioned before the ld+json schema

**Do not preserve the source post's summary block CSS as-is.** Source posts may have divergent styling that causes visual defects (e.g. unreadable header text, missing border-radius, wrong font). Always strip and reapply the canonical CSS at Step 3 (see 1D and Step 3).

---

### 1G — Character Encoding Audit

Non-Latin scripts, diacritics, and special characters in source posts are a known failure mode. Blogger's HTML editor and external editing tools can silently replace non-ASCII characters with literal `?` marks when content is pasted from word processors or other editors. The corruption can exist in the source file before processing begins, so it cannot be caught by simply preserving source content.

**Run this scan on the source post before any editing. This pass covers the entire raw post body, including visible prose and attributes.**

1. **Every literal `?` character audit — mandatory**  
   Search the raw source for every literal `?` character, not only long runs. Each occurrence must be classified before editing.

   Classify every `?` as one of:
   - ✅ legitimate punctuation in an actual question or quoted question
   - ✅ intentional illegible-signage notation approved by context
   - ❌ corrupted non-ASCII placeholder
   - ⚠️ unknown / requires operator confirmation

   **Suspicion rule:** any `?` embedded inside a word, place name, road name, business name, caption, `alt=`, `title=`, schema string, transliteration, or signage string is suspect, even if it is a single character. Examples that must be investigated: `?ol`, `??? TN? ?134`, `????????`, `?????? ?????????`.

2. **Multi-`?` sequences**  
   Search the raw source for runs of two or more consecutive literal `?` characters (`??` or longer). These are strong signatures of corrupted non-ASCII text. Every occurrence must be investigated.

   - Determine what the sequence was meant to represent by reading surrounding Latin-script transliteration, caption context, route notes, or visible signage.
   - Count the `?` characters where relevant; each `?` often replaces one source-script character, but do not rely on count alone.
   - Reconstruct the correct text only when the evidence is strong.
   - If the source is unreadable signage and the operator intentionally used `?` to mark it as unreadable, record it as intentional. Otherwise treat it as a hard corruption candidate.

3. **Script-specific checks for this series** — Turkmen posts may contain:
   - Turkmen Cyrillic (pre-1993 script): sequences like `Жэхеннем`, `дервезеси`, `чүйги`
   - Turkmen Latin diacritics: ä, ö, ü, ý, ç, ň, ž — these survive encoding correctly in UTF-8 and are legitimate; no action needed
   - Road-name transliterations with Turkmen diacritics, e.g. `Ýol`, `Daşoguz`, `Aşgabat`, `Atamyrat Nyýazow Şaýoly`
   - Arabic-script Turkmen: rare, but possible in historical sections
   - Other Cyrillic or non-Latin scripts where route context requires them

4. **Unicode replacement characters (U+FFFD `�`)**  
   Search for `\ufffd` or the rendered glyph `�`. Any occurrence is a hard encoding error and must be corrected.

5. **Numeric HTML entities for non-ASCII** (`&#NNN;` where NNN > 127)**  
   Flag any found. They are not inherently wrong but may indicate the source was auto-escaped in a way that conceals the intended character.

6. **Propagation rule**  
   Once a corrupted string is identified and corrected, fix every duplicate occurrence across:
   - body prose
   - headings
   - image captions
   - `alt=` attributes
   - `title=` attributes
   - summary block narrative and table rows
   - Route Summary box
   - Route at a Glance
   - ld+json schema string values

7. **Do-not-guess rule**  
   If the intended character sequence cannot be reconstructed with high confidence from the source context, route notes, photo/signage evidence, or reliable references, do not invent a replacement. Mark it ⚠️ and halt for operator confirmation.

**Output:** A complete literal-`?` audit table with: location, surrounding text, classification, action, and replacement if applicable. If no suspicious `?` characters exist, state "NO SUSPECT QUESTION MARKS FOUND." Also list any U+FFFD or numeric-entity findings.

**Halt condition:** All ❌ corrupted placeholders must be corrected in the output HTML. All ⚠️ unknown cases require operator confirmation before delivery. Do not deliver a post with unresolved `?` placeholder text visible to readers or inside attributes/schema.

**Scope:** This check covers **all text in the post** — body paragraphs, headings, image captions, `alt=` text, `title=` attributes, summary block text, Route Summary box, Route at a Glance, and ld+json schema string values. The ld+json schema is particularly vulnerable because it is written afresh during Phase 3 and must encode any non-ASCII place names correctly.

---

### 1H — Repetition Scan

Read the entire post body — all paragraphs, headings, and image captions — and identify every instance where the same fact, concept, descriptive phrase, statistic, or idea appears more than once. This is distinct from 1B (readability): 1B catches narrative and structural problems; 1H catches content-level duplication that wastes word count, dilutes topical focus, and signals thin content to Google.

**What to flag:**

- The same factual claim stated twice (e.g. a Guinness record cited in an intro paragraph and again in the section body)
- The same descriptive phrase or sentence-level wording repeated near-verbatim in two different locations
- The same historical or geographical context given at both a heading level and inside the body paragraph beneath it
- The same sensory or atmospheric observation recycled across sections (e.g. "white marble gleaming in the sun" appearing in two separate location descriptions)
- Structural repetition: the same rhetorical move performed at the opening of multiple sections (e.g. every section starts with a sentence about arriving or approaching)

**What not to flag:**

- Intentional callbacks that create narrative cohesion (e.g. a motif that the author consciously returns to)
- Factual mentions required for context in different sections where a first-time reader landing mid-post would not have the prior paragraph
- The place name or attraction name itself — repeating the name is not duplication

**Output:** A numbered list of every repetition found. For each item: location (section heading or approximate paragraph), what is repeated, and where the earlier instance appears. Mark severity:
- 🔴 **Hard duplicate** — same fact or phrase in two places; one instance must be cut or rewritten
- 🟡 **Soft duplicate** — similar idea expressed differently; flag for possible consolidation

Mark **NONE FOUND** if the post is clean.

**Resolution happens at Step 12 (Phase 3).** Do not alter text during Phase 1.

---

### 1I — Writing Rules Audit (Existing Prose)

**rev-15.** English Writing Rules are not limited to newly drafted text. Read the entire original source post body against `english-writing-rules_v2.txt` and flag every violation, regardless of whether the surrounding text will otherwise be left untouched. This pass is distinct from 1H: 1H catches duplication; 1I catches forbidden words, forbidden phrases, structural tics, and narrator/register violations in the author's existing prose.

**What to flag:**

- Any Forbidden Word from `english-writing-rules_v2.txt` appearing anywhere in existing prose (e.g. "Indeed," "Furthermore," "Nestled," "Unprecedented")
- Any Forbidden Phrase appearing anywhere in existing prose (e.g. "In conclusion," "Embark on a journey," "Naturally")
- Category-colon label openers (e.g. "Fun fact:", "Pro tip:") in existing prose — still a violation everywhere in the post **except** inside a Step 9-F section-closing factoid, which is the one workflow-sanctioned use of a labeled opener (rev-16); do not extend this exception to any other location
- The "X is not just a Y. It is a Z." contrast-framing pattern in existing prose
- "We learned that" / "We realized that" constructions in existing prose
- Narrator inconsistency — first-person singular ("I", "me") where the series otherwise uses "we/us"
- Register drift — passages that shift into formal or ornamental language inconsistent with the authoritative-yet-casual house register

**What not to flag:**

- The author's sentence-level style, rhythm, and sense of humor — voice and tone are exempt, not the substance of the rules
- A word that happens to share a forbidden term's spelling but is used in an unrelated, non-cliché sense (rare; use judgement)

**Severity marking:**
- 🔴 **Clear violation** — straightforward forbidden word/phrase/tic with no stylistic justification; default to fixing at Step 12
- 🟠 **Voice-exception candidate** — the flagged word/phrase/tic appears to be doing real comedic or stylistic work specific to this passage; still flagged, but routed to the Phase 4 approval gate for an operator judgment call rather than fixed automatically (see Step 12)

**Output:** A numbered list of every violation found. For each item: location, the violation, classification (🔴/🟠), and the forbidden-rule category it falls under. Mark **NONE FOUND** if the post is clean.

**Resolution happens at Step 12 (Phase 3), using the same hierarchy as repetition resolution.** Do not alter text during Phase 1.

---

## PHASE 2 — URL Stub Lock

**The URL stub (slug) is permanently frozen. It cannot be changed under any circumstances.**

Once a Blogger post is live and crawled, changing the URL destroys all accumulated signals. This applies even when the slug is suboptimal.

- Never propose a modified URL
- Generated HTML must not contain any modified slug in any `href`
- If output HTML accidentally contains a different slug: reject and regenerate
- Confirmed at Phase 5 sanity check: zero occurrences of any modified URL stub

---

## PHASE 3 — Content Fixes

**Pre-Phase 1I / Pre-Phase 3 hard stop:** Before running Phase 1I or writing a single word of new text, confirm `english-writing-rules_v2.txt` is loaded and has been read in full during this session. Also confirm `TVC-reference-prefold-turkmenistan-part1.html` has been read — it is required for Step 3. If either has not been read yet, read them now. Do not proceed to Phase 1I or Step 1 until this is done.

Apply steps in this exact order. The order is not arbitrary — steps 1–5 handle the pre-fold zone in document sequence; steps 6–13 handle the post-body in document sequence; step 14 is the final human read-through gate before Phase 4.

Preserve all items from the Phase 1C inventory throughout.

---

### Step 1 — New SEO-Optimized Post Title

**Primary directive (rev-16): SEO keyword coverage governs the title.** The title's job is to contain the most widely searched, highest-relevance keywords for this post's route and content — place names, regions, named landmarks, and route-type terms that real searchers actually type. Everything else in this step is secondary to that.

**Rule:** One clean route → one title. Format: `[Origin] to [Destination] Overland via [waypoints or themes]`

- **Default cap: three waypoints.** This is the starting point, not an absolute ceiling. If keyword research (Phase 1A context, known search-volume patterns, or place names that are independently high-value search terms) shows that a fourth or fifth waypoint materially improves keyword coverage, include it. Do not strip a high-value place name from the title just to satisfy the three-waypoint default.
- **Test before exceeding the default:** before adding a fourth+ waypoint, confirm each additional term is a place/landmark/theme a searcher would plausibly type on its own — not a minor stop included for completeness. Padding the title with low-value waypoints to "use up" the SEO exception is not permitted; the exception exists for keyword value, not for narrative completeness.
- No emoji, no parentheticals, no business brand names — these remain hard rules regardless of SEO value, since they actively hurt CTR and clarity rather than helping search.
- In Blogger: Post Settings → Title field only. This populates both the `<title>` tag and the page H1 — do not repeat it in the body.
- **Log the decision.** Whenever the title exceeds three waypoints, note in the Phase 4 summary which waypoints were added beyond the default and the keyword rationale for each.

**Example (within default cap):**  
❌ `From Chandolin, Switzerland to Venice, Italy via Lake Como: Silk Road, Simplon Tunnel & Marco Polo's Legacy (& Shehzadi's first international oil change)`  
✅ `Chandolin to Venice Overland via the Simplon Tunnel, Lake Como, and Murano`

**Example (exceeding default for keyword coverage):**  
✅ `Ashgabat to Darvaza Overland via the Karakum Desert, Door to Hell, and Konye-Urgench` — four waypoints, each independently a high-search-volume term (Darvaza/Door to Hell is one of the most-searched Turkmenistan landmarks); justified and logged at Phase 4.

---

### Step 2 — Draft the SEO-Optimized Search Description

**Primary directive (rev-16): SEO keyword coverage governs the description, same as Step 1.** Within the 150-character limit, prioritize the highest-value search terms over completeness or elegance of phrasing.

**Where:** Blogger Post Settings → Search Description field. The theme appends ` #VagabondCouple` automatically — do not include it manually.

**Rules:**
- Maximum **150 characters** (measured before the theme's auto-appended hashtag) — this ceiling is a hard platform constraint, not adjustable
- Must include: primary route (origin → destination), the **highest-value searchable themes/landmarks** (not capped at 1–2 if more fit and each adds real keyword value — prioritize by search relevance, then fit as many as the character limit allows), and **ETR (Estimated Time to Read)**
- **ETR calculation:** count human-readable words in the post body below `<!--more-->` only — exclude the ld+json schema JSON, exclude the summary block (which is above `<!--more-->`). Divide by 238 (average adult reading pace). Round to nearest whole minute.
- Format: `[Route summary]. [Key themes/landmarks, as many high-value terms as fit]. ETR: [N] min.`
- If a choice must be made between a slightly more natural-sounding sentence and fitting one more high-value keyword inside 150 characters, favor the keyword.
- Verify character count before finalizing

**Example (~2,100 readable body words ≈ 9 min):**
> `Chandolin to Venice overland: Simplon Tunnel car train, Lake Como, Venetian silk, Marco Polo & Murano glass. ETR: 9 min.`
> (118 characters ✅)

**⚠️ ETR is a two-stage process.** At this step, draft the route summary and theme language only. **Do not calculate or commit the ETR word count here** — Steps 6, 7, 8, 9-F, 10, and 13 will all add body words that affect the count. The ETR is calculated and the description finalised at **Step 2-F** after Step 13, once all body content is complete.

---

### Step 3 — Verify or Create the Summary Block

Using Phase 1F audit findings, **always strip all existing inline CSS from the entire summary block and reapply the canonical template below.** Source posts may have divergent styling that causes visual defects (unreadable header text, missing border-radius, alternating row backgrounds that conflict with dark mode, etc.). The canonical template is the single authoritative standard regardless of what the source post contains.

**Content rules:**
- **If present and content is accurate:** preserve label text, narrative paragraph, and table row content. Strip all CSS, reapply canonical below.
- **If present but content is inaccurate:** correct label, narrative, and/or table rows. Strip all CSS, reapply canonical below.
- **If absent:** create it from scratch using canonical template. Write label, narrative, and rows appropriate to this post's route.

**Canonical summary block template** — use this exact structure and inline CSS, substituting only the text content:

```html
<div style="background: #fdf8f2; border: 2px solid rgb(139, 69, 19); border-radius: 8px; padding: 18px 22px; margin: 1.5em 0; font-family: Georgia, serif;">
  <p style="font-variant: small-caps; font-size: 0.85em; color: saddlebrown; letter-spacing: 0.08em; margin: 0 0 10px 0;">[POST TITLE] — Post Summary</p>
  <p style="margin: 0 0 14px 0;">[Narrative paragraph in author's voice — full route arc of this post.]</p>
  <table style="width: 100%; border-collapse: collapse; font-size: 0.92em;">
    <tbody>
      <tr style="border-top: 1px solid rgb(139, 69, 19);">
        <td style="padding: 6px 8px; color: saddlebrown; font-weight: bold; white-space: nowrap;">What&#39;s Covered</td>
        <td style="padding: 6px 8px;"></td>
      </tr>
      <tr style="border-top: 1px solid #e8d5b7;">
        <td style="padding: 6px 8px; color: saddlebrown;">[emoji]</td>
        <td style="padding: 6px 8px;">[Section name — brief descriptor]</td>
      </tr>
      <!-- repeat the data row pattern for each top-level H2 section -->
    </tbody>
  </table>
</div>
```

**Critical rules for the canonical template:**
- The header row uses `border-top: 1px solid rgb(139, 69, 19)` — **no dark background on any `<tr>` or `<td>`**. The saddlebrown text color alone provides the visual distinction. A dark `background` on the header row produces unreadable text in dark mode and is forbidden.
- Data row left `<td>` holds an emoji (or `▸` if no emoji) with `color: saddlebrown`. Right `<td>` holds plain text with no color override.
- No alternating `background: #fef5e7` on row cells — this conflicts with dark mode and is forbidden.
- The label `<p>` uses small-caps with `color: saddlebrown` — no `<strong>` wrapper, no font-size above `0.85em`.
- The outer `<div>` must include `border-radius: 8px` and `font-family: Georgia, serif`.
- Table rows contain one row per top-level H2 section only. No H3 or H4 sub-sections.

**Placement:** After the 1–2 intro/context paragraphs, before the ld+json schema block.

---

### Step 4 — Verify or Add the TravelAction ld+json Schema

**Placement:** Immediately after the summary block's closing `</div>`, before `<!--more-->`.

Use the structure from `TRAVELACTION-ld_json-SCHEMA-EXAMPLE.txt`. Required fields: `@context`, `@type: TravelAction`, `name`, `description`, `touristType: Overlander`, `fromLocation`, `toLocation` (with `containedInPlace`), `instrument` (vehicle: Shehzadi, Toyota, Tundra), `author` (entity/trust signal — see below), `hasPart` (legs with descriptions, plus individual `Place`, `Mountain`, `LakeBodyOfWater`, `TouristAttraction`, `Road` entries as appropriate).

**`author` field (rev-14):** Every schema must include an `author` object identifying the publishing entity, to support entity recognition and trust signals during indexing evaluation:
```json
"author": {
  "@type": "Person",
  "name": "The Vagabond Couple",
  "sameAs": "https://thevagabondcouple.blogspot.com/"
}
```
Use this exact structure on every post — name and `sameAs` value are constant across the series, do not vary per post. Do not invent additional credentials, organizations, or biographical claims not already true of the blog; the field exists to identify the consistent publishing entity, not to embellish it.

- **If schema is already present:** verify it matches the actual route — correct any mismatched place names, missing waypoints, or wrong `fromLocation`/`toLocation`. Also verify the `author` field is present in the exact form above; add it if missing.
- **If schema is absent:** create it in full, including `author`.

The schema must be valid JSON. Parse it mentally (or with a tool) before proceeding: no trailing commas, no unquoted keys, all braces and brackets balanced.

---

### Step 5 — Set `<!--more-->` Position

**`<!--more-->` is a hard requirement.** It must appear exactly once.

**Required position:** immediately after the ld+json schema's closing `</script>` tag, before any map embed or first body paragraph.

**Correction rules:**
- **Absent:** add it in the required position. Blocking error if missing.
- **Too early** (before the summary block or before the schema): move it to after `</script>`.
- **Too late** (after a map embed, image, or body heading): move it to before the map/body.
- **Inside** the summary block or schema: move it outside and after `</script>`.

After this step, the pre-fold zone is complete and locked:
```
[Hero image]
[Intro/context paragraphs]
[Summary block]
[ld+json schema]
<!--more-->
```

---

### Step 6 — Rewrite the First Body Paragraph

This is the first paragraph **below** `<!--more-->` (after any map embed). It is the first content Google's crawler reads as the main body of the page, and the first thing a reader sees after clicking through from the index.

**Rule:** Origin, destination, and primary route method must appear before any atmosphere, voice, or character introductions.

**Template:**
```
We drove from [ORIGIN] to [DESTINATION] via [KEY WAYPOINTS / METHOD].
[One sentence on what made this stretch notable — practical or thematic.]
[One sentence on what this post covers.]
```

The original voice returns from the second paragraph onward. Do not flatten the tone of the rest of the post.

**Note on intro/context paragraphs above `<!--more-->`:** Those 1–2 paragraphs (which link from the previous part and hand off narrative continuity) are in the pre-fold zone and are not the target of this rewrite. They may retain their original voice. Only the first paragraph of the clickthrough body is rewritten here.

**Writing Rules compliance gate (Step 6):** Before moving to Step 7, verify this paragraph against `english-writing-rules_v2.txt`. Confirm: narrator is "we/us", no forbidden words, no forbidden phrases, no category-colon labels, no contrast-framing pattern, no "We learned/realized that", register is authoritative-yet-casual. If any rule is violated, rewrite before proceeding.

---

### Step 7 — Add the Route Summary Box

**Placement:** After the first body paragraph (Step 6), before the Route at a Glance H2. If a map embed is present between `<!--more-->` and the first body paragraph, the Route Summary box comes after the first body paragraph — not between the map and the paragraph.

Use the `tvc-route-summary` class. No inline color styles.

```html
<div class="tvc-route-summary">
  <strong>Route:</strong> [Origin] → [stop] → [stop] → [Destination]<br />
  <strong>Method:</strong> [Overland by truck / car train through X / ferry / mixed]<br />
  <strong>Distance / Time:</strong> Approx. [X] km / [Y] days<br />
  <strong>Themes:</strong> [theme] · [theme] · [theme]<br />
  <strong>Vehicle:</strong> Shehzadi (2024 Toyota Tundra)
</div>
```

**Writing Rules compliance gate (Step 7):** The Route Summary box contains no prose sentences beyond labelled data fields, so forbidden-phrase and narrator rules are less likely to fire — but confirm no forbidden words appear in the theme or method descriptions, and that no field value duplicates a fact stated in the first body paragraph or elsewhere in the post.

---

### Step 8 — Add the Route at a Glance Section

**Placement:** Immediately after the Route Summary box, before the first section H2.

**Distinction from the summary block's "What's Covered" table:** The "What's Covered" table is pre-fold, section-based, written in the author's voice. The Route at a Glance is in-body, geography-ordered, stop-by-stop — a navigational list for readers already in the post.

```html
<h2>Route at a Glance</h2>
<ol>
  <li>[Stop or leg 1 — brief descriptor]</li>
  <li>[Stop or leg 2 — brief descriptor]</li>
  ...
</ol>
```

Use `<ol>` (ordered), not `<ul>`. One item per named stop or leg segment in travel order.

**Writing Rules compliance gate (Step 8):** Each list item is a brief descriptor, not a prose sentence, but confirm no forbidden words appear in any item text and that the stop names and descriptors do not duplicate phrasing already used in the Route Summary box or first body paragraph.

---

### Step 9 — Clean Up Section Headings

Remove images from inside `<h2>` or `<h3>` tags. Remove inline `style=` from all heading tags. Rephrase headings that bury the place name.

**Rules:**
- Headings are clean text only — no images, no inline styles
- Emoji are acceptable only when the place name or topic leads; an emoji must not be the only readable content
- A heading must contain at least one named place, concept, or event
- Move any image that was inside a heading to immediately before or after the heading as a standalone `tr-caption-container` table

**Zero-H2 source posts:** Some source posts contain no H2 headings at all — the entire body is a continuous stream of paragraphs, images, and embeds with no structural breaks. This is not an edge case to be skipped; it is a Phase 1C finding (record H2 count as 0 in the inventory) that must be resolved at Step 9 before Step 3 (summary block) and Step 8 (Route at a Glance) can be completed correctly, since both depend on H2 sections existing. When this occurs:
1. Read the full body first and map the natural topic breaks (a change of location, a new attraction, a new activity) — do not insert headings at arbitrary intervals.
2. Insert each new H2 immediately before the paragraph or image table that begins the new topic. Prefer landing right after an existing image table and right before the paragraph that shifts topic, since this is usually where the author's own prose already pivots.
3. Aim for sections of roughly 300–700 words each — consistent with the "descriptive breathers every 300-400 words" guidance in the writing rules — but let actual topic boundaries override a rigid word-count target.
4. Each new heading must satisfy the same rules as a cleaned heading: clean text, contains a named place or topic, no images or styles.
5. Build the summary block's What's Covered table and the Route at a Glance to match the new H2 structure exactly — there is no pre-existing structure to preserve, so both are created fresh at Steps 3 and 8 using the same section list.

**Summary block re-sync (after Step 9):** The What's Covered table in the summary block must match the final H2 structure. After cleaning headings (or inserting new ones in a zero-H2 post), verify that every row in the table still corresponds to an H2 that exists with the same sense (not necessarily verbatim — a heading reworded at Step 9 is still the same section). If any H2 was renamed in a way that changes its meaning, or if headings were added or removed, update the affected summary block row(s) accordingly. This check takes priority over the "do not alter summary block content" default — accuracy of the table rows is non-negotiable.

---

### Step 9-F — Section-Closing Factoids (rev-16)

**Purpose:** Relieve reader monotony and add genuine informational value at the close of most sections with a short, well-researched factoid about something in that section — a "did you know"-caliber detail that is interesting enough to be worth reading, not filler.

**Coverage:** Most top-level H2 sections get a closing factoid. Skip a section if, after genuine research effort, no factoid exists that is both interesting and non-duplicative of content already in the post (Phase 1H / 1I) — do not force a weak or generic factoid into every section just to hit full coverage. Do not add a factoid to a section that is very short (a sentence or two) where it would visually dominate the section.

**Research and sourcing standard:**
- Research each factoid using reliable sources — official tourism boards, reputable encyclopedias, established travel/history references, scientific or geological sources as relevant to the subject.
- **No hallucination.** Do not invent a statistic, date, record, or claim. If a genuinely interesting fact cannot be verified, do not include a weaker invented substitute — skip the section instead.
- **Folklore and legend-status facts are allowed**, but must be explicitly framed as such — e.g. "Local legend holds that…" / "According to local tradition…" / "The story is disputed, but…" — never presented as settled fact if the underlying claim is folkloric, disputed, or unverifiable as literal history. The factoid can still be "spicy" in framing (surprising, vivid, a little dramatic) as long as its truth-status is honestly signaled.
- A factoid must be specific to the place, object, or event covered in that section — not a generic fact about the country or region that could apply to any section.

**Placement:** Immediately before the section's closing transition (or, if no transition exists, as the final element of the section), after all other section content. One factoid per section, never two.

**Opener style — Phase 4 decision required (rev-16):** A "did you know"-style or similarly flagged opener is the one sanctioned exception to the workflow's blanket ban on category-colon/label openers (see Phase 1I and the Forbidden Phrases list) — but only for this specific use, and only with explicit per-post sign-off. At Step 9-F, draft each factoid two ways: (a) with a flagged opener (e.g. "Did you know…") and (b) folded naturally into a sentence with no label at all. Present both forms for every factoid at the Phase 4 approval gate and let the operator choose the opener style for that post. Default to the no-label form if the operator does not specify. Do not mix opener styles within a single post — pick one approach and apply it to every factoid in that post.

**Writing Rules compliance gate (Step 9-F):** Every factoid — regardless of opener style — must otherwise comply with `english-writing-rules_v2.txt`: no forbidden words, no forbidden phrases, no contrast-framing pattern, register is authoritative-yet-casual (a known sanctioned exception to the category-colon ban does not exempt the rest of the sentence from the remaining rules). Confirm the factoid introduces no fact or phrase already present elsewhere in the post (Phase 1H / 1I).

**Output for Phase 4:** A list of every section with a factoid, the factoid text in both opener forms, source/basis for the fact (including "folklore — labeled as such" where applicable), and a note for any section deliberately skipped and why.

---

### Step 10 — Add the Journey Significance Paragraph

**Placement:** After the last section content block, before the "Next Stop" outro.

One paragraph connecting this post's stops to the wider overland journey. Give the post a thesis that extends beyond individual tourist stops.

For posts on or near the Silk Road: connect the specific stops to the historical Silk Road and the expedition's overland context.

For posts not on the Silk Road corridor: connect the stops to the expedition's larger journey arc — what changed, what was learned, what the road required.

**Writing Rules compliance gate (Step 10):** Before moving to Step 11, verify this paragraph against `english-writing-rules_v2.txt`. Confirm: narrator is "we/us", no forbidden words, no forbidden phrases, no category-colon label opener, no contrast-framing pattern, no "We learned/realized that", register is authoritative-yet-casual. Also confirm the paragraph introduces no fact or idea already stated elsewhere in the post (Phase 1H / Phase 1I / Step 12 repetition and writing-rules resolution). If any check fails, rewrite before proceeding.

---

### Step 11 — Verify Internal Links Within This Post

All existing internal links in the post body must point to clean canonical URLs. Verify no `?m=1` in any `href`. Replace any `?m=1` occurrence.

Never introduce links to `?m=1` URLs. This step only affects links **within** this post's HTML — the task of adding links to this post from other posts is a separate post-publish action (see Phase 7).

---

### Step 12 — Resolve Repetition and Writing Rules Violations

Using the Phase 1H and Phase 1I findings, address every flagged repetition and every flagged writing-rules violation in the existing post body. This step applies to **author prose**, not only to newly written text — there is no separate exemption for original prose.

**Resolution hierarchy — apply in this order:**

1. **Cut** — if one instance is redundant and the remaining instance fully conveys the information, remove the weaker one. Prefer cutting over rewriting when the surviving text is already strong. For a writing-rules violation, "cut" means removing the offending word/phrase/tic without otherwise altering the sentence if possible.
2. **Reword** — if both instances are in sections where the information is genuinely needed (e.g. a fact required for context in two different sections), rewrite one of them so the wording is distinct. Do not paraphrase so lightly that the repetition is merely disguised. For a writing-rules violation, reword the offending construction while preserving the author's surrounding sentence style.
3. **Replace with researched content** — if cutting or rewording would leave a section thin, replace the cut content with a new, non-duplicative fact or observation about the same location or subject, sourced from reliable reference material (official tourism sources, reputable encyclopaedias, established travel guides). The replacement must: (a) be factually accurate and verifiable, (b) be thematically relevant to the section it appears in, (c) match the author's register — authoritative-yet-casual, not ornamental, (d) pass the English Writing Rules (no forbidden words, correct "we/us" narrator where Claude is writing), and (e) not itself duplicate any other content already in the post.

**Repetition (1H) — Hard rule:** 🔴 Hard duplicates must be resolved. A post with the same fact stated twice in different paragraphs is not deliverable.

**Repetition (1H) — Soft duplicates (🟡):** Use judgement. If the two instances serve meaningfully different rhetorical purposes, leave both and note the decision in the Phase 4 summary. If they are simply lazy repetition, resolve.

**Writing rules (1I) — 🔴 Clear violations:** Fix by default using the resolution hierarchy above. No operator confirmation needed; log the fix in the Phase 4 summary.

**Writing rules (1I) — 🟠 Voice-exception candidates:** Do not fix automatically. Carry the flagged item forward to the Phase 4 summary as an explicit line item (location, the violation, why it appears to be doing comedic/stylistic work) and present it to the operator as a decision: fix it, or grant a documented voice-exception override and leave it in place. Default action if the operator does not respond to the flag is to fix it. A granted override is logged in the Phase 4 "What Was NOT Changed" section, not silently absorbed into "voice and tone preserved."

**Scope note (rev-15):** There is no exemption for existing author prose from the substance of the English Writing Rules. The only standing exemption is *voice and tone* — the author's sentence-level style and sense of humor are not normalized away. Forbidden words, forbidden phrases, structural tics, narrator inconsistency, and repetition are violations wherever they occur and must be resolved here, subject to the voice-exception override above.

---

### Step 13 — Insert Image Separator Paragraphs

Using the Phase 1C consecutive-image flag list, insert a separator paragraph between every pair of consecutive `tr-caption-container` tables identified during the scan.

**Rules for separator content:**

1. **Minimum one `<p>` element** between any two `tr-caption-container` tables. A `.separator` div, a `<br>`, or whitespace does not satisfy this requirement — it must be a `<p>` with readable prose.
2. **Content must be original and non-repetitive.** The separator paragraph must not restate anything already said in the surrounding paragraphs, the section body, or anywhere else in the post (apply the same repetition check as Step 12 to separator content before inserting it).
3. **Content must be factually grounded.** Research the location, attraction, or subject depicted in the two adjacent images. Write a paragraph that adds genuine informational value — a detail about the history, construction, cultural significance, practical reality, or sensory character of what is shown — that is not covered elsewhere in the post.
4. **Match the author's register.** Authoritative-yet-casual. No ornamental language, no category-colon labels, no forbidden words or phrases. First-person plural ("we") where a narrator voice is appropriate; third-person descriptive where factual context fits better.
5. **Length:** 2–4 sentences. Long enough to constitute a real paragraph; short enough not to bloat the post.
6. **The separator paragraph itself must pass the Phase 1H repetition check** before it is inserted — verify it introduces no new duplication with existing content.

**What counts as "consecutive":** Two `tr-caption-container` tables are consecutive if the only HTML between their closing `</table>` and the next opening `<table` is whitespace, empty `<p></p>` tags, or `.separator` divs with no text content. A `<p>` containing at least one word of prose breaks the sequence.

**YouTube embeds and map iframes** are not `tr-caption-container` tables and do not count toward consecutive image pairs. However, a `tr-caption-container` table immediately before or after a YouTube embed with no prose between them is a visual density problem — flag it as a soft issue in the Phase 4 summary but do not treat it as a blocking error for this step.

**Writing Rules compliance gate (Step 13):** Every separator paragraph must be verified against `english-writing-rules_v2.txt` before insertion. Confirm: no forbidden words, no forbidden phrases, no category-colon label opener, no contrast-framing pattern, register is authoritative-yet-casual. Also confirm it introduces no fact or phrase already present in the post. If any check fails, rewrite the separator before inserting it.

**Final full-body repetition sweep (after Step 13):** All body content is now present — original prose, Step 12 rewrites, Step 13 separators, and all other new text from Steps 6–10. Run one complete pass across the entire body checking for any repetition that the per-step gates may not have caught: (a) new text from two different steps that happen to cover the same fact, (b) a separator paragraph that echoes a phrase from a section rewritten at Step 12, (c) the Journey significance paragraph (Step 10) overlapping with the Route at a Glance (Step 8) in more than route naming. Resolve any issues found using the Step 12 resolution hierarchy before proceeding to Step 2-F.

---

### Step 2-F — Finalise ETR and Search Description

All body content is now complete. Calculate the final ETR and write the search description.

**ETR calculation (final):** Count every human-readable word in the post body below `<!--more-->` — including the rewritten first body paragraph (Step 6), Route Summary box (Step 7), Route at a Glance items (Step 8), section-closing factoids (Step 9-F), Journey significance paragraph (Step 10), any replacement content from Step 12, and all separator paragraphs from Step 13. Exclude ld+json schema JSON. Divide total by 238. Round to nearest whole minute.

**Finalise the description:** Take the route summary and theme language drafted at Step 2, insert the calculated ETR, and verify the total character count is ≤150. Adjust wording if the count is over — never truncate the ETR itself.

**Writing Rules compliance gate (Step 2-F):** The search description is newly written output text. Before logging it in the Phase 4 summary, verify it against `english-writing-rules_v2.txt`: no forbidden words, no forbidden phrases, no category-colon label opener. The narrator rule ("we/us") applies if the description uses a first-person voice — if it is written in third-person route-summary style it is exempt, but confirm no forbidden words appear regardless of voice.

**Update the Phase 4 summary:** Replace the Step 2 row with the final description text, character count, and confirmed ETR.

---

### Step 14 — Structural Cohesion & Holistic Read-Through (rev-18)

This step has two sequential sub-phases. **14A must return PASS before 14B begins.** This is the final step before Phase 4.

---

#### 14A — Mechanical Cohesion Check (Pre-requisite)

Run these objective, deterministic checks on the drafted post (all content from Steps 1–13 and Step 2-F in place). Fix any failures before proceeding to 14B — do not carry a 14A gap forward into the holistic read.

1. **Pronoun/Entity Consistency (new text only):** Scan all text added or rewritten in Phase 3 (Steps 6, 7, 8, 9-F if included, 10, 12 replacements, 13 separators). Verify:
   - First-person is consistently "we"/"us" — no "I" or "me" appears.
   - The vehicle "Shehzadi" is spelled identically wherever it appears in new text. If the source post's own usage is internally inconsistent or in question, defer to the canonical spelling already established elsewhere in the series (not simply "whatever the source's first mention happens to say") — flag a source-level inconsistency rather than silently propagating it.
   - All named places and landmarks in the new text match the spelling/transliteration already established in the existing source prose (e.g., if the source uses "Aşgabat" with a diacritic, new text must match it, not substitute "Ashgabat").

2. **Structural Matching:** Compare the **Route at a Glance** `<ol>` list items directly against the **H2 headings** present in the body below `<!--more-->` — item by item, not by way of the summary block table.
   - Every `<li>` must correspond to an H2 heading that exists (the sense must match — verbatim equality is not required, but the stop/leg named in the list must have a corresponding section heading).
   - Every H2 heading (excluding "Route at a Glance" itself and "Next Stop") must have a corresponding `<li>` in the Route at a Glance.
   - If a mismatch exists, either adjust the Route at a Glance list or insert/move an H2 heading to match. Do not proceed to 14B until the lists are structurally aligned.

3. **Transition Completeness (limited to heavily edited sections):** For any H2 section where the body was substantially rewritten (Step 9 heading rephrasing, Step 12 replacement, or Step 13 separator insertion), verify the first sentence of the *next* section does not start abruptly with a proper noun that was not mentioned in the current section's last sentence. If it does, add a short bridging phrase to the current section's closing. This is a scoped check — do not inspect unmodified sections.

**Output for Phase 4:** Either `14A — MECHANICAL PASS` or `14A — GAP FOUND: [list specific mismatches fixed]`.

**Gate:** 14B may not begin until 14A returns PASS.

---

#### 14B — Holistic Smooth-Reading Gate

After all content changes from Steps 1–13 and Step 2-F have been planned and drafted, and 14A has returned PASS, read the entire post from first word to last — including the pre-fold zone, the rewritten first body paragraph, the Route Summary box, the Route at a Glance, every section, every section-closing factoid, every separator paragraph, the Journey significance paragraph, and the Next Stop outro — as a first-time human reader who has not read the source post and has no prior knowledge of the series.

**This is not a checklist pass.** It is a holistic reading for coherence, flow, and naturalness. The question is not "does each component comply with its individual rule?" but "does this post read as a single, well-written, authored piece?"

**Block the Phase 4 submission and fix before proceeding if any of the following are true:**

- Any section feels abrupt or disconnected from what precedes it — a transition is missing or jarring
- Any newly written paragraph (Steps 6, 7, 8, 9-F, 10, 12 replacements, 13 separators) reads with a noticeably different voice from the author's surrounding prose — it sounds like a different writer
- The rewritten first body paragraph and the author's second paragraph do not flow into each other naturally
- A separator paragraph inserted at Step 13 reads as filler or interrupts the visual narrative rather than adding genuine value
- A section-closing factoid (Step 9-F) reads as filler, feels forced into a section where it doesn't belong, or makes the post feel gimmicky through repetition of the same factoid format section after section
- A folklore/legend factoid is not clearly framed as such, or reads as if presented as settled fact
- The Journey significance paragraph feels grafted on rather than earned by the post's content
- The Route at a Glance and Route Summary box, when read in sequence with the first body paragraph, repeat the same route information three times without each serving a clearly distinct purpose for the reader
- Any heading rephrased at Step 9 reads awkwardly or loses the sense of the original
- The post as a whole feels longer than its content warrants — flag any section that could be tightened without losing author voice or factual substance

**Output for Phase 4:** Either `14B — PASS — post reads as a coherent, smoothly flowing whole` or a list of specific issues found and how they were resolved. If issues required further edits, those edits must themselves be re-checked against writing rules and the repetition rule, and against 14A's criteria if the edit touched pronouns, names, or structure, before the Phase 4 summary is submitted.

**This step cannot be skipped.** A post that passes every individual checklist item but reads poorly as a whole is not deliverable. Both 14A and 14B must return PASS before Phase 4.

---

## PHASE 4 — Approval Gate

After completing all Phase 1 passes and all Phase 3 steps (including Step 2-F and the Step 14 read-through), present the modification summary below. **Stop. Do not generate output HTML until the operator provides explicit approval.**

Use this exact template, filled in for the specific post:

```
## Proposed Modifications — [POST TITLE]
URL (unchanged): [clean URL]

### Fact Check (1A)
[PASS / FLAGGED ITEMS — list any ⚠️ or ❌]

### Readability (1B)
Flags found: [PASS / list each flag]
Flags resolved in Phase 3: [PASS — all resolved / list each resolution]

### Character Encoding (1G)
[NO SUSPECT QUESTION MARKS FOUND / complete literal-`?` audit table: location, classification, action, replacement if applicable; list any U+FFFD or numeric-entity findings]

### Media & Links Inventory (1C)
Photograph images: [N] (all in tr-caption-container tables) — retained ✅
Consecutive image pairs found: [N pairs / NONE] — [listed: image N+image N+1 at [section] / NONE]
Internal links: [N] — all clean URLs, no ?m=1 ✅
External links: [N] — rel= and target= preserved ✅
YouTube embeds: [N] — [absent / re-emitted using project template ✅]
Map embeds: [N] — [absent / src= and structure unchanged ✅]
Other iframes/embeds: [N] — [absent / describe each, confirm retained ✅]
<!--more--> tag: [present at line N / MISSING — will be added / moved from line N to correct position]

### Repetition Scan (1H)
[NONE FOUND / numbered list of each repetition: location, what repeats, severity 🔴/🟡]

### Writing Rules Audit — Existing Prose (1I) — rev-15
[NONE FOUND / numbered list of each violation: location, the violation, category, severity 🔴/🟠]
🔴 Clear violations: [resolved at Step 12 / NONE]
🟠 Voice-exception candidates awaiting operator decision: [list each, with the case for leaving it / NONE]

### Summary Block (1F)
Status: [Present and accurate / Present, corrected: [what changed] / Absent — will be created]
Label: ✅ | Narrative paragraph: ✅ | What's Covered table: [N] rows ✅
CSS: stripped and reapplied to canonical template ✅
Position: after intro paragraphs, before ld+json ✅

### CSS Changes (1D)
Inline style= attributes stripped: [N occurrences, list types]
Summary block CSS: stripped and reapplied to canonical template ✅
YouTube embed inline CSS: preserved (from project template, exempt) ✅
New class: tvc-route-summary [added to theme / already present in theme ✅]
Hardcoded colors removed from body: [list any found and removed]

### Content Changes (Phase 3 step order)
Step 1 — Title: [old] → [new] | Waypoint count: [3 (default) / N — keyword rationale per waypoint beyond 3: list each]
Step 2 — Search description draft: route/theme language drafted ✅ (ETR finalised at Step 2-F)
Step 3 — Summary block: [verified / corrected / created]
Step 4 — Schema: [verified / updated / added]; author field: [present / added]
Step 5 — <!--more-->: [confirmed in place / moved from line N / added]
Step 6 — First body paragraph: rewritten (route-first)
Step 7 — Route Summary box: added (tvc-route-summary)
Step 8 — Route at a Glance: added ([N] stops, <ol>)
Step 9 — Headings cleaned: [list each old → new]; summary block re-sync: [NONE REQUIRED / list any rows updated]
Step 9-F — Section-closing factoids: [N sections with factoid / list: section — factoid (opener style: labeled/unlabeled) — source or "folklore, labeled"] | Sections skipped: [NONE / list each, with reason] | Opener style for this post: [labeled "Did you know" style / unlabeled, folded into sentence] — operator decision
Step 10 — Journey significance paragraph: added after [section name]
Step 11 — Internal link hrefs verified: [N] links, no ?m=1 ✅
Step 12 — Repetition and writing-rules violations resolved: [NONE REQUIRED / list each resolution: what was cut/reworded/replaced and with what] | Voice-exception overrides granted: [NONE / list each, with operator decision]
Step 13 — Image separators inserted: [NONE REQUIRED / N separator paragraphs inserted at: list locations]
Final full-body repetition sweep: [CLEAN / list any issues found and resolved]
Step 2-F — Search description finalised: "[final text]" ([N] chars, ETR: [N] min, based on [N] body words) ✅
Step 14 — 14A Mechanical Cohesion: [PASS / list mechanical fixes applied] | 14B Holistic Read-Through: [PASS — post reads as a coherent, smoothly flowing whole / list issues found and how resolved]

### Writing Rules Compliance (english-writing-rules_v2.txt) — applies to entire post body, original and new text alike (rev-15)
File confirmed loaded: ✅
Existing prose (1I audit): [PASS — all 🔴 resolved, 🟠 candidates decided / list any still open]
Step 6 (first body paragraph): [PASS / issues found and fixed]
Step 7 (Route Summary box): [PASS / issues found and fixed]
Step 8 (Route at a Glance): [PASS / issues found and fixed]
Step 9-F (section-closing factoids — sourcing, register, opener-style consistency, folklore framing where applicable): [PASS / NONE ADDED / issues found and fixed]
Step 10 (Journey significance paragraph): [PASS / issues found and fixed]
Step 13 (separator paragraphs): [PASS / NONE INSERTED / issues found and fixed]
Step 12 (replacement content and existing-prose fixes): [PASS / NONE WRITTEN / issues found and fixed]
Step 2-F (search description): [PASS / issues found and fixed]

### What Was NOT Changed
- URL stub: unchanged ✅
- Author voice, humor, and tone: preserved ✅ — including any 🟠 voice-exception overrides granted: [NONE / list each]
- All [N] photograph images and alt text: unchanged ✅
- All [N] tr-caption-container table structures: preserved ✅
- All internal and external `href` values: exact byte-for-byte preservation verified against Phase 1C inventory, except approved canonical cleanup ✅
- All map embed src= values: unchanged ✅
- Summary block CSS: stripped and reapplied to canonical template ✅
- title= attributes on img tags: preserved ✅

Awaiting approval to proceed with HTML generation.
```

---

## PHASE 5 — HTML Generation and Sanity Check

**Only after explicit operator approval from Phase 4.**

**Verification standard (Rule G2):** The HTML Sanity Checklist below must be completed twice, by two different methods, with zero gaps before Phase 6 delivery is permitted. A single clean pass is not sufficient. See Rule G2 for the full procedure and indicator format.

**rev-16 — Phase 1 blind-spot safeguard:** G2's two passes verify the output against Phase 1's findings — they cannot catch something Phase 1 itself missed during the original scan, since both passes treat the Phase 1 inventories and audits as ground truth. If a later full re-run of this same post (a second pass through the entire workflow, not just Phase 5) surfaces an issue that should have been caught the first time, treat it as a Phase 1 methodology gap, not a Phase 5 failure, and apply the corrective step below before delivering this post:
- Identify which Phase 1 pass should have caught it (1A/1B/1C/1D/1F/1G/1H/1I) and why it didn't (wrong scope, ambiguous instruction, the pass wasn't actually re-read against the live output, etc.).
- Before finalizing this post, re-run that specific Phase 1 pass on the **current** output (not the original source) once more, since a gap in the original scan may mean other instances of the same issue exist uncaught.
- Note the gap and its root cause in the Phase 4 summary if Phase 4 has not yet been presented, or as an addendum if this is discovered post-approval — operator visibility into recurring blind spots is part of the verification record, not an admission to bury.
- If the same category of gap has now occurred on two or more separate posts, it is a workflow defect, not a one-off — flag it explicitly to the operator as a candidate for a workflow revision, rather than silently patching it post-by-post.

---

### HTML Output Rules

1. **Post body HTML only.** Everything that goes into the Blogger post HTML editor. No `<html>`, `<head>`, or `<body>` wrapper tags.

2. **Follow the canonical document structure exactly:**
   ```
   [Hero image — tr-caption-container]
   [1–2 intro/context paragraphs]
   [Summary block — canonical inline CSS from Step 3 template]
   [TravelAction ld+json <script> block]
   <!--more-->
   [Map embed — if present; otherwise next item follows directly]
   [First body paragraph — route-first rewrite]
   [tvc-route-summary box]
   [Route at a Glance H2 + <ol>]
   [Post body sections...]
   [Journey significance paragraph]
   [Next Stop outro]
   ```

3. **Inline style= stripping:** Remove all inline `style=` from post body except: (a) summary block — strip source CSS and reapply canonical template from Step 3 exactly; (b) YouTube embed wrapper divs — exempt, use project template verbatim.

4. **Blogger image-caption tables:** All `tr-caption-container` / `tr-caption` table structures preserved exactly. No conversion to other formats.

5. **YouTube embeds:** All YouTube embeds (pre-existing and any new) use the `YOUTUBE-VIDEO-EMBED-FOR-BLOGGER.txt` template. Original video IDs and captions preserved.

6. **URL stub:** Unchanged. Zero occurrences of any modified slug in any `href`.

7. **`<!--more-->`:** Present exactly once, immediately after ld+json `</script>`, before map or body.

---

### HTML Sanity Checklist

All checks must pass. A failing check blocks delivery — fix the issue and re-check.

**Document structure:**
- [ ] No `<html>`, `<head>`, or `<body>` wrapper tags in output
- [ ] No broken or unclosed tags (every opened tag is closed; no orphaned `</p>`, `</div>`, `</td>`)
- [ ] Canonical document order followed (pre-fold zone → `<!--more-->` → body)
- [ ] `<!--more-->` present exactly once, immediately after ld+json `</script>`

**Pre-fold zone:**
- [ ] Hero image in `tr-caption-container` table, first in document
- [ ] Intro/context paragraphs present (1–2 paragraphs)
- [ ] Summary block present with all three parts: label, narrative paragraph, What's Covered table
- [ ] Summary block CSS matches canonical template from Step 3 exactly (not source post CSS)
- [ ] Summary block positioned before ld+json schema
- [ ] What's Covered table rows match actual top-level H2 sections in post body
- [ ] ld+json schema positioned between summary block and `<!--more-->`
- [ ] ld+json is valid JSON: balanced braces/brackets, no trailing commas, no unquoted keys
- [ ] `"@type": "TravelAction"` confirmed in schema
- [ ] `fromLocation` and `toLocation` correctly populated
- [ ] `author` field present with `@type: Person`, `name: "The Vagabond Couple"`, `sameAs: "https://thevagabondcouple.blogspot.com/"` — exact and unvaried across posts

**First body paragraph (below `<!--more-->`):**
- [ ] First content paragraph (after any map embed) contains origin, destination, and route method within its first 150 words
- [ ] Route-first paragraph is immediately after map embed (or after `<!--more-->` if no map)

**Route Summary and navigation:**
- [ ] `tvc-route-summary` class used (no inline color styles)
- [ ] Route at a Glance uses `<ol>`, not `<ul>`
- [ ] Route at a Glance positioned after tvc-route-summary, before first section H2

**CSS / style compliance:**
- [ ] Zero inline `style=` attributes stripped from post body (summary block and YouTube wrapper divs are the only permitted exceptions)
- [ ] Zero hardcoded hex or named colors in any new elements
- [ ] No images inside `<h2>` or `<h3>` tags
- [ ] All headings are clean text only

**Repetition and existing-prose writing rules (1H / 1I / Step 12):**
- [ ] All 🔴 hard duplicates identified in Phase 1H are resolved in the output — no fact, statistic, or near-verbatim phrase appears twice in the body
- [ ] All 🟡 soft duplicates are either resolved or explicitly noted as intentional in the Phase 4 summary
- [ ] All 🔴 clear writing-rules violations identified in Phase 1I (existing prose) are resolved in the output — no forbidden word, forbidden phrase, or structural tic remains, except where a 🟠 override was explicitly granted
- [ ] All 🟠 voice-exception candidates from Phase 1I were presented at Phase 4 and have a recorded operator decision (fixed, or override granted and logged in "What Was NOT Changed")
- [ ] Any replacement content written during Step 12 passes the English Writing Rules and introduces no new repetition
- [ ] Separator paragraphs added at Step 13 do not themselves duplicate any existing content
- [ ] Final full-body repetition sweep (after Step 13) was completed with zero unresolved issues — no cross-step duplication between new text from different steps remains in the output

**Image spacing (1C / Step 13):**
- [ ] No two `tr-caption-container` tables are adjacent without at least one `<p>` containing prose between them
- [ ] Every separator paragraph inserted at Step 13 contains factually accurate, researched content
- [ ] Separator paragraphs match the author's register — no forbidden words, no category-colon labels, no ornamental language

**Media and links (cross-reference Phase 1C inventory):**
- [ ] All [N] photographs present with unchanged `src` URLs
- [ ] All [N] photographs have descriptive `alt=` text
- [ ] `title=` attributes on images preserved where present
- [ ] All [N] `tr-caption-container` tables structurally intact
- [ ] All YouTube embeds present, using project template format (wrapper div + iframe + tr-caption paragraph)
- [ ] All map embeds present with unchanged `src` URLs and structure
- [ ] All other iframes/embeds present and unchanged
- [ ] All [N] internal links present with exact original `href` values preserved byte-for-byte, except approved `?m=1` canonical cleanup under Rule G3
- [ ] All [N] external links present with exact original `href` values preserved byte-for-byte and original `rel=` and `target=` attributes retained
- [ ] Zero unapproved `href` differences from the Phase 1C inventory
- [ ] Zero `?m=1` in any internal `thevagabondcouple.blogspot.com` `href` unless explicitly approved as intentional

**URL stub:**
- [ ] No modified slug appears anywhere in the output HTML

**Deliverable verification:**
- [ ] Deliverable 2 (title): waypoint count is 3 by default, or >3 only with a logged keyword-value rationale per added waypoint (Step 1, rev-16); no emoji, no parentheticals, no brand names
- [ ] Deliverable 3 (search description): ≤150 characters (count manually), ETR present, highest-value searchable themes/landmarks prioritized over completeness, format correct

**Re-run Phase 1A facts check on new text:**
- [ ] No factual errors introduced in the rewritten first body paragraph, Route at a Glance, Route Summary box, or Journey significance paragraph
- [ ] Every Step 9-F factoid is independently verifiable from a reliable source, or explicitly and visibly framed as folklore/legend/disputed if its truth-status is not settled — zero factoids presented as settled fact without a verifiable basis

**Section-closing factoids (Step 9-F, rev-16):**
- [ ] Coverage matches the Phase 4 log — every section listed as "has factoid" has one, every section listed as "skipped" has none, and skip reasons are genuine (no available non-duplicative fact), not laziness
- [ ] No factoid duplicates a fact already stated elsewhere in the post (re-check against 1H / 1I findings and Step 12 resolutions)
- [ ] No factoid is generic enough to apply to any section in the series — each is specific to its own section's place/object/event
- [ ] Folklore/legend/disputed factoids are explicitly framed as such in the text itself, not just in the Phase 4 sourcing note
- [ ] Opener style (labeled "Did you know" vs. unlabeled) is consistent across every factoid in the post, matching the operator's Phase 4 selection
- [ ] Each factoid otherwise passes English Writing Rules (forbidden words/phrases, contrast-framing, register) aside from the sanctioned opener-style exception

**Character encoding (Phase 1G):**
- [ ] Every literal `?` character in the output has been audited and classified as legitimate punctuation, intentional illegible-signage notation, corrected corruption, or approved operator-confirmed exception
- [ ] Zero unresolved suspicious `?` characters anywhere in body text, headings, captions, `alt=`, `title=`, summary block text, Route Summary box, Route at a Glance, or ld+json string values
- [ ] Zero sequences of 2+ consecutive literal `?` characters anywhere in the output unless explicitly documented as intentional illegible-signage notation
- [ ] Zero Unicode replacement characters (U+FFFD `�`) anywhere in the output
- [ ] All non-ASCII characters in body text, headings, captions, `alt=`, `title=`, and ld+json string values are correctly encoded UTF-8 — not numeric entities, not `?` placeholders
- [ ] All non-ASCII characters in newly written text (first body paragraph, Route Summary box, Route at a Glance, Journey significance paragraph, summary block narrative, ld+json schema) are verified correct — place name diacritics, degree symbols, arrow characters, and em/en dashes included
- [ ] Any corruption found in the source and reconstructed during Phase 1G is confirmed fixed in every duplicate occurrence across prose, captions, attributes, summary block, route boxes/lists, and schema

**English Writing Rules compliance — applies to the entire post body, original prose and newly written text alike (rev-15) — `english-writing-rules_v2.txt` must be loaded, not applied from memory:**
- [ ] `english-writing-rules_v2.txt` was confirmed present and read in full before Phase 1 and Phase 3 began
- [ ] Narrator is "we" / "us" throughout the post — no first-person singular ("I", "me") anywhere, original prose or new text
- [ ] No Forbidden Words anywhere in the post body, original or new: Harness, Leverage, Empower, Propel, Ignite, Amplify, Foster, Indeed, Furthermore, Notably, Consequently, Ultimately, Substantially, Delve, Explore, Comprehensive, Landscape, Realm, Tapestry, Pivot, Holistic, Multifaceted, Nestling, Nestled, Testament to, Unwavering, Heartfelt, Unprecedented, Ponder, Unlocking the potential — except where a 🟠 voice-exception override was explicitly granted at Phase 4
- [ ] No Forbidden Phrases anywhere in the post body, original or new: "In the ever-evolving landscape of", "It is worth mentioning that", "As we navigate the complexities of", "At the forefront of", "In conclusion", "Today's fast-paced world", "Game-changing solution", "Embark on a journey", "Naturally" — except where a 🟠 voice-exception override was explicitly granted at Phase 4
- [ ] No sentence anywhere opens with a category-colon label (e.g. "Fun fact:", "Historical irony:", "Pro tip:" — these are banned structural tics), original or new — **except** Step 9-F section-closing factoids if the operator selected the labeled "Did you know" style for this post at Phase 4 (rev-16); confirm the post is internally consistent — either every factoid uses the labeled style or none do, never mixed
- [ ] No "X is not just a Y. It is a Z." contrast-framing pattern anywhere in the post body
- [ ] No "We learned that" or "We realized that" construction anywhere in the post body — state the fact directly
- [ ] The post stays in an authoritative-yet-casual register throughout — no shift into formal or ornamental language, including in unmodified original passages
- [ ] Non-repetition gate (newly written sections): no idea, concept, or factual claim in the rewritten first body paragraph, Route Summary box, Route at a Glance, Journey significance paragraph, or separator paragraphs duplicates something already said elsewhere in the post body (full-body repetition across all existing prose is handled separately by Phase 1H / Step 12 above)
- [ ] Search description (Step 2-F) contains no forbidden words or forbidden phrases; if written in first-person voice, narrator is "we/us"
- [ ] Every 🔴 violation flagged in Phase 1I is resolved in the output; every 🟠 candidate has a logged operator decision (see Phase 4 "What Was NOT Changed")
- [ ] Voice and tone — the author's sentence-level style and humor — were preserved, not flattened into uniform house style, throughout this resolution process

**Step 14 re-run on generated HTML (rev-18 — scoped, not full duplication):**

**14B (Holistic Read-Through) — re-run in full:**
- [ ] The generated HTML has been read top-to-bottom as a first-time human reader — not scanned for checklist items, but read for flow and coherence
- [ ] All Phase 3 changes integrate seamlessly; no section reads as patched or inserted by a different writer
- [ ] Transitions between sections are natural — no abrupt jumps caused by edits
- [ ] Separator paragraphs (Step 13) add genuine value and do not read as filler
- [ ] The Journey significance paragraph is earned by the post's content, not grafted on
- [ ] The post reads as a single authored piece from first word to last
- [ ] If any issue was found during this final read, it was fixed and the fix was re-verified against writing rules before delivery

**14A (Mechanical Cohesion) — re-run selectively, not in full:** Two of 14A's three checks have no equivalent anywhere else in this checklist and must be re-verified directly against the generated HTML, since HTML generation itself can introduce a mismatch that wasn't present in the draft:
- [ ] **Route at a Glance ↔ H2 direct correspondence:** every `<li>` in the generated HTML's Route at a Glance still corresponds to an actual H2 in the generated body, and every body H2 (excluding "Route at a Glance" and "Next Stop") still has a corresponding `<li>` — checked directly against each other, not inferred from the summary block table or from the Route at a Glance's position in the document
- [ ] **Place/vehicle name spelling consistency:** every occurrence of "Shehzadi" and every named place/landmark in the generated HTML uses the same spelling/transliteration throughout — re-verify directly, since this has no analog in the encoding audit (1G catches corruption, not transliteration drift) or in the narrator-pronoun checklist item below

**14A items intentionally not re-run here (confirmed non-redundant exclusion, rev-18):**
- Narrator pronoun consistency ("we"/"us", no "I"/"me") — already covered in full by the English Writing Rules compliance checklist item above ("Narrator is 'we' / 'us' throughout the post")
- The proper-noun transition scan — substantially covered by the 14B holistic read immediately above, which independently catches abrupt section openings as part of "transitions between sections are natural"

---

## PHASE 6 — Deliverables

Present all three simultaneously after the sanity check passes.

**Deliverable 1 — Updated post body HTML**  
Complete, validated, sanity-checked HTML. Ready to paste into the Blogger post HTML editor (Edit → HTML view). Replaces the entire current post body content.

**Deliverable 2 — New SEO-optimized post title**  
Ready to paste into Blogger: Post Settings → Title. One sentence, three waypoints by default — more only where each added waypoint is an independently high-value search term, logged at Phase 4 — no emoji, no parentheticals.

**Deliverable 3 — New Blogger search description**  
Ready to paste into Blogger: Post Settings → Search Description. Maximum 150 characters. Includes ETR. The theme appends ` #VagabondCouple` automatically — do not include it.

---

## PHASE 7 — Publish, Link, and Index

### 7A — Publish

1. Paste Deliverable 2 into Post Settings → Title
2. Paste Deliverable 3 into Post Settings → Search Description
3. Paste Deliverable 1 into the post HTML editor (replacing the entire body)
4. Publish the post
5. Wait 5–10 minutes for Blogger to propagate

### 7B — Add Cross-Links to Related Posts (separate editing task)

After publishing, edit adjacent posts in the series to add links to this post. This is a separate task from the HTML generation above and requires individual edits to other published posts.

**Links to add:**
- Previous leg post: add anchor text describing this post's route (e.g. `Chandolin to Venice overland via the Simplon Tunnel`)
- Next leg post: add a back-reference to this post
- Thematically related posts (same region, shared theme): add descriptive anchor text links

All anchor text must be descriptive and route-specific. Never link to `?m=1`.

### 7C — Request Indexing

**Prerequisite: Phase 7B cross-links must be added before requesting indexing.** Interlinking between related posts is part of the site's topical signal. Requesting indexing before cross-links are in place means Google crawls a less-connected page. Complete 7B first.

1. Google Search Console → URL Inspection → paste clean canonical URL (no `?m=1`)
2. Test Live URL — confirm Google can fetch the page
3. Confirm Google-selected canonical is the clean URL
4. Click Request Indexing
5. Log the date

Do not request indexing more than once per two weeks for the same URL. Return in 7–14 days to confirm status changed to Indexed.

---

## PHASE 8 — Whole-Blog Editorial Retrospective (rev-16)

**When this phase runs:** Not per-post. Run Phase 8 after a meaningful batch of posts has been processed under this workflow (e.g. a full series, or a natural checkpoint the operator calls for) — whenever the operator wants a step back from individual-post mechanics to assess the body of work as a reader and as an editor would. This phase is explicitly invoked by the operator; it does not run automatically at the end of every single post.

**Purpose:** Phases 1–7 verify each post against its own rules in isolation. Nothing in the per-post pipeline reads the blog the way an actual visitor or a publishing editor would: start to finish, across multiple posts, noticing patterns, fatigue, and quality drift that only show up at scale. Phase 8 is that reading.

**Sourcing the read:** The posts in scope are live on `thevagabondcouple.blogspot.com`, not sitting in chat context from earlier in this session. Fetch each post's live published URL in sequence (the operator provides the batch's URL list, or it is pulled from `Silk-Road-Journey-Blog-URLs-in-Sequence.md` or the equivalent reference list for the series in question) and read the rendered post as a visitor would encounter it — not the HTML source, not the Phase 4 summaries from when each post was processed. Reading the Phase 4 summaries instead of the live posts would just re-run the same per-post lens Phase 8 exists to get away from.

### 8A — The Slow Read

Read the processed posts in their published sequence, the way a real visitor working through the series would — not skimming for compliance, not checking boxes, but reading for the actual experience: does this hold attention, does the voice stay consistent, does the structure start to feel formulaic by the fifth or tenth post even though each one individually passed every gate.

**Read for:**
- **Cross-post repetition** that no single-post repetition scan (1H) could ever catch, since 1H is scoped to one post — the same anecdote, the same turn of phrase, the same factoid-opener rhythm, or the same section-closing beat repeating across consecutive posts in a way that becomes noticeable to a reader going through the series.
- **Formula fatigue** — Step 9-F factoids, Route at a Glance lists, Route Summary boxes, and Journey significance paragraphs are individually justified per post, but reading several posts back-to-back may reveal they've become a predictable, skippable ritual rather than something a reader looks forward to.
- **Voice drift across the batch** — does the author's voice feel the same in post 1 and post 12 of a series, or has the cumulative effect of many small Step 12/1I fixes flattened it without any single fix being individually responsible.
- **Title and description pattern overuse** — does the rev-16 SEO-primary title/description latitude, applied post after post, start to read as keyword-stuffed across the series even though each individual title passed its own justification test.
- **Factoid quality distribution** — are the Step 9-F factoids genuinely interesting throughout, or did quality decay as the batch went on (later posts getting weaker, more generic, or more frequently skipped than earlier ones).
- **Structural consistency** — does the canonical document structure actually produce a consistent reading rhythm across posts, or do some posts feel noticeably longer, denser, or thinner than their neighbors without good reason.

**This is not a checklist pass and does not use a rubric in real time.** Read first. Form impressions. Only after the full read, organize those impressions into the editorial report below.

### 8B — The Editor's Report

After the slow read, switch explicitly into the stance of a rigorous publishing editor reviewing a body of work before it goes further — someone whose job is the reader's experience and the publication's quality bar, not the individual contributor's effort.

**Produce a report with these sections:**

1. **Overall assessment** — one or two paragraphs, direct and unvarnished. Is this body of work in good shape? Would an editor sign off on it as-is?
2. **Strengths observed** — what is genuinely working well across the batch (specific, not generic praise).
3. **Issues found** — every pattern-level problem identified during 8A, each with: what it is, which posts it appears in, and severity (🔴 reader-facing quality problem / 🟡 minor or borderline / ⚪ noted but not actionable).
4. **Recommendation: run again, or proceed?** A direct yes/no-style recommendation on whether the affected posts should go through another remediation pass before being considered final, with the reasoning stated plainly. This is a judgment call, not a checklist outcome — make it as a call, not a hedge.
5. **If "run again" is recommended:** for every 🔴 or significant 🟡 issue identified, state the specific workflow rule, step, or phase that — had it existed or been worded differently — would have caught or prevented this issue the first time. This is the feedback loop: issues found at the blog level should translate into concrete proposed edits to this workflow document (new checklist items, a new phase, a reworded rule), not just into one-off fixes to the affected posts. List these as a numbered set of proposed workflow changes, each tied to the issue that motivated it.
6. **If "proceed" is recommended:** state explicitly that no batch-level issues rise to the level of requiring rework, and which minor (🟡/⚪) items, if any, are worth keeping an eye on in future posts without blocking anything now.

**Output format:** Present the full report in one comprehensive message — this is the one phase where Rule G1's minimum-verbosity default is intentionally suspended, since the entire point of Phase 8 is the operator reading the editorial judgment in full, not a status indicator.

**Hard rule:** Phase 8 does not modify any post's HTML directly. It produces findings and recommendations only. Any fix it identifies as necessary is executed as its own subsequent per-post pass through Phases 1–7, on the affected post, using normal approval gates — Phase 8 is diagnostic, not a content-editing phase.

---

## Priority Order

| # | Phase | Action | Est. time |
|---|---|---|---|
| 0 | Pre-check | Verify all 6 project documents present; confirm G1 amended halt format and G4 step-entry gate active; read `english-writing-rules_v2.txt` and `TVC-reference-prefold-turkmenistan-part1.html` in full **once per session** (rev-18) — subsequent posts in the same session skip this re-read | 5 min (first post in session); ~1 min (subsequent posts) |
| 1 | 1A | Fact & sanity check | 15 min |
| 2 | 1B | Human readability pass | 10 min |
| 3 | 1C | Media, links & embeds inventory (incl. consecutive image scan) | 12 min |
| 4 | 1D | Inline CSS audit | 10 min |
| 5 | 1E | Confirm YouTube template loaded from project file | 2 min |
| 6 | 1F | Summary block audit | 5 min |
| 7 | 1G | Character encoding audit, including every literal `?` character | 8 min |
| 8 | 1H | Repetition scan (full body) | 10 min |
| 9 | 1I | Writing rules audit — existing prose (rev-15) | 10 min |
| 10 | 2 | Confirm URL stub locked | 1 min |
| 11 | 3, Steps 1–14 (incl. 2-F, 9-F, 14A/14B) | Apply content fixes in sequence; writing rules gate applies to entire body at every step touching text; Step 9-F factoid research; Step 14A mechanical check then 14B full read-through | 105 min |
| 12 | 4 | Present modification summary (incl. writing rules compliance for entire body + read-through result), await approval | — |
| 13 | 5 | Generate HTML; run sanity checklist twice using two different methods (Rule G2, hardened) — zero gaps required on both passes | 50 min |
| 14 | 6 | Deliver all 3 deliverables | 5 min |
| 15 | 7A | Publish post, paste deliverables | 10 min |
| 16 | 7B | Add cross-links to related posts | 15 min |
| 17 | 7C | Request indexing; verify after 7–14 days | 5 min |
| 18 | 8 | Whole-blog editorial retrospective — operator-invoked, after a batch/series checkpoint, not per-post | 30–60 min per batch |

---

## Hard Rules Summary

- **Minimum verbosity (Rule G1).** During execution, output only the phase+step indicator. Halt conditions are reported with one-line reason and one-line action. Phase 4 is the only full summary. Deliverables are presented without preamble.
- **Two independent-method verification passes required before delivery (Rule G2, hardened rev-16).** Pass 1 is checklist-driven; Pass 2 re-derives from source artifacts (Phase 1C inventory, 1G audit table, 1H/1I findings, writing rules file, ETR recompute) rather than re-reading the checklist from memory. Any failure at either pass resets the counter to zero and restarts both passes. Single-pass delivery, or two passes using the identical method, is not permitted.
- **No step may begin until the prior step is confirmed complete (Rule G4, rev-17).** Every entry into a new step or pass silently checks that the immediately prior one in the canonical sequence actually produced its required output, resolved any halt it raised, and ran any compliance gate it defines. A gap blocks entry with a halt — it is never silently skipped or backfilled with an unearned PASS. Applies across session breaks: resuming a post mid-workflow re-confirms the last completed step before continuing.
- **Missing project document → STOP.** All six must be present before starting. This includes `english-writing-rules_v2.txt` — if it is missing, no new text may be written. This includes `TVC-reference-prefold-turkmenistan-part1.html` — if it is missing, Step 3 and Phase 1F cannot be executed correctly.
- **`TVC-reference-prefold-turkmenistan-part1.html` is the ground truth for summary block CSS.** Any source post summary block that deviates from it in CSS structure must have its CSS stripped and reapplied from the canonical template in Step 3. Do not rely on memory of the correct CSS — read the reference file.
- **`english-writing-rules_v2.txt` must be loaded once per session, before the first post's Phase 1I and Phase 3 begin (rev-18: session-scoped, not re-read per post).** Applying writing rules from memory without ever having loaded the file is not acceptable; re-reading the unchanged file for every subsequent post in the same session is unnecessary and is no longer required. Every existing-prose finding (1I) and every piece of newly written text, on every post in the session, is still checked against the loaded rules at the step that produces or audits it, and again in the Phase 5 sanity checklist. Re-read the file only if it changes mid-session or a new session begins.
- **Step 14 is mandatory and split into 14A → 14B (rev-18).** 14A (mechanical: pronoun/name consistency, Route at a Glance ↔ H2 correspondence, scoped transition check) must PASS before 14B (holistic read for flow, voice, and naturalness) begins. A post that passes every individual checklist item but reads poorly as a whole is not deliverable. At first execution (before Phase 4), both 14A and 14B run in full. On the generated HTML (before Phase 6 delivery), 14B re-runs in full, but 14A re-runs only its two checks with no equivalent elsewhere in the Phase 5 checklist (Route at a Glance ↔ H2 correspondence; place/vehicle name spelling) — narrator-pronoun and transition-scan re-checks are intentionally skipped as confirmed redundant with other checklist items.
- **URL stub is frozen.** Never propose, suggest, or output a modified slug. Live post URLs cannot change.
- **`<!--more-->` is mandatory, exactly once.** Position: after ld+json `</script>`, before map/body.
- **Everything above `<!--more-->` is the index preview.** Hero image, intro paragraphs, summary block, and schema all live here.
- **Schema must include the `author` field on every post (rev-14).** `@type: Person`, `name: "The Vagabond Couple"`, `sameAs: "https://thevagabondcouple.blogspot.com/"` — exact and constant across the series. Add if missing; never fabricate additional credentials.
- **Summary block is mandatory.** Create it if absent. Always strip existing CSS and reapply the canonical template from Step 3 — never blindly preserve source CSS, which may produce visual defects. It is the sole exemption to the hex-color rule.
- **Summary block "What's Covered" rows = top-level H2 sections only.** Not H3 or H4.
- **All media, links, and embeds are 100% retained.** The Phase 1C inventory is the non-negotiable verification checklist.
- **All existing `href` values are preserved exactly.** No URL normalization, query reordering, fragment removal, entity re-encoding, or guessed canonical replacement is allowed. Only approved `?m=1` cleanup on internal Blogspot links or Phase 4-approved broken-link correction may change an existing `href`.
- **`tr-caption-container` table structure is sacred.** Never convert to `<figure>`, `<figcaption>`, or any other format.
- **All YouTube embeds use the project template file verbatim** — existing and new. Re-emit pre-existing embeds in the correct format.
- **YouTube embed wrapper div inline styles are exempt from stripping.** They are structural, not decorative.
- **No hardcoded colors in new elements.** Summary block is the sole exception.
- **Phase 3 steps run in order.** Steps 1–5 complete the pre-fold zone first. Steps 6–13 handle the body.
- **No consecutive images.** Any two `tr-caption-container` tables with no intervening prose `<p>` between them is a blocking error. Flag at Phase 1C; fix at Step 13 with researched, non-repetitive separator paragraphs.
- **No repeated facts or near-verbatim phrases anywhere in the post body.** Phase 1H scans all existing prose — not just newly written text. Every 🔴 hard duplicate identified must be resolved at Step 12 by cutting, rewording, or replacing with researched content before delivery.
- **No HTML generation before approval gate (Phase 4).** Mandatory stop.
- **Cross-linking other posts (Phase 7B) is separate from the HTML deliverable.** It happens after publishing.
- **No indexing request before publish.** Phase 7C is the last step.
- **Author voice and tone are preserved, not the only thing exempt from editing (rev-15).** The author's sentence-level style and sense of humor are never normalized away. This is a narrower exemption than "existing prose is untouchable" — original prose is fully in scope for structural, SEO, and Phase 1I writing-rules fixes; only voice/tone is off-limits, subject to the Step 12 override procedure for genuine stylistic exceptions.
- **Character encoding must be verified (Phase 1G).** Every literal `?` character must be audited, not only long `????` runs. Any `?` embedded in a word, place name, road name, caption, `alt=`, `title=`, signage string, or schema value is suspect until classified. Unresolved placeholder text such as `?ol`, `??? TN? ?134`, or `????` is a blocking error equivalent to a broken image link.
- **English Writing Rules apply to the entire post body — original prose and newly written text alike (rev-15).** Read `english-writing-rules_v2.txt` from project knowledge before auditing or writing — do not apply from memory. Phase 1I audits existing prose; Step 12 resolves both 1H repetition and 1I writing-rules findings, using the cut/reword/replace hierarchy. The first body paragraph, Route Summary box, Route at a Glance, Journey significance paragraph, summary block narrative, separator paragraphs, and any Step 12 replacement or fix must all comply: correct narrator pronouns, no forbidden words or phrases (except logged 🟠 voice-exception overrides), no structural tics, no repetition of ideas already in the post body.
- **Title and search description are SEO-primary (rev-16).** The three-waypoint title cap and the 1–2 theme cap on the search description are defaults, not hard ceilings — both may be exceeded when each additional term is an independently high-value search keyword, with the rationale logged at Phase 4. Padding to exploit the exception is forbidden; the bar is real keyword value, not narrative completeness.
- **Section-closing factoids are encouraged but not mandatory per-section (rev-16).** Most top-level H2 sections get a researched, verifiable closing factoid (Step 9-F); skip a section rather than force a weak or duplicative one. No hallucinated facts — ever. Folklore/legend-status facts are allowed only if explicitly framed as such in the text. The labeled "Did you know"-style opener is the sole sanctioned exception to the category-colon ban, used only in Step 9-F, only with explicit operator sign-off at Phase 4, and applied consistently across the whole post (never mixed with the unlabeled style within one post).
- **Phase 8 is a batch-level retrospective, not a per-post phase (rev-16).** Operator-invoked after a series/batch checkpoint. It reads the published posts as a real visitor and editor would, surfaces cross-post and pattern-level issues no per-post phase can see, and ends with an explicit run-again-or-proceed recommendation. If run-again is recommended, it must name the specific workflow change that would have prevented each issue — Phase 8 closes the loop back into this document, it does not just generate one-off fix lists. Phase 8 never edits HTML directly; identified fixes go through Phases 1–7 on the affected post.

---

## Adapting to Other Posts

Only these variables change per post:

| Variable | Locations |
|---|---|
| Origin / destination / waypoints | Title (Step 1), search description (Step 2), first body paragraph (Step 6), Route Summary box (Step 7), Route at a Glance (Step 8), schema (Step 4) |
| Route method | First body paragraph, Route Summary box |
| Summary block label, narrative, table rows | Step 3 — match this post's part number, route, and H2 sections |
| Journey significance connection | Step 10 — Silk Road for relevant posts; broader journey arc otherwise |
| Fact check targets | Phase 1A — all named places, elevations, dates, and claims in this specific post |
| Media inventory counts | Phase 1C — audit each post independently; counts vary |
| Inline CSS patterns found | Phase 1D — patterns may vary by post; do not assume identical to Chandolin–Venice |
| ETR word count | Step 2-F — count final body words after all content additions (Steps 6–13, including 9-F factoids) |
| YouTube video IDs and captions | Phase 1E / Step 11 inventory — specific to each post |
| Cross-link targets | Phase 7B — previous leg, next leg, and thematically related posts |
| Section-closing factoids (rev-16) | Step 9-F — specific to each post's sections; opener-style choice (labeled/unlabeled) is also a per-post operator decision at Phase 4, not a fixed series-wide setting |
| Waypoint count beyond the default-3 cap (rev-16) | Step 1/Step 2 — whether keyword research justifies exceeding the default varies by post; never assume a prior post's waypoint count applies here |

**Retroactive rev-14 gap:** All posts processed under rev-13 or earlier (including China Overland Part 1: Irkeshtam to Kashgar via Wuqia, published 2026-06-21) were delivered without the schema `author` field, since that requirement did not exist yet. These posts are not currently non-compliant with the rev-13 rules they were processed under, but they are inconsistent with rev-14 going forward. Adding the `author` field to already-published posts is a lightweight schema-only edit (no content, CSS, or structural changes) and can be batched in alongside Phase 7B cross-linking work when that phase runs, rather than treated as its own separate pass.

Everything else in this document — document structure, Blogger platform rules, schema format, URL freeze, summary block requirement, `<!--more-->` placement, YouTube template, CSS exemptions, approval gate, sanity checklist, and deliverable format — is constant across all posts.
