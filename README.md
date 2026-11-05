# Autonomous AI Job Hunter

A modular, approval-first job discovery and application workspace. It runs locally with SQLite and mock AI mode, and can use Gemini, Telegram, Gmail OAuth, PostgreSQL/Supabase and Playwright when configured.

## Windows setup

```powershell
C:\Users\saikr\Desktop\job-scraper\myenv\Scripts\activate
pip install -r requirements.txt
playwright install chromium
python scripts\initialize_database.py
python main.py --mode test
python main.py --mode status
streamlit run app.py
```

The Windows virtual-environment activation command is `C:\Users\saikr\Desktop\job-scraper\myenv\Scripts\activate`. The included `myenv` is ignored by git and should not be committed.

## Daily commands

```text
python main.py --mode discover  # fetch and deduplicate jobs
python main.py --mode process   # match, generate documents and outreach drafts
python main.py --mode apply     # prepare supported applications; approval remains required by default
python main.py --mode daily     # discovery plus processing
python main.py --mode status
```

Copy `.env.example` to `.env` and keep secrets out of git. Empty API values are valid: Gemini falls back to deterministic profile-grounded matching, Telegram/Gmail stay disabled, and all local database flows remain available.

## Profile and sources

`master_profile.json` is the single source of truth. The dashboard can upload a PDF/DOCX resume and show a conservative extraction proposal. Review it before setting `verified` to `true`; no personal data is invented.

Add public ATS sources to `ats_sources.json`:

```json
[{"type": "greenhouse", "board_token": "example"}, {"type": "lever", "company_slug": "example"}, {"type": "ashby", "board_name": "example"}]
```

Add permitted RSS/JSON sources to `custom_sources.json`. For outreach, add contacts you verified from public sources to `public_contacts.json`; drafts are generated for recruiter, referral and hiring-manager purposes and are never auto-sent by default.

Enable permitted JobSpy searches in `jobspy_sources.json`, for example `{"search_term":"Python Developer","location":"India","sites":["indeed"],"results_wanted":10}`. Each adapter failure is recorded while other sources continue.

## Integrations

- **Gemini:** set `GEMINI_API_KEY`; structured Pydantic responses are validated.
- **Telegram:** create a bot with BotFather and set `TELEGRAM_BOT_TOKEN` and the allow-listed `TELEGRAM_CHAT_ID`.
- **Gmail:** create an OAuth desktop client, set the Gmail variables, complete OAuth to create `storage/gmail_token.json`, and use the draft client. Sending remains opt-in.
- **Cloud database:** set `DATABASE_URL` to PostgreSQL/Supabase. `database/cloud.py` provides private Supabase Storage uploads when `SUPABASE_URL`, `SUPABASE_KEY` and `SUPABASE_STORAGE_BUCKET` are configured. For GitHub Actions, use a persistent database/object-storage service; runner-local SQLite is ephemeral.

## Safety and limitations

The system does not bypass CAPTCHA, MFA, anti-bot controls or authentication. It does not fabricate contact addresses, guess legal/sensitive answers, or claim a submission succeeded without portal evidence. LinkedIn/Indeed/Glassdoor/ZipRecruiter discovery is isolated behind optional JobSpy support and can be disabled when a source restricts access. Unsupported sites are preserved for manual application with generated documents.

## GitHub Actions

`.github/workflows/daily_job_search.yml` runs at 03:30 UTC (09:00 Asia/Kolkata) and supports manual dispatch. Configure repository secrets for the providers you use. For reliable state across runs, configure `DATABASE_URL` with PostgreSQL/Supabase; do not store personal documents or credentials in the repository.

## Checks

```text
python -m compileall -q .
pytest -q
```
