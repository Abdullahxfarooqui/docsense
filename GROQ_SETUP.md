# 🚀 Groq API Setup Guide

## Why Groq?
✅ **FREE**: 14,400 requests per day (vs OpenRouter's 50)
✅ **FAST**: 500-800 tokens/second (vs Ollama's 1 token/second on your hardware)
✅ **POWERFUL**: Uses LLaMA 3.1 70B model (much smarter than 3B models)
✅ **No Hardware Requirements**: Runs on Groq's cloud infrastructure

## 🔑 Get Your Free API Key (Takes 2 Minutes)

### Step 1: Visit Groq
1. Open your browser and go to: **https://console.groq.com**
2. Click **"Sign Up"** or **"Get Started"**

### Step 2: Sign Up
1. You can sign up with:
   - Google account (fastest)
   - GitHub account
   - Email

### Step 3: Create API Key
1. Once logged in, you'll see the dashboard
2. Click on **"API Keys"** in the left sidebar
3. Click **"Create API Key"**
4. Give it a name like "DocSense"
5. Click **"Create"**
6. **COPY THE KEY** (it looks like: `gsk_xxxxxxxxxxxxxxxxxxxxxxxxxxxxx`)

### Step 4: Add to Your Application
1. Open the file: `.env` in the pdf_research_assistant_starter folder
2. Find this line: `OPENAI_API_KEY=YOUR_GROQ_API_KEY_HERE`
3. Replace `YOUR_GROQ_API_KEY_HERE` with your actual key
4. Save the file

**Example:**
```env
OPENAI_API_KEY=gsk_abc123xyz456def789ghi012jkl345mno678pqr901
```

### Step 5: Run Your Application
```bash
cd ~/Desktop/Docsense/pdf_research_assistant_starter
source venv/bin/activate
streamlit run app.py
```

## 📊 Performance Comparison

| Feature | Ollama (Your Hardware) | Groq Cloud |
|---------|----------------------|------------|
| Speed | ~1 token/second | ~500-800 tokens/second |
| 700 tokens | ~12 minutes ⏳ | ~1-2 seconds ⚡ |
| Daily Limit | Unlimited | 14,400 requests/day |
| Cost | Free | Free |
| Hardware | Requires powerful PC | Any device |

## ✅ What I Changed

1. **Removed Ollama model** (incompatible with your hardware)
2. **Updated `.env`** to use Groq API
3. **Restored high-quality settings**:
   - Brief responses: 400-600 tokens
   - Detailed responses: 700-1200 tokens
4. **Updated default model** to `llama-3.1-70b-versatile`

## 🎯 Next Steps

1. **Get your Groq API key** from https://console.groq.com
2. **Add it to `.env`** file
3. **Run the app** and enjoy FAST responses! ⚡

## 💡 Tips

- Keep your API key secret (don't share it)
- The free tier gives you 14,400 requests/day
- Groq is 500x faster than Ollama on your hardware
- You'll get research-quality responses in 2-5 seconds instead of 5-20 minutes!

## ❓ Need Help?

If you have any issues:
1. Make sure you copied the full API key (starts with `gsk_`)
2. Check that there are no extra spaces in the `.env` file
3. Restart the application after adding the key
