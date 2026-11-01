# Payal M

Schedules three daily posts to a Facebook Page you administer: lifestyle photos featuring fictional, clearly adult Indian women (25+), plus a hydraulic-press video in the midday slot when video generation is available. If video generation fails or the configured model is unavailable, the midday slot uses a third photo so the daily schedule remains three posts. Posts are scheduled for 07:00, 13:00, and 19:00 in `Asia/Kolkata`.

Photos use Pollinations and can draw broad style/composition guidance from authorized images in `data/reference_images/`. Reference people are not reproduced. Generated subjects are fully clothed and respectfully portrayed; no minors or sexualized content are requested. The hydraulic-press video depicts a simulated test inside a closed safety enclosure, with no people or injuries.

## Local Setup

Install Python 3.12 and dependencies:

```powershell
python -m venv .venv
.venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
Copy-Item .env.example .env
```

Configure `.env` before running the publishing script. It schedules real Page posts; there is no local dry-run command. Review generated content and test carefully before enabling publication.

## GitHub Actions

The scheduled workflow runs daily at 05:45 India time and prepares the three posts for the daily schedule. Scheduled jobs may be delayed. Manual workflow dispatch defaults to a plan-only dry run; disable that input only when you intend to generate and schedule real Page content.

For a single-photo test, leave `dry_run_only` checked and check `test_photo_only`. This generates one café-scene photo and schedules it to publish about 30 minutes later; it skips the regular three-post job. This is a real public Page post, not a private preview. For the regular three-post test, leave `test_photo_only` unchecked and uncheck `dry_run_only`.

Add these repository secrets under **Settings > Secrets and variables > Actions**:

- `FB_PAGE_ID`
- `FB_PAGE_ACCESS_TOKEN`
- `POLLINATIONS_API_KEY`
- At least one text provider: `GEMINI_API_KEY`, `OPENROUTER_API_KEY`, or `OPENAI_API_KEY`
- Optional Gemini fallbacks: `GEMINI_API_KEY_2` and `GEMINI_API_KEY_3`

Optional repository variables: `POLLINATIONS_IMAGE_MODEL` and `POLLINATIONS_VIDEO_MODEL`. The image default is `black-forest-labs/flux.2-klein-4b`; the video default is `google/veo-3.1-fast`. Video generation may require a paid balance and may be unavailable for an account/model. On video-generation failure, the workflow logs the failure and schedules a photo for that slot. Verify model access, pricing, and duration limits before enabling the scheduled workflow.

GitHub Actions needs permission to write repository contents to persist duplicate-prevention state. The Page token needs Page publishing, post/comment reads and replies, and `read_insights` for video views. Meta app review or business verification may be required. Ranking falls back to engagement counts if video insights are unavailable.

Upload only reference photos you own or are authorized to use. They should be suitable for public upload to the image provider. Do not expect generated images to copy a reference person's identity.

## Limitations And Safety

This automation targets Facebook Pages only; it does not publish to Facebook Groups or reply to Group comments. Meta Groups API access is not available for this workflow. No personal-account automation or browser scraping is used.

Comment text is sent to the configured text model to draft a reply. Review automated replies during initial testing. Generated media is not guaranteed to follow prompts, so review output before enabling scheduled publication. Never commit `.env`, API keys, Page tokens, App Secrets, or private reference images. Use only a Page you administer.
