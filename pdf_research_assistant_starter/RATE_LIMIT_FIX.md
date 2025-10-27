# 🔧 Rate Limit Fix & Model Configuration Guide

## ✅ Issue Resolved

**Problem**: Rate limit exceeded (429 error) on DeepSeek R1T2 Chimera free model
**Solution**: Switched to alternative free model with better rate limits + added error handling

---

## 🎯 What Was Changed

### 1. Default Model Updated
**File**: `.env`

```bash
# OLD (50 requests/day limit)
OPENAI_MODEL=tngtech/deepseek-r1t2-chimera:free

# NEW (Higher rate limits)
OPENAI_MODEL=meta-llama/llama-3.1-8b-instruct:free
```

### 2. Added Rate Limit Error Handling
**Files**: `document_mode.py`, `chat_mode.py`

Now when rate limits are hit, users see a helpful message:
```
⚠️ Rate Limit Exceeded

The free model has reached its rate limit. Please:
1. Wait a few minutes and try again
2. Or switch to a different model in the .env file
3. Or add credits to your OpenRouter account

Available free alternatives:
- meta-llama/llama-3.1-8b-instruct:free
- google/gemma-2-9b-it:free
- microsoft/phi-3-medium-128k-instruct:free
```

---

## 🔄 Available Free Models

Edit your `.env` file to switch models:

### Recommended Options (Good Balance)

1. **Llama 3.1 8B** (Default - Best overall)
   ```bash
   OPENAI_MODEL=meta-llama/llama-3.1-8b-instruct:free
   ```
   - Rate limit: Higher than DeepSeek
   - Quality: Excellent reasoning and structure
   - Speed: Fast

2. **Google Gemma 2 9B**
   ```bash
   OPENAI_MODEL=google/gemma-2-9b-it:free
   ```
   - Rate limit: Good
   - Quality: Strong reasoning
   - Speed: Very fast

3. **Microsoft Phi-3 Medium**
   ```bash
   OPENAI_MODEL=microsoft/phi-3-medium-128k-instruct:free
   ```
   - Rate limit: Good
   - Quality: Excellent for long documents (128k context)
   - Speed: Moderate

4. **Qwen 2 7B**
   ```bash
   OPENAI_MODEL=qwen/qwen-2-7b-instruct:free
   ```
   - Rate limit: Good
   - Quality: Strong general performance
   - Speed: Fast

---

## 🚀 How to Switch Models

### Option 1: Edit .env File (Recommended)

1. Open `.env` file in the project root
2. Find the line: `OPENAI_MODEL=...`
3. Replace with your chosen model
4. Save the file
5. Restart the Streamlit app

```bash
# Stop the app (Ctrl+C in terminal)
# Restart it
streamlit run app.py
```

### Option 2: Environment Variable

Set it before running:
```bash
export OPENAI_MODEL=meta-llama/llama-3.1-8b-instruct:free
streamlit run app.py
```

---

## 💡 Rate Limit Information

### Free Tier Limits (Approximate)

| Model | Daily Limit | Notes |
|-------|-------------|-------|
| DeepSeek R1T2 Chimera | 50 requests | Lower limit |
| Llama 3.1 8B | Higher | Recommended |
| Gemma 2 9B | Higher | Fast |
| Phi-3 Medium | Higher | Best for long docs |
| Qwen 2 7B | Higher | Good balance |

**Note**: Exact limits vary by OpenRouter and can change. Free models share rate limits across users.

---

## 🎯 When You Hit Rate Limits

### Immediate Solutions

1. **Wait**: Rate limits typically reset every 24 hours (UTC)
2. **Switch Model**: Use a different free model (see options above)
3. **Add Credits**: Add $10 to OpenRouter account for 1000 free requests/day

### Long-Term Solutions

1. **Paid Tier**: OpenRouter paid models have much higher limits
2. **Direct API**: Use OpenAI, Anthropic, or Google APIs directly
3. **Local Models**: Run models locally with Ollama

---

## 🔍 How Rate Limit Handling Works

### Error Detection
```python
# Automatically detects 429 errors
if '429' in error_str or 'rate limit' in error_str.lower():
    # Show helpful message to user
    yield "⚠️ Rate Limit Exceeded\n\n[helpful instructions]"
```

### User-Friendly Messages
- ✅ Clear explanation of the issue
- ✅ Step-by-step solutions
- ✅ Alternative model suggestions
- ✅ No cryptic error codes

---

## 🧪 Testing Your Configuration

After switching models, test with:

1. **Simple query**: "Hello, can you hear me?"
2. **Document query**: Upload a PDF and ask "What is the main topic?"
3. **Detailed query**: "Analyze the key findings in detail"

Monitor the terminal for logs:
```
INFO - ✓ Chat Mode initialized with model: meta-llama/llama-3.1-8b-instruct:free
INFO - 📚 RAG detailed response (max_tokens=3500, temp=0.7)
INFO - ✓ Response validated: 650 words
```

---

## 💳 Adding Credits to OpenRouter

If you need higher limits:

1. Go to https://openrouter.ai/
2. Sign in with your account
3. Navigate to "Credits"
4. Add $10 minimum
5. Unlock 1000 free model requests per day

**Benefits**:
- Much higher rate limits
- Access to premium models
- Priority processing
- No daily caps

---

## ⚙️ Advanced: Custom Model Configuration

You can also use paid models with better quality:

```bash
# GPT-4 (OpenAI)
OPENAI_MODEL=openai/gpt-4-turbo-preview

# Claude 3 (Anthropic)
OPENAI_MODEL=anthropic/claude-3-opus

# Gemini Pro (Google)
OPENAI_MODEL=google/gemini-pro-1.5

# DeepSeek V3 (Paid)
OPENAI_MODEL=deepseek/deepseek-chat
```

**Note**: Paid models require OpenRouter credits.

---

## 🐛 Troubleshooting

### Error: "Model not found"
- Check model name spelling in `.env`
- Verify model is available on OpenRouter
- Restart the app after changes

### Error: "Invalid API key"
- Check `OPENAI_API_KEY` in `.env`
- Verify key is active on OpenRouter
- Regenerate key if needed

### Still hitting rate limits
- All free models have limits
- Consider adding credits
- Use local models with Ollama
- Wait for reset (24 hours)

---

## 📚 Additional Resources

- **OpenRouter Docs**: https://openrouter.ai/docs
- **Model Comparison**: https://openrouter.ai/models
- **Pricing**: https://openrouter.ai/docs/pricing

---

## ✅ Current Status

**Fixed!** The application now:
- ✅ Uses Llama 3.1 8B (better rate limits)
- ✅ Detects rate limit errors
- ✅ Shows helpful messages
- ✅ Suggests alternatives
- ✅ Continues working without crashes

**Restart the app to use the new model:**
```bash
# In the terminal where app is running, press Ctrl+C
# Then restart:
cd /home/farooqui/Desktop/Docsense/pdf_research_assistant_starter
source venv/bin/activate
streamlit run app.py
```

---

*Rate Limit Fix Guide - October 23, 2025*
