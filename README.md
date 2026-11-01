# Payal M

Automates content for a Facebook Page you administer: two AI-generated hydraulic-press experiment photos and one short vertical video each day. Reference images can guide style. Recent Page engagement is used to inspire new experiments, and scheduled post IDs plus experiment history reduce duplicate posts. A separate workflow checks Page post comments every 30 minutes and replies once per comment.

## Setup

Install Python 3.12 and dependencies:

```powershell
python -m venv .venv
.venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
Copy-Item .env.example .env
```

Configure `.env` before running scripts. These commands can schedule real posts and send real replies; there is no local dry-run mode.

Posts are scheduled for 07:00, 13:00, and 19:00 in `Asia/Kolkata`. GitHub Actions starts the daily job at 05:45 India time; manual dispatch follows the same schedule. Scheduled workflow times can be delayed by GitHub.

## GitHub Secrets

Add under **Settings > Secrets and variables > Actions**:

- `FB_PAGE_ID`
- `FB_PAGE_ACCESS_TOKEN`
- `POLLINATIONS_API_KEY`
- At least one text provider key: `GEMINI_API_KEY`, `OPENROUTER_API_KEY`, or `OPENAI_API_KEY`
- Optional Gemini fallbacks: `GEMINI_API_KEY_2` and `GEMINI_API_KEY_3`

Optional repository variables: `POLLINATIONS_IMAGE_MODEL` and `POLLINATIONS_VIDEO_MODEL`. Video generation consumes Pollen; the default video model may require a paid balance. Check current model prices, access, and supported clip duration before enabling scheduled runs.

GitHub Actions needs permission to write repository contents to persist duplicate-prevention state. The Page token needs Page publishing, post/comment reads and replies, and `read_insights` for video views. Meta app review or business verification may be required. Ranking falls back to likes, comments, and shares if video insights are unavailable.

## Limits And Safety

This automation targets Facebook Pages only. Facebook Group publishing/comment replies are not enabled because Meta restricts Group API access; personal-account automation and browser scraping are not used.

This repository is public. Do not commit credentials, private reference photos, or other sensitive material. Only commit images you are authorized to publish publicly. Use a Page you administer. Generated media is not guaranteed to follow safety prompts, so review output before enabling scheduled publication. Comment text is sent to the configured text model to draft a reply.
