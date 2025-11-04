# 🆓 Working Free Models on OpenRouter

## ✅ Confirmed Working Free Models (October 2025)

These models are verified to work with OpenRouter's free tier:

### 1. Microsoft Phi-3 Mini (CURRENT - RECOMMENDED)
```bash
OPENAI_MODEL=microsoft/phi-3-mini-128k-instruct:free
```
- **Size**: 3.8B parameters
- **Context**: 128K tokens
- **Quality**: Good for most tasks
- **Speed**: Fast
- **Rate Limit**: Higher than other free models

### 2. Microsoft Phi-3 Medium
```bash
OPENAI_MODEL=microsoft/phi-3-medium-128k-instruct:free
```
- **Size**: 14B parameters
- **Context**: 128K tokens
- **Quality**: Better reasoning
- **Speed**: Medium

### 3. Meta Llama 3.2 3B
```bash
OPENAI_MODEL=meta-llama/llama-3.2-3b-instruct:free
```
- **Size**: 3B parameters
- **Quality**: Good for simple tasks
- **Speed**: Very fast

### 4. Google Gemma 7B
```bash
OPENAI_MODEL=google/gemma-7b-it:free
```
- **Size**: 7B parameters
- **Quality**: Good
- **Speed**: Medium

### 5. Mistral 7B Instruct
```bash
OPENAI_MODEL=mistralai/mistral-7b-instruct:free
```
- **Size**: 7B parameters
- **Quality**: Excellent
- **Speed**: Medium

### 6. Nous Research Hermes 2 Pro
```bash
OPENAI_MODEL=nousresearch/hermes-2-pro-llama-3-8b:free
```
- **Size**: 8B parameters
- **Quality**: Very good for instruction following
- **Speed**: Medium

---

## ⚠️ Models That DON'T Work (404 Errors)

These model names don't exist or aren't available:
- ❌ `meta-llama/llama-3.1-8b-instruct:free`
- ❌ `meta-llama/llama-3.3-70b-instruct:free`
- ❌ `qwen/qwen-2-7b-instruct:free`
- ❌ `google/gemma-2-9b-it:free`

---

## 🔄 How to Switch Models

### Method 1: Edit .env file
```bash
cd /home/farooqui/Desktop/Docsense/pdf_research_assistant_starter
nano .env  # or use any text editor
```

Change the line:
```bash
OPENAI_MODEL=microsoft/phi-3-mini-128k-instruct:free
```

### Method 2: Quick command line
```bash
echo "OPENAI_MODEL=microsoft/phi-3-medium-128k-instruct:free" >> .env
```

### Method 3: Try multiple models (automatic fallback)
If rate limited on one model, manually switch to another in the list above.

---

## 💡 Rate Limit Strategy

Each free model has **separate rate limits**! 

### Smart Usage:
1. Start with `microsoft/phi-3-mini-128k-instruct:free`
2. If rate limited, switch to `microsoft/phi-3-medium-128k-instruct:free`
3. If still limited, try `meta-llama/llama-3.2-3b-instruct:free`
4. Continue rotating through the list

This gives you **multiple 50 request quotas** across different models!

---

## 🎯 Current Configuration

**Active Model:** `microsoft/phi-3-mini-128k-instruct:free`

**Why Phi-3 Mini?**
- ✅ Fast responses
- ✅ 128K token context window (handles large documents)
- ✅ Good instruction following
- ✅ Reliable availability
- ✅ Lower rate limit pressure than popular models

---

## 📊 Model Comparison

| Model | Size | Speed | Quality | Context | Best For |
|-------|------|-------|---------|---------|----------|
| Phi-3 Mini | 3.8B | ⚡⚡⚡ | ⭐⭐⭐ | 128K | General use |
| Phi-3 Medium | 14B | ⚡⚡ | ⭐⭐⭐⭐ | 128K | Complex tasks |
| Llama 3.2 3B | 3B | ⚡⚡⚡ | ⭐⭐⭐ | 4K | Simple Q&A |
| Gemma 7B | 7B | ⚡⚡ | ⭐⭐⭐⭐ | 8K | Balanced |
| Mistral 7B | 7B | ⚡⚡ | ⭐⭐⭐⭐ | 8K | Reasoning |
| Hermes 2 Pro | 8B | ⚡⚡ | ⭐⭐⭐⭐ | 8K | Instructions |

---

## 🚀 Application Status

**After restart, your app will use:**
- Model: `microsoft/phi-3-mini-128k-instruct:free`
- Fresh rate limits
- All optimizations active

**Test it at:** http://localhost:8501

---

## 🔍 How to Verify Model Works

After restart, check the terminal logs:
```
✓ Document Mode initialized with model: microsoft/phi-3-mini-128k-instruct:free
```

If you see a **404 error**, the model name is wrong.  
If you see a **429 error**, you hit the rate limit.

---

## 📝 Quick Reference Commands

### Restart App
```bash
pkill -f "streamlit run app.py"
cd /home/farooqui/Desktop/Docsense/pdf_research_assistant_starter
source venv/bin/activate
streamlit run app.py
```

### Check Current Model
```bash
grep "OPENAI_MODEL=" .env
```

### Change Model Quickly
```bash
sed -i 's/OPENAI_MODEL=.*/OPENAI_MODEL=microsoft\/phi-3-medium-128k-instruct:free/' .env
```

---

*Last Updated: 2025-10-23 16:40*  
*Current Model: microsoft/phi-3-mini-128k-instruct:free*
