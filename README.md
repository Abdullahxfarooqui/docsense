````markdown
# 📚 PDF Research Assistant

A **production-grade, modular PDF Research Assistant** web application built with Streamlit, LangChain, ChromaDB, and OpenAI GPT-4. This application provides a professional interface for uploading PDF documents, processing them into a vector database, and asking natural language questions with AI-powered answers that include proper source citations.

## ✨ Features

### 🔍 **Core Functionality**
- **Multi-file PDF Upload**: Upload up to 5 PDF files simultaneously (max 50MB total)
- **Intelligent Text Processing**: Robust text extraction with paragraph preservation
- **Smart Chunking**: Overlapping text segments with optimal size for embeddings
- **Vector Search**: Semantic similarity search using ChromaDB vector database
- **AI-Powered Q&A**: GPT-4 generated answers with explicit source citations
- **Source Transparency**: Toggle to show/hide source chunks with similarity scores

### 🎨 **Professional UI/UX**
- **Modern Design**: Clean, responsive interface with professional styling
- **Real-time Feedback**: Progress bars, spinners, and status messages
- **Error Handling**: Graceful error management with user-friendly messages
- **Accessibility**: Keyboard navigation and screen reader support
- **Mobile Responsive**: Works seamlessly on desktop, tablets, and mobile devices

### ⚡ **Performance & Reliability**
- **Caching**: Intelligent caching of embeddings and query results
- **Session Management**: Persistent state across user interactions
- **Retry Logic**: Automatic retries for API calls with exponential backoff
- **Memory Optimization**: Efficient handling of large documents and embeddings
- **Error Recovery**: Robust error handling with detailed logging

### 🔒 **Security & Best Practices**
- **Environment Variables**: Secure API key management
- **Input Validation**: Comprehensive file and input validation
- **Safe Dependencies**: Using official, verified package versions
- **PEP8 Compliance**: Clean, maintainable code following Python standards
- **Type Safety**: Comprehensive type hints throughout the codebase

## 🛠️ **Technical Architecture**

### **Modular Design**
- **`app.py`**: Main Streamlit application with UI and user interaction logic
- **`ingestion.py`**: PDF processing, text extraction, chunking, and embedding generation
- **`query_engine.py`**: Vector search, context preparation, and LLM-based answer generation

### **Technology Stack**
- **Frontend**: Streamlit with custom CSS styling
- **Backend**: Python 3.10+ with comprehensive error handling
- **AI/ML**: OpenAI GPT-4 and text-embedding-ada-002
- **Vector Database**: ChromaDB with persistent storage
- **Document Processing**: PyMuPDF for robust PDF text extraction
- **Text Processing**: LangChain for intelligent chunking and embedding management

## 🚀 **Quick Start**

### **Prerequisites**
- Python 3.10 or higher
- OpenAI API key
- Git (for cloning the repository)

### **Installation**

1. **Clone the repository**:
```bash
git clone <repository-url>
cd pdf_research_assistant_starter
```

2. **Create and activate a virtual environment**:
```bash
# Create virtual environment
python3 -m venv venv

# Activate virtual environment
# On macOS/Linux:
source venv/bin/activate
# On Windows:
venv\Scripts\activate
```

3. **Install dependencies**:
```bash
pip install -r requirements.txt
```

4. **Set up environment variables**:

Create a `.env` file in the project root or set environment variables directly:

```bash
# Option 1: Using .env file (recommended)
echo "OPENAI_API_KEY=your_api_key_here" > .env

# Option 2: Direct environment variable
# macOS/Linux:
export OPENAI_API_KEY="your_api_key_here"
# Windows:
set OPENAI_API_KEY="your_api_key_here"
```

5. **Run the application**:
```bash
streamlit run app.py
```

6. **Access the application**:
Open your web browser and navigate to `http://localhost:8501`

## 📖 **Usage Guide**

### **Step 1: Upload Documents**
1. Use the sidebar file uploader to select up to 5 PDF files
2. Ensure total file size doesn't exceed 50MB
3. View upload validation and file information
4. Click "🚀 Process Documents" to begin ingestion

### **Step 2: Processing**
1. Watch the real-time progress as documents are processed
2. Text is extracted, chunked, and converted to embeddings
3. All data is stored in the local ChromaDB vector database
4. Processing completion is confirmed with statistics

### **Step 3: Ask Questions**
1. Enter your question in natural language
2. Click "🔍 Ask" to search and generate an answer
3. Receive AI-generated answers with source citations
4. Optionally view source chunks with similarity scores

### **Step 4: Manage Session**
1. Toggle source chunk visibility in the sidebar
2. View vector store statistics and status
3. Clear vector store or reset entire session as needed
4. Upload new documents to replace or add to existing ones

## 🔧 **Configuration Options**

### **Environment Variables**
- `OPENAI_API_KEY`: Your OpenAI API key (required)

### **Application Constants** (configurable in source code)
- `MAX_FILES = 5`: Maximum number of uploadable files
- `MAX_TOTAL_SIZE_MB = 50`: Maximum total upload size in MB
- `CHUNK_SIZE = 1000`: Text chunk size in characters
- `CHUNK_OVERLAP = 100`: Overlap between consecutive chunks
- `TOP_K_RESULTS = 3`: Number of relevant chunks to retrieve

### **Model Configuration**
- **LLM Model**: GPT-4 (configurable in `query_engine.py`)
- **Embedding Model**: text-embedding-ada-002
- **Temperature**: 0.1 (low for consistent answers)

## 🏗️ **Development**

### **Project Structure**
```
pdf_research_assistant_starter/
├── app.py                 # Main Streamlit application
├── ingestion.py          # PDF processing and vector storage
├── query_engine.py       # Search and answer generation
├── requirements.txt      # Python dependencies
├── README.md            # This documentation
├── .env                 # Environment variables (create this)
├── .chromadb/           # ChromaDB vector database (auto-created)
└── venv/               # Virtual environment (auto-created)
```

### **Code Standards**
- **Type Hints**: Comprehensive type annotations throughout
- **Docstrings**: Detailed function and class documentation
- **Error Handling**: Robust exception handling with custom exceptions
- **Logging**: Structured logging for debugging and monitoring
- **PEP8**: Python code style guide compliance

### **Adding Features**
1. **New File Formats**: Extend `ingestion.py` to support DOCX, TXT, etc.
2. **Advanced Search**: Add filters, date ranges, or metadata search
3. **Export Functionality**: Add PDF export of Q&A sessions
4. **User Authentication**: Integrate user management and document isolation
5. **Cloud Storage**: Add support for cloud-based vector stores

## 🐛 **Troubleshooting**

### **Common Issues**

**1. "OPENAI_API_KEY environment variable is not set"**
- Ensure you've set the OpenAI API key as described in the setup instructions
- Restart the application after setting the environment variable

**2. "No relevant documents found for your question"**
- Check that documents have been successfully processed
- Try rephrasing your question
- Ensure your question relates to the content of uploaded documents

**3. "Upload size too large"**
- Reduce the total size of uploaded files to under 50MB
- Consider splitting large PDFs into smaller files

**4. "Failed to extract text from PDF"**
- Ensure PDFs are not password-protected or corrupted
- Try re-uploading the file or using a different PDF

### **Performance Optimization**
- **Large Documents**: For very large document collections, consider increasing chunk overlap
- **Slow Responses**: Check your internet connection and OpenAI API status
- **Memory Issues**: Restart the application if processing very large files

### **Logging and Debugging**
- Check the terminal/console for detailed error messages
- Enable debug logging by modifying the logging level in the source code
- Use Streamlit's built-in error reporting for UI issues

## 📄 **License**

This project is provided as-is for educational and commercial use. Please ensure compliance with OpenAI's terms of service when using their APIs.

## 🤝 **Contributing**

Contributions are welcome! Please follow these guidelines:
1. Follow the existing code style and standards
2. Add comprehensive tests for new features
3. Update documentation for any changes
4. Ensure all dependencies are properly specified

## 📞 **Support**

For issues, questions, or feature requests:
1. Check the troubleshooting section above
2. Review the application logs for detailed error messages
3. Ensure all dependencies are correctly installed
4. Verify your OpenAI API key is valid and has sufficient credits

## 🚀 **Deployment**

### **Local Deployment**
The application is ready to run locally following the installation instructions above.

### **Cloud Deployment**
This application can be deployed on various cloud platforms:

- **Streamlit Cloud**: Direct deployment from GitHub repository
- **Heroku**: Use the provided `requirements.txt` and add a `Procfile`
- **Docker**: Create a Dockerfile for containerized deployment
- **AWS/GCP/Azure**: Deploy on cloud virtual machines or container services

### **Production Considerations**
- Use environment-specific API keys and configuration
- Implement proper logging and monitoring
- Consider using a managed vector database for scalability
- Add authentication and user management for multi-user scenarios
- Implement rate limiting and usage quotas

---

**Built with ❤️ using Streamlit, LangChain, and OpenAI**
````