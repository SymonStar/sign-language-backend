# Deploy to Render - Step by Step

## Step 1: Create Render Account
1. Go to: https://render.com
2. Click "Get Started" or "Sign Up"
3. Sign up with GitHub (recommended) or email
4. Verify your email

## Step 2: Create New Web Service
1. Click "New +" button (top right)
2. Select "Web Service"
3. Choose "Build and deploy from a Git repository"

## Step 3: Connect Repository

**Option A - If you have GitHub:**
1. Push this folder to GitHub
2. Connect your GitHub account to Render
3. Select the repository

**Option B - Without GitHub (Manual Deploy):**
1. On Render dashboard, select "Deploy from Git"
2. Click "Public Git repository"
3. I'll help you create a GitHub repo or use alternative

## Step 4: Configure Service

Fill in these settings:

- **Name:** `sign-language-api` (or any name you want)
- **Region:** Choose closest to you
- **Branch:** `main` (or `master`)
- **Root Directory:** Leave blank
- **Environment:** `Python 3`
- **Build Command:** `pip install -r requirements.txt`
- **Start Command:** `gunicorn app:app`
- **Instance Type:** `Free`

## Step 5: Add Environment Variable (Optional)

If you have Groq API key:
1. Click "Advanced"
2. Add Environment Variable:
   - Key: `GROQ_API_KEY`
   - Value: `your_groq_api_key_here`

## Step 6: Deploy

1. Click "Create Web Service"
2. Wait 5-10 minutes for deployment
3. You'll get a URL like: `https://sign-language-api.onrender.com`

## Step 7: Test Your Deployment

Open browser and go to:
```
https://your-app-name.onrender.com/api/health
```

Should show:
```json
{"status": "ok", "message": "Sign Language API is running"}
```

## Your API URL

Once deployed, your API will be at:
```
https://your-app-name.onrender.com/api/translate
```

Use this URL in your mobile app and PWA!

## Troubleshooting

**If deployment fails:**
- Check logs in Render dashboard
- Make sure all files are uploaded
- Verify requirements.txt has all packages

**If server sleeps:**
- Free tier sleeps after 15 min inactivity
- First request takes 30 sec to wake up
- Upgrade to paid tier ($7/month) for always-on

## Next Steps

1. ✅ Deploy backend to Render
2. ⏭️ Build PWA with your deployed URL
3. ⏭️ Test with phone camera
