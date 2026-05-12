# Phase 11: Streamlit Deployment

This Streamlit app provides a chat interface and dashboard for the Mutual Fund FAQ Assistant.

## Local Run

1. Start the FastAPI backend:

```powershell
py -3.12 phase_6\api\main.py
```

2. In a second terminal, run Streamlit:

```powershell
streamlit run streamlit_app/app.py
```

3. Open the Streamlit URL shown in the terminal, usually `http://localhost:8501`.

## Configuration

The app reads the backend API URL from either:

- `API_BASE_URL` environment variable
- `.streamlit/secrets.toml` key `api_base_url`
- fallback: `http://localhost:8002`

Use `.streamlit/secrets.toml.template` as the template for local secrets.

## Streamlit Community Cloud

1. Push this repository to GitHub.
2. Go to `https://share.streamlit.io`.
3. Create a new app and set the main file path to `streamlit_app/app.py`.
4. Add secrets in the Streamlit dashboard, for example:

```toml
api_base_url = "https://your-backend-url.example.com"
```

5. Deploy and verify:

- Chat query flow
- Supported scheme selector
- Feedback buttons
- Backend health display
- Source link display

## Docker Run

```powershell
docker build -t mf-chatbot .
docker run -p 8501:8501 mf-chatbot
```
