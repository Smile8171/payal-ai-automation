# Payal AI Automation

Schedules two AI-generated images and one short slideshow video daily for an authorized Facebook Page. A separate job checks recent Page comments every 30 minutes and replies once per comment. The daily job uses recent post engagement to guide creative themes and records scheduled slots to avoid duplicate runs.

## Setup

Install Python 3.12 and FFmpeg, then install dependencies:

```powershell
python -m venv .venv
.venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
Copy-Item .env.example .env
```

Set the environment variables from `.env.example`, then run either job:

```powershell
python publish_daily_content.py
python reply_to_comments.py
```

The daily workflow schedules images for 07:00 and 13:10 and the video for 17:00 in `Asia/Kolkata`. GitHub Actions runs daily at 05:45 India time. Dispatching the daily workflow manually also schedules posts; it does not publish them immediately.

## GitHub Actions secrets

Add these under **Settings > Secrets and variables > Actions**:

- `FB_PAGE_ID`
- `FB_PAGE_ACCESS_TOKEN`
- `POLLINATIONS_API_KEY`
- At least one text provider key: `GEMINI_API_KEY`, `OPENROUTER_API_KEY`, or `OPENAI_API_KEY`

Allow Actions to write repository contents so the jobs can persist duplicate-prevention state. The Page token needs Meta permissions for publishing Page content, reading engagement, and replying to comments. Meta app review may be required.

Comment text is sent to the configured text provider to draft a reply. A fallback reply is used if all text providers fail.

## Safety

Use only a Page you administer and content you are authorized to publish. Test with a non-production Page before enabling real credentials. Never commit `.env`, API keys, Page tokens, app secrets, or private media.
