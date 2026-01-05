# API Key Registration Guide

Follow these steps to register for free API keys to enable all LLUT connectors.

## Step 1: Congress.gov API Key (2-3 minutes)

### Registration Process

1. **Open the registration page**:

   - URL: https://api.congress.gov/sign-up/

2. **Fill out the form**:

   - First Name
   - Last Name
   - Email Address
   - Organization (optional)
   - Agree to Terms of Service

3. **Submit the form**

4. **Check your email**:

   - You should receive an email with your API key within a few minutes
   - Subject: "Your api.data.gov API key"
   - The key will be a long string (e.g., "abc123def456...")

5. **Copy your API key** - you'll need it in Step 3

### API Details

- **Rate Limit**: 5,000 requests per hour
- **Cost**: FREE forever
- **Access**: Bills, Resolutions, Amendments, Summaries
- **Documentation**: https://api.congress.gov/

---

## Step 2: GovInfo API Key (2-3 minutes)

### Registration Process

1. **Open the registration page**:

   - URL: https://api.data.gov/signup/
   - (This is the shared api.data.gov registration that works for GovInfo)

2. **Fill out the form**:

   - First Name
   - Last Name
   - Email Address
   - Website (optional - can leave blank or put "localhost")
   - How will you use the API? (can put "Legal document research")
   - Agree to Terms of Service

3. **Submit the form**

4. **Check your email immediately**:

   - You should receive an email instantly
   - Subject: "Your api.data.gov API key"
   - The key will be a 40-character string

5. **Copy your API key** - you'll need it in Step 3

### API Details

- **Rate Limit**: Generous (hourly limits)
- **Cost**: FREE forever
- **Access**: Federal Register, CFR, Bills, Statutes, Court Opinions
- **Bonus**: Same key works for many federal APIs
- **Documentation**: https://api.govinfo.gov/docs/

---

## Step 3: Add API Keys to LLUT

Once you have both API keys, you have three options to add them:

### Option A: Via API (Recommended - Instant)

Open a terminal and run:

```bash
curl -X POST http://localhost:8000/api/settings \
  -H "Content-Type: application/json" \
  -d '{
    "settings": {
      "sources": {
        "congress_gov": {
          "enabled": true,
          "api_key": "YOUR_CONGRESS_API_KEY_HERE",
          "poll_interval_minutes": 1440
        },
        "govinfo": {
          "enabled": true,
          "api_key": "YOUR_GOVINFO_API_KEY_HERE",
          "poll_interval_minutes": 1440
        }
      }
    }
  }'
```

**Replace**:

- `YOUR_CONGRESS_API_KEY_HERE` with your Congress.gov API key
- `YOUR_GOVINFO_API_KEY_HERE` with your GovInfo/api.data.gov API key

### Option B: Via Settings File (Manual)

1. Open: `app_data/settings.json`
2. Find the `sources` section
3. Update the API keys:

```json
{
  "sources": {
    "congress_gov": {
      "enabled": true,
      "api_key": "YOUR_CONGRESS_API_KEY_HERE",
      "poll_interval_minutes": 1440
    },
    "govinfo": {
      "enabled": true,
      "api_key": "YOUR_GOVINFO_API_KEY_HERE",
      "poll_interval_minutes": 1440
    }
  }
}
```

4. Save the file
5. Reload settings (backend will auto-reload on next request)

### Option C: Via Settings UI (When Frontend is Ready)

1. Open LLUT desktop app
2. Navigate to Settings
3. Enter API keys in the form
4. Click Save

---

## Step 4: Test the Connectors

### Test Congress.gov

```bash
curl -X POST http://localhost:8000/api/sync/run \
  -H "Content-Type: application/json" \
  -d '{"sources":["congress_gov"]}'
```

**Expected Result**:

```json
{
  "success": true,
  "job_id": "...",
  "message": "Sync job started"
}
```

Check status:

```bash
curl "http://localhost:8000/api/sync/status"
```

Should show bills being synced.

### Test GovInfo

```bash
curl -X POST http://localhost:8000/api/sync/run \
  -H "Content-Type: application/json" \
  -d '{"sources":["govinfo"]}'
```

**Expected Result**: Same as above, should sync Federal Register documents, CFR updates, etc.

### Test All Sources

```bash
curl -X POST http://localhost:8000/api/sync/run \
  -H "Content-Type: application/json" \
  -d '{"sources":null}'
```

This will sync from all 4 sources!

### Search All Documents

```bash
curl "http://localhost:8000/api/search?q=bill&limit=10"
```

Should return results from Congress.gov bills.

```bash
curl "http://localhost:8000/api/search?q=regulation&limit=10"
```

Should return results from Federal Register and CFR.

---

## Troubleshooting

### "API key is invalid"

- Double-check you copied the entire key (no extra spaces)
- Make sure you're using the right key for the right service
- Check your email for the correct key

### "Rate limited"

- Wait a few minutes
- Check your usage at api.data.gov (for GovInfo)
- Congress.gov: 5,000 requests/hour should be plenty for normal use

### "401 Unauthorized"

- API key not set correctly
- Try restarting the backend
- Verify settings.json has the keys

### "No documents found"

- Check that the source is enabled in settings
- Verify the date range (connectors look back 30-90 days)
- Check sync status for errors

---

## Success Checklist

After registration and setup, verify:

- [ ] Received Congress.gov API key via email
- [ ] Received GovInfo API key via email
- [ ] Updated settings with both keys
- [ ] Tested Congress.gov sync (should find bills)
- [ ] Tested GovInfo sync (should find documents)
- [ ] Searched database and found new documents
- [ ] All 4 connectors now working

---

## What You'll Get

Once both API keys are registered:

### Congress.gov Access

- Current and recent Congressional bills
- Bill summaries and actions
- Amendments
- Resolutions
- Committee reports

### GovInfo Access

- Code of Federal Regulations (CFR)
- Federal Register documents
- US Statutes at Large
- Congressional Bills (alternative source)
- Supreme Court opinions (alternative to web scraping)
- Congressional hearings
- Presidential documents



---