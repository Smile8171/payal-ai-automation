# Payal AI Automation

Starter project for automating content on an authorized Facebook Page.

## Intended workflow

- Generate two original images and one short video each day.
- Publish through the Meta Graph API.
- Track published content to reduce duplicates.
- Use engagement data to inform future content.
- Reply to Page comments with short, friendly AI-generated responses.

## Current status

This repository is an initial scaffold, not a production-ready publisher. The current image pipeline creates placeholder variations, and the runner prints a plan rather than publishing it. Do not add production credentials or rely on the scheduled workflow until generation, posting, comment handling, and tests are completed.

## Local setup

```powershell
python -m venv .venv
.venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
Copy-Item .env.example .env
python run.py
```

Use `.env.example` for variable names only. Keep real keys and Page tokens in local environment variables or GitHub Actions secrets, never in committed files.

## Required Meta permissions

The Page access token must be authorized for the Graph API operations the app uses, such as publishing Page content and reading/replying to comments. Meta app review and Page permissions may be required.

## Configuration

See `.env.example`. Configure only credentials for services you actually enable. Never commit `.env`, access tokens, app secrets, or generated private media.
