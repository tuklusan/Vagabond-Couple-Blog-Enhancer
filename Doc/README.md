# Blogger Post Rewrite Pipeline

A Python pipeline that:
1. **Logs in** to your Blogger account via OAuth2 (browser-based, token cached)
2. **Finds a post** by title (exact or partial match)
3. **Rewrites the prose** surgically using Claude + your writing rules file
4. **Injects a TravelAction ld+json block** above the `<!-- more -->` jump break
5. **Saves both original and rewritten HTML** locally for review
6. **Waits for your approval** before uploading anything back to Blogger

---

## Setup

### 1. Python dependencies
```bash
pip install google-auth google-auth-oauthlib google-auth-httplib2 \
            google-api-python-client anthropic beautifulsoup4
```

### 2. Google Cloud credentials (`client_secrets.json`)

You need an OAuth2 Desktop App credential from Google Cloud:

1. Go to [Google Cloud Console](https://console.cloud.google.com/)
2. Create or select a project
3. **APIs & Services → Library** → search "Blogger API v3" → Enable it
4. **APIs & Services → OAuth consent screen** → choose **External** → fill in App name + your email → Save
5. **APIs & Services → Credentials** → **Create Credentials → OAuth client ID**
   - Application type: **Desktop app**
   - Name: anything (e.g. "Blogger Pipeline")
6. Click **Download JSON** → rename the file to `client_secrets.json`
7. Place `client_secrets.json` in the same folder as `blogger_pipeline.py`

> **First run:** A browser window will open asking you to log in and grant access.  
> The token is saved to `blogger_token.json` for future runs.

### 3. Anthropic API key
```bash
export ANTHROPIC_API_KEY="sk-ant-..."
```
Or add it to a `.env` file and use `python-dotenv`.

---

## Usage

```bash
# Basic usage (will prompt to choose blog if you have multiple)
python blogger_pipeline.py \
    --title "Three Days in Lisbon" \
    --rules writing_rules.md

# Specify blog ID to skip the selection prompt
python blogger_pipeline.py \
    --title "Three Days in Lisbon" \
    --rules writing_rules.md \
    --blog-id 1234567890123456789

# Skip Claude rewrite — only inject ld+json (e.g. after manual edits)
python blogger_pipeline.py \
    --title "Three Days in Lisbon" \
    --rules my_rules.md \
    --skip-rewrite

# Dry run — process everything, open the file, but never upload
python blogger_pipeline.py \
    --title "Three Days in Lisbon" \
    --rules my_rules.md \
    --dry-run
```

---

## Pipeline Steps in Detail

### Step 1–2: Auth & Post Lookup
- OAuth token is cached in `blogger_token.json` after the first login
- Post search is case-insensitive; if multiple matches are found you'll get a numbered list to choose from

### Step 3: Claude Rewrite
- Claude receives the full post HTML + your rules file
- It rewrites **only prose text** — all tags, classes, images, links, ld+json blocks, and Blogger markup are left intact
- The model used is `claude-sonnet-4-20250514` with 8192 token output

### Step 4: TravelAction ld+json Injection
The script generates a `TravelAction` Schema.org block and inserts it immediately before `<!-- more -->`:

```html
<script type="application/ld+json">
{
  "@context": "https://schema.org",
  "@type": "TravelAction",
  "name": "Post Title",
  "url": "https://yourblog.com/post",
  ...
}
</script>
<!-- more -->
```

Several fields are pre-filled from post metadata (title, URL, published date, labels).  
Fields marked `FILL_IN_*` should be edited in the saved HTML file before approving.

### Step 5: Review
- Two files are saved to `rewritten_posts/`:
  - `PostTitle__TIMESTAMP__ORIGINAL.html` — untouched original
  - `PostTitle__TIMESTAMP__REWRITTEN.html` — the result to review
- The rewritten file opens in your browser automatically

### Step 6: Approval
At the prompt, enter:
- `y` — upload the saved file to Blogger
- `n` — cancel, no changes made
- `edit` — stop here so you can edit the file manually, then re-run with `--skip-rewrite`

> If you edited the HTML file on disk before typing `y`, the script reads the **current file contents** — so your edits are captured.

---

## File Layout

```
.
├── blogger_pipeline.py      ← main script
├── client_secrets.json      ← OAuth credentials (you provide)
├── blogger_token.json       ← cached access token (auto-generated)
├── writing_rules.md         ← your style rules (you provide/edit)
└── rewritten_posts/
    ├── Three_Days_in_Lisbon__20240601_143022__ORIGINAL.html
    └── Three_Days_in_Lisbon__20240601_143022__REWRITTEN.html
```

---

## Troubleshooting

| Problem | Solution |
|---|---|
| `client_secrets.json not found` | Download from Google Cloud Console (see Setup §2) |
| `No blogs found` | Make sure you logged in with the right Google account |
| `Post not found` | Try a shorter or partial title string |
| Claude returns fenced markdown | The script auto-strips ` ```html ` fences |
| Token expired | Delete `blogger_token.json` and re-run to re-authenticate |
| Upload fails with 403 | Your OAuth scope may not include write access — delete token and re-auth |
