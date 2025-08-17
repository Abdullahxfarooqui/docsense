#!/bin/bash
"""
PDF Research Assistant - Quick Setup Script

This script automates the setup process for the PDF Research Assistant application.
It creates a virtual environment, installs dependencies, and guides you through
the configuration process.

Usage:
    chmod +x setup.sh
    ./setup.sh

Or run directly with bash:
    bash setup.sh
"""

set -e  # Exit on any error

echo "🚀 PDF Research Assistant - Quick Setup"
echo "========================================="
echo ""

# Check if Python 3.10+ is available
echo "📋 Checking Python version..."
python3 --version
python_version=$(python3 -c "import sys; print(f'{sys.version_info.major}.{sys.version_info.minor}')")
required_version="3.10"

if [ "$(printf '%s\n' "$required_version" "$python_version" | sort -V | head -n1)" = "$required_version" ]; then
    echo "✅ Python $python_version is supported"
else
    echo "❌ Python $python_version is not supported. Please install Python 3.10 or higher."
    exit 1
fi

echo ""

# Create virtual environment
echo "🏗️  Creating virtual environment..."
if [ -d "venv" ]; then
    echo "⚠️  Virtual environment already exists. Removing old one..."
    rm -rf venv
fi

python3 -m venv venv
echo "✅ Virtual environment created"

# Activate virtual environment
echo "🔧 Activating virtual environment..."
source venv/bin/activate
echo "✅ Virtual environment activated"

# Upgrade pip
echo "📦 Upgrading pip..."
pip install --upgrade pip

# Install dependencies
echo "📚 Installing dependencies..."
pip install -r requirements.txt
echo "✅ Dependencies installed successfully"

echo ""

# Check for .env file
echo "🔑 Checking environment configuration..."
if [ ! -f ".env" ]; then
    echo "⚠️  No .env file found. Creating from template..."
    cp .env.template .env
    echo "📄 Created .env file from template"
    echo ""
    echo "🔔 IMPORTANT: Please edit the .env file and add your OpenAI API key!"
    echo "   1. Get your API key from: https://platform.openai.com/api-keys"
    echo "   2. Edit .env file and replace 'your_openai_api_key_here' with your actual key"
    echo "   3. Save the file"
    echo ""
    read -p "Press Enter after you've updated the .env file with your API key..."
else
    echo "✅ .env file already exists"
fi

echo ""

# Run installation test
echo "🧪 Running installation tests..."
python test_installation.py

echo ""

# Final instructions
echo "🎉 Setup completed successfully!"
echo ""
echo "📚 Quick Start:"
echo "   1. Activate the virtual environment:"
echo "      source venv/bin/activate"
echo "   2. Start the application:"
echo "      streamlit run app.py"
echo "   3. Open your browser to: http://localhost:8501"
echo ""
echo "📖 For detailed instructions, see README.md"
echo ""
echo "🆘 Need help? Check the troubleshooting section in README.md"

# Ask if user wants to start the app now
echo ""
read -p "🚀 Would you like to start the application now? (y/n): " -n 1 -r
echo ""
if [[ $REPLY =~ ^[Yy]$ ]]; then
    echo "🎬 Starting PDF Research Assistant..."
    streamlit run app.py
fi
