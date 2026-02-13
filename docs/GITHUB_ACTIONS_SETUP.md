# GitHub Actions Setup Guide – Step by Step

This guide walks you through running the AI News Digest on GitHub Actions so it runs automatically every day at 1:30 PM EST.

---

## Prerequisites

Before starting, you need:

1. **A GitHub account** and your project pushed to a GitHub repository
2. **A cloud PostgreSQL database** (free options: [Supabase](https://supabase.com), [Neon](https://neon.tech))
3. **A Groq API key** – [groq.com](https://console.groq.com)
4. **SMTP credentials** – Gmail App Password or another email service

---

## Part 1: Set Up a Cloud Database

GitHub Actions runs in the cloud and needs a database it can reach from the internet.

### Option A: Supabase (Free)

1. Go to [supabase.com](https://supabase.com) and sign up
2. Click **New Project**
3. Choose a name, password, and region → **Create new project**
4. Wait for the project to be ready
5. Go to **Project Settings** (gear icon) → **Database**
6. Under **Connection string**, select **URI**
7. Copy the connection string (looks like `postgresql://postgres.[project-ref]:[password]@aws-0-[region].pooler.supabase.com:5432/postgres`)
8. Replace `[YOUR-PASSWORD]` with your actual database password
9. Save this URL – you’ll use it as `DATABASE_URL`

### Option B: Neon (Free)

1. Go to [neon.tech](https://neon.tech) and sign up
2. Click **New Project**
3. Choose a name and region → **Create project**
4. On the dashboard, find **Connection string**
5. Copy the connection string (looks like `postgresql://user:password@ep-xxx.region.aws.neon.tech/neondb?sslmode=require`)
6. Save this URL – you’ll use it as `DATABASE_URL`

---

## Part 2: Get Your API Keys and SMTP Credentials

### Groq API Key

1. Go to [console.groq.com](https://console.groq.com)
2. Sign up or log in
3. Go to **API Keys** → **Create API Key**
4. Copy the key (starts with `gsk_...`)

### Gmail App Password (for SMTP)

1. Turn on 2-Step Verification for your Google account
2. Go to [Google Account → Security → App passwords](https://myaccount.google.com/apppasswords)
3. Create an app password for “Mail”
4. Copy the 16-character password

---

## Part 3: Add Secrets to GitHub

1. Open your repository on GitHub
2. Click **Settings**
3. In the left sidebar, under **Security**, click **Secrets and variables** → **Actions**
4. Click **New repository secret**
5. Add each secret one by one:

| Name | Value | Notes |
|------|-------|-------|
| `DATABASE_URL` | Your full Postgres URL | From Supabase or Neon |
| `GROQ_API_KEY` | Your Groq API key | Starts with `gsk_` |
| `SMTP_SERVER` | `smtp.gmail.com` | For Gmail |
| `SMTP_PORT` | `587` | For Gmail |
| `SMTP_USERNAME` | Your Gmail address | e.g. `you@gmail.com` |
| `SMTP_PASSWORD` | Your Gmail App Password | 16-character app password |
| `EMAIL_RECIPIENT` | Where to send the digest | e.g. `you@gmail.com` |

6. For each secret:
   - Click **New repository secret**
   - Enter the **Name** (exactly as in the table)
   - Paste the **Value**
   - Click **Add secret**

---

## Part 4: Push the Workflow to GitHub

1. Make sure the workflow file exists at `.github/workflows/daily-digest.yml`
2. In your project folder, run:

```bash
git add .github/workflows/daily-digest.yml
git add app/run.py
git add docs/GITHUB_ACTIONS_SETUP.md
git commit -m "Add GitHub Actions workflow for daily digest"
git push origin main
```

(Use `master` instead of `main` if that’s your default branch.)

---

## Part 5: Run a Test

1. On GitHub, open your repository
2. Click the **Actions** tab
3. In the left sidebar, click **Daily Digest**
4. Click **Run workflow** (right side)
5. Click the green **Run workflow** button
6. Wait a few seconds, then refresh
7. Click the running workflow (e.g. “Run pipeline”)
8. Click the **run-digest** job to see logs

The job will:

- Scrape articles
- Summarize them
- Curate by your interests
- Send the digest email

---

## Part 6: Check the Schedule

The workflow is set to run **every day at 1:30 PM EST**.

- GitHub Actions uses **UTC**
- 1:30 PM EST = 6:30 PM UTC (18:30)
- The cron expression `30 18 * * *` means: minute 30, hour 18, every day

You can confirm it in **Actions** → **Daily Digest** → the schedule will appear under the workflow name.

---

## Troubleshooting

### “relation 'articles' does not exist”

Tables are created automatically. If you still see this, the database URL may be wrong. Check `DATABASE_URL` in your secrets.

### “Email send failed”

- Confirm all SMTP secrets are correct
- For Gmail, use an App Password, not your normal password
- Check that “Less secure app access” is not required (App Passwords replace this)

### “Connection refused” or “Connection timed out”

- `DATABASE_URL` must point to a cloud database, not `localhost`
- Ensure the database allows connections from the internet (Supabase/Neon do by default)

### Workflow doesn’t run on schedule

- GitHub may delay scheduled runs on free plans
- Check **Actions** → **Daily Digest** for run history
- You can always trigger it manually with **Run workflow**

---

## Summary Checklist

- [ ] Cloud database created (Supabase or Neon)
- [ ] `DATABASE_URL` saved
- [ ] Groq API key obtained
- [ ] Gmail App Password created
- [ ] All 7 secrets added in GitHub
- [ ] Workflow file pushed to the repo
- [ ] Manual test run completed
- [ ] Digest email received
