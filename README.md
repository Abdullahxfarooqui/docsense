# DocSense - PDF Research Assistant

A powerful RAG (Retrieval-Augmented Generation) based research assistant that helps you upload, process, and query PDF and text documents using AI.

## 🚀 Features

- **Multi-format Document Support**: Upload PDF and TXT files
- **AI-Powered Question Answering**: Uses DeepSeek API via OpenRouter for intelligent responses
- **Vector Search**: ChromaDB-based semantic search for relevant document chunks
- **Source Citations**: Answers include proper citations with source documents
- **Professional UI**: Clean, accessible Streamlit interface with dark mode support
- **Performance Optimized**: Caching, batch processing, and fast text search
- **Error Handling**: Robust error handling and retry mechanisms

## 🛠️ Technology Stack

- **Frontend**: Streamlit
- **Vector Database**: ChromaDB
- **LLM**: DeepSeek R1T2 Chimera (via OpenRouter)
- **Embeddings**: OpenAI text-embedding-ada-002
- **Document Processing**: PyPDF2, LangChain
- **Backend**: Python 3.12+

## 📋 Prerequisites

- Python 3.12 or higher
- OpenRouter API key (get one at [openrouter.ai](https://openrouter.ai))

## 🔧 Installation

1. **Clone the repository**:
   ```bash
   git clone https://github.com/Abdullahxfarooqui/docsense.git
   cd docsense
   ```

2. **Navigate to the project directory**:
   ```bash
   cd pdf_research_assistant_starter
   ```

3. **Create and activate virtual environment**:
   ```bash
   python3 -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

4. **Install dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

5. **Set up environment variables**:
   - Copy the `.env` file and add your OpenRouter API key:
   ```bash
   OPENAI_API_KEY=your_openrouter_api_key_here
   ```

## 🚀 Running the Application

1. **Start the Streamlit application**:
   ```bash
   streamlit run app.py
   ```

2. **Open your browser** and navigate to `http://localhost:8501`

3. **Upload documents** and start asking questions!

## 📁 Project Structure

```
pdf_research_assistant_starter/
├── app.py                    # Main Streamlit application
├── ingestion.py             # Document processing and vector storage
├── query_engine.py          # Search and answer generation
├── requirements.txt         # Python dependencies
├── .env                     # Environment configuration
├── README.md               # Project documentation
├── venv/                   # Virtual environment (not in git)
└── .chromadb/             # Vector database (not in git)
```

## 🔧 Configuration

The application can be configured through environment variables in the `.env` file:

- `OPENAI_API_KEY`: Your OpenRouter API key
- `OPENAI_MODEL`: Model to use (default: `tngtech/deepseek-r1t2-chimera:free`)
- `MAX_UPLOAD_SIZE_MB`: Maximum file upload size (default: 50MB)
- `CHUNK_SIZE`: Text chunk size for processing (default: 1000)

## 🎯 How It Works

1. **Document Upload**: Users upload PDF or TXT files through the web interface
2. **Text Extraction**: Content is extracted and split into manageable chunks
3. **Vector Storage**: Chunks are embedded and stored in ChromaDB for fast retrieval
4. **Question Processing**: User questions are vectorized and matched against stored chunks
5. **Answer Generation**: DeepSeek API generates contextual answers with proper citations

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add some amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

## 📄 License

This project is licensed under the MIT License - see the LICENSE file for details.

## 🆘 Support

If you encounter any issues or have questions, please [open an issue](https://github.com/Abdullahxfarooqui/docsense/issues) on GitHub.

## 🙏 Acknowledgments

- [OpenRouter](https://openrouter.ai) for API access
- [DeepSeek](https://deepseek.com) for the powerful language model
- [ChromaDB](https://www.trychroma.com) for vector database capabilities
- [Streamlit](https://streamlit.io) for the web framework
