# Mutual Funds RAG Chatbot

A facts-only mutual fund assistant for selected HDFC mutual fund schemes. The system uses a Streamlit frontend and a FastAPI backend with retrieval, guardrails, and source attribution.

## Live Demo

- **Streamlit App**: https://m2-mutualfunds-ragchatbot-myswxfvmxiveywjvcqf9x8.streamlit.app/
- **Backend API**: https://mf-chatbot-api2.onrender.com
- **API Docs**: https://mf-chatbot-api2.onrender.com/docs
- **Health Check**: https://mf-chatbot-api2.onrender.com/api/health

## Architecture

- **Frontend**: Streamlit Community Cloud
- **Backend**: FastAPI deployed on Render
- **LLM**: Groq API
- **Retrieval**: ChromaDB-backed retrieval with API-based embeddings/lightweight fallback
- **Data Refresh**: GitHub Actions data pipeline scheduled daily

## Supported Scope

The assistant is designed to answer factual questions for selected HDFC mutual fund schemes, including:

- Expense ratio
- NAV
- Exit load
- Minimum SIP
- Benchmark
- Risk classification
- Lock-in period
- Fund manager

It does not provide investment advice.

## Local Development

### Backend

```powershell
cd "c:\milestone 2"
uvicorn phase_6.api.main:app --host 0.0.0.0 --port 8002
```

Backend URLs:

- http://localhost:8002/
- http://localhost:8002/api/health
- http://localhost:8002/docs

### Streamlit Frontend

```powershell
cd "c:\milestone 2"
streamlit run streamlit_app/app.py
```

For local frontend-to-backend testing, set Streamlit secret:

```toml
api_base_url = "http://localhost:8002"
```

## Deployment

### Streamlit Cloud

Set the following Streamlit secret:

```toml
api_base_url = "https://mf-chatbot-api2.onrender.com"
```

### Render Backend

Required environment variables:

```text
GROQ_API_KEY=your_groq_key
PORT=8002
PYTHONPATH=/app
CHROMA_DB_PATH=/app/phase_3/vector_db
EMBEDDING_DIM=384
```

Optional hosted embedding API variables:

```text
EMBEDDING_API_PROVIDER=huggingface
EMBEDDING_API_URL=https://api-inference.huggingface.co/pipeline/feature-extraction/BAAI/bge-small-en-v1.5
EMBEDDING_API_KEY=your_huggingface_token
```
