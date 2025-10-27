# 🚀 Quick Setup: Groq API (14,400 FREE requests/day!)

## Why Groq Instead of Ollama?

**Ollama installation requires system-level changes** that are having dependency issues on your system.

**Groq is MUCH easier** and gives you:
- ✅ 14,400 requests/day (vs OpenRouter's 50)
- ✅ 2-minute setup (no installation)
- ✅ Very fast responses
- ✅ Free forever
- ✅ Better than most local models

---

## 🎯 Setup Groq (2 Minutes)

### Step 1: Get Your Free API Key

1. Go to: **https://console.groq.com/**
2. Click "Sign Up" or "Log In"
3. Go to "API Keys" section
4. Click "Create API Key"
5. Copy your key (starts with `gsk_...`)

### Step 2: Update Your .env File

Open your `.env` file and change these lines:

```bash
# OLD (OpenRouter - rate limited)
# OPENAI_API_KEY=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
# OPENAI_BASE_URL=https://openrouter.ai/api/v1
# OPENAI_MODEL=meta-llama/llama-3.2-3b-instruct

# NEW (Groq - 14,400 requests/day FREE!)
OPENAI_API_KEY=gsk_YOUR_API_KEY_HERE
OPENAI_BASE_URL=https://api.groq.com/openai/v1
OPENAI_MODEL=llama-3.1-70b-versatile
```

### Step 3: Restart Your App

```bash
pkill -f "streamlit run app.py"
cd /home/farooqui/Desktop/Docsense/pdf_research_assistant_starter
source venv/bin/activate
streamlit run app.py
```

### Step 4: Test!

Go to http://localhost:8501 and start asking questions! 🎉

---

## 📊 Available Groq Models

All FREE with 14,400 requests/day:

### Best for Your RAG System:
```bash
OPENAI_MODEL=llama-3.1-70b-versatile
```
- **Size**: 70B parameters
- **Quality**: Excellent
- **Speed**: Very fast
- **Context**: 8K tokens

### Alternative Models:
```bash
# Faster, smaller
OPENAI_MODEL=llama-3.1-8b-instant

# Good balance
OPENAI_MODEL=mixtral-8x7b-32768

# Best reasoning
OPENAI_MODEL=llama-3.3-70b-versatile
```

---

## ⚡ Why Groq is Perfect for You

| Feature | Groq | OpenRouter Free | Ollama |
|---------|------|-----------------|--------|
| **Requests/Day** | 14,400 | 50 | Unlimited |
| **Setup Time** | 2 min | 2 min | 30+ min |
| **Installation** | None | None | System dependencies |
| **Speed** | Very Fast | Fast | Slow (no GPU) |
| **Quality** | Excellent | Good | Medium |
| **Cost** | FREE | FREE | FREE |
| **Works Now?** | ✅ YES | ❌ Rate limited | ❌ Install failed |

---

## 🔧 If You Still Want Ollama Later

After you're testing successfully with Groq, you can try Ollama again with these instructions:

### Install via Snap (Easier)
```bash
sudo snap install ollama
ollama serve &
ollama pull llama3.2:3b
```

### Or Install via APT
```bash
# Fix your apt sources first
sudo rm /etc/apt/sources.list.d/windsurf.list
sudo apt update
sudo apt install curl -y
curl -fsSL https://ollama.ai/install.sh | sh
```

### Then Configure
```bash
OPENAI_BASE_URL=http://localhost:11434/v1
OPENAI_MODEL=llama3.2:3b
OPENAI_API_KEY=ollama
```

---

## 🎯 RECOMMENDED ACTION NOW

**Use Groq - it's the fastest solution:**

1. ✅ Go to https://console.groq.com/
2. ✅ Sign up (takes 30 seconds)
3. ✅ Get API key
4. ✅ Update `.env` file
5. ✅ Restart app
6. ✅ Start using your RAG system!

You'll have **14,400 requests/day** which is **288x more** than OpenRouter's free tier!

---

## 📝 Quick Commands

### Update .env (after getting Groq API key)
```bash
cd /home/farooqui/Desktop/Docsense/pdf_research_assistant_starter
nano .env  # or use any text editor
```

Change to:
```bash
OPENAI_API_KEY=gsk_your_key_from_groq_here
OPENAI_BASE_URL=https://api.groq.com/openai/v1
OPENAI_MODEL=llama-3.1-70b-versatile
```

### Restart App
```bash
pkill -f "streamlit run app.py"
source venv/bin/activate
streamlit run app.py
```

---

## ✅ What You Get

After setup:
- ✅ 14,400 requests/day (vs 50 with OpenRouter)
- ✅ Very fast responses (Groq is optimized)
- ✅ Excellent 70B model (better than most local models)
- ✅ All your RAG optimizations working
- ✅ No rate limit errors
- ✅ Production-ready system

---

**Get started now:** https://console.groq.com/

Your application is fully ready - it just needs an API key that isn't rate-limited! 🚀
