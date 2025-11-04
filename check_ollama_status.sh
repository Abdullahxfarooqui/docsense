#!/bin/bash
# Quick status check for Ollama integration

echo "===================================="
echo "🔍 OLLAMA STATUS CHECK"
echo "===================================="
echo ""

echo "1️⃣ Ollama Service Status:"
if ps aux | grep -v grep | grep "ollama serve" > /dev/null; then
    echo "   ✅ Ollama service is running"
else
    echo "   ❌ Ollama service is NOT running"
    echo "   Run: ollama serve &"
fi
echo ""

echo "2️⃣ Model Download Status:"
if ps aux | grep -v grep | grep "ollama pull" > /dev/null; then
    echo "   ⏳ Model download in progress..."
    echo "   Please wait a few more minutes"
else
    echo "   ✅ No active downloads"
fi
echo ""

echo "3️⃣ Available Models:"
ollama list
echo ""

echo "4️⃣ Configuration (.env):"
cd /home/farooqui/Desktop/Docsense/pdf_research_assistant_starter
echo "   Base URL: $(grep OPENAI_BASE_URL .env)"
echo "   Model: $(grep OPENAI_MODEL .env | head -1)"
echo ""

echo "5️⃣ Next Steps:"
if ollama list | grep -q "llama3.2:3b"; then
    echo "   ✅ Model ready! You can:"
    echo "   1. Test: ollama run llama3.2:3b 'Hello'"
    echo "   2. Restart app: pkill -f streamlit && streamlit run app.py"
else
    echo "   ⏳ Wait for download to complete"
    echo "   Check again in 2-3 minutes with: bash check_ollama_status.sh"
fi
echo ""
echo "===================================="
