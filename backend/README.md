# SEO Article Writing System - Backend

## Quick Start

```bash
# Create virtual environment
python -m venv venv

# Activate (Windows)
.\venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Run development server
uvicorn app.main:app --reload
```

## Project Structure

```
backend/
├── app/
│   ├── main.py              # FastAPI application entry
│   ├── config.py            # Environment configuration
│   ├── api/v1/              # API routes
│   ├── core/                # Core utilities (security, etc.)
│   ├── services/            # Business logic
│   ├── models/              # SQLAlchemy models
│   ├── schemas/             # Pydantic schemas
│   └── utils/               # Helper functions
├── tests/
├── alembic/                 # Database migrations
├── requirements.txt
└── .env                     # Environment variables (not in git)
```

## Environment Variables

Create a `.env` file with:

```
DATABASE_URL=postgresql://user:password@localhost:5432/seo_db
REDIS_URL=redis://localhost:6379
SECRET_KEY=your-secret-key
GOOGLE_API_KEY=your-google-api-key
GOOGLE_CX_ID=your-google-cx-id
OPENAI_API_KEY=your-openai-api-key
```
