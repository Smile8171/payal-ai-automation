# Payal AI Automation

Schedules two AI-generated images daily for an authorized Facebook Page. Video generation and posting are paused until a genuinely free video provider is available. A separate job checks recent Page comments every 30 minutes and replies once per comment. The daily job uses recent post engagement to guide creative themes and records scheduled slots to avoid duplicate runs.

## Setup

Install Python 3.12 and FFmpeg, then install the dependencies:

```powershell
python -m venv .venv
.venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
Copy-Item .env.example .env
```

Set the environment variables from `.env.example` locally, then run either job:

```powershell
python publish_daily_content.py
python reply_to_comments.py
```

The posting job schedules images for 07:00 and 13:10 in `Asia/Kolkata`. GitHub Actions runs it daily at 05:45 India time and checks comments every 30 minutes. Dispatching the daily workflow manually also schedules posts; it does not publish them immediately.

## GitHub Actions Secrets

Add these under **Settings > Secrets and variables > Actions**:

- `FB_PAGE_ID`
- `FB_PAGE_ACCESS_TOKEN`
- `POLLINATIONS_API_KEY`
- At least one text provider key: `GEMINI_API_KEY`, `OPENROUTER_API_KEY`, or `OPENAI_API_KEY`
- Optional Gemini fallbacks: `GEMINI_API_KEY_2` and `GEMINI_API_KEY_3`

Enable Actions and allow workflows to write repository contents so the jobs can persist duplicate-prevention state. The Page token needs Meta permissions for Page publishing, engagement reads, and comment replies. Meta app review may be required.

Comment text is sent to the configured text provider to draft a reply. The fallback reply is used if all text providers fail.

## Safety

Use only a Page you administer and content you are authorized to publish. Test with a non-production Page before enabling real credentials. Never commit `.env`, API keys, Page tokens, app secrets, or private media.
