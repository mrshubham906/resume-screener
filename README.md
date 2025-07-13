# Resume Screener Microservice

A powerful backend microservice that accepts candidate resumes in PDF format, parses them, stores structured data, and allows querying for the best matches based on job descriptions using OpenAI embeddings and vector search.

## Features

- **AI-Powered Resume Parsing**: Uses OpenAI GPT to extract structured data from PDF resumes (skills, experience, education, contact info)
- **Vector Search**: Use OpenAI embeddings for semantic similarity search
- **Async Processing**: Redis + Celery for background task processing
- **MongoDB Storage**: Store resume metadata and parsed content
- **Pinecone Integration**: Vector database for similarity search
- **RESTful API**: FastAPI-based endpoints for upload and search
- **Docker Support**: Complete containerized setup
- **Authentication**: API key-based authentication

## Architecture

```
┌─────────────┐    ┌─────────────┐    ┌─────────────┐
│   FastAPI   │    │    Redis    │    │   Celery    │
│   (API)     │◄──►│   (Queue)   │◄──►│  (Worker)   │
└─────────────┘    └─────────────┘    └─────────────┘
       │                   │                   │
       ▼                   ▼                   ▼
┌─────────────┐    ┌─────────────┐    ┌─────────────┐
│  MongoDB    │    │  Pinecone   │    │   OpenAI    │
│ (Metadata)  │    │ (Vectors)   │    │ (Embeddings)│
└─────────────┘    └─────────────┘    └─────────────┘
```

## Quick Start

### Prerequisites

- Python 3.12+
- Docker and Docker Compose
- OpenAI API key (with access to gpt-4o-2024-08-06 model)
- Pinecone API key
- OpenAI Python SDK 1.50.0+

### Python Version

This project is optimized for Python 3.12. All dependencies have been updated to their latest versions that support Python 3.12. If you're using a different Python version, you may need to adjust the requirements.txt file.

### Setup

1. **Clone the repository**
   ```bash
   git clone <repository-url>
   cd resume-screener
   ```

2. **Configure environment variables**
   ```bash
   cp env.example .env
   # Edit .env with your API keys
   ```

3. **Start the services**
   ```bash
   docker-compose up -d
   ```

4. **Access the API**
   - API Documentation: http://localhost:8000/docs
   - Health Check: http://localhost:8000/health

## OpenAI Resume Parser with Structured Output

The resume parser now uses OpenAI's structured output model to intelligently extract structured information from PDF resumes. This approach provides several advantages over traditional regex-based parsing and JSON parsing:

### Key Benefits

- **Intelligent Understanding**: GPT understands context and can extract information even from complex resume formats
- **Flexible Format Support**: Works with various resume layouts and structures
- **Accurate Skill Extraction**: Identifies technical skills and technologies more accurately
- **Structured Data**: Extracts experience, education, and contact information in a structured format
- **Type Safety**: Uses Pydantic models for guaranteed data structure and validation
- **Reliable Parsing**: No more JSON parsing errors or malformed responses
- **Fallback Mechanism**: Includes basic regex fallback if OpenAI API is unavailable

### How It Works

1. **PDF Text Extraction**: Uses `pdfplumber` and `PyPDF2` to extract raw text from PDF
2. **Structured Output Processing**: Sends the extracted text to OpenAI with Pydantic model schema
3. **Type-Safe Response**: Receives validated structured data including:
   - Skills list
   - Work experience (company, position, duration, description)
   - Education (degree, institution, year)
   - Contact information (email, phone, LinkedIn)
   - Professional summary

### Structured Output Models

The parser uses Pydantic models for type-safe data extraction:

```python
class ContactInfo(BaseModel):
    email: Optional[str] = None
    phone: Optional[str] = None
    linkedin: Optional[str] = None

class ExperienceOutput(BaseModel):
    company: str
    position: str
    duration: str
    description: str

class EducationOutput(BaseModel):
    degree: str
    institution: str
    year: Optional[str] = None

class ResumeStructuredOutput(BaseModel):
    skills: List[str]
    experience: List[ExperienceOutput]
    education: List[EducationOutput]
    contact_info: ContactInfo
    summary: str
```

### Testing the Parser

You can test the structured output parser using the provided test script:

```bash
# Set your OpenAI API key
export OPENAI_API_KEY="your-openai-api-key-here"

# Run the test script
python test_structured_output.py
```

This will test the structured output functionality with a sample resume and show you the extracted data.

### Configuration

The parser uses the following configuration in `app/config.py`:

```python
openai_api_key: str = "your-openai-api-key-here"
openai_parsing_model: str = "gpt-4o-2024-08-06"  # Model for structured output parsing
openai_model: str = "text-embedding-ada-002"  # Model for embeddings
```

**Note**: The structured output feature requires OpenAI API version 1.50.0+ and the `gpt-4o-2024-08-06` model or newer.

## API Endpoints

### Authentication

All endpoints require an API key in the header:
```
X-API-Key: your-api-key-here
```

### 1. Upload Resume

**POST** `/upload/resume`

Upload a PDF resume for processing.

```bash
curl -X POST "http://localhost:8000/upload/resume" \
  -H "X-API-Key: your-api-key" \
  -F "file=@resume.pdf"
```

**Response:**
```json
{
  "id": "64f8a1b2c3d4e5f6a7b8c9d0",
  "filename": "resume.pdf",
  "status": "processing",
  "message": "Resume uploaded successfully and queued for processing",
  "upload_date": "2024-01-15T10:30:00Z"
}
```

### 2. Get Upload Status

**GET** `/upload/status/{resume_id}`

Get the processing status of a resume.

```bash
curl -X GET "http://localhost:8000/upload/status/64f8a1b2c3d4e5f6a7b8c9d0" \
  -H "X-API-Key: your-api-key"
```

**Response:**
```json
{
  "id": "64f8a1b2c3d4e5f6a7b8c9d0",
  "filename": "resume.pdf",
  "status": "processed",
  "upload_date": "2024-01-15T10:30:00Z",
  "processing_time": 3.2
}
```

### 3. Search Resumes

**POST** `/search/`

Search for resumes matching a job description.

```bash
curl -X POST "http://localhost:8000/search/" \
  -H "X-API-Key: your-api-key" \
  -H "Content-Type: application/json" \
  -d '{
    "job_description": "We are looking for a Python developer with experience in FastAPI, MongoDB, and machine learning. The ideal candidate should have 3+ years of experience in backend development and be familiar with Docker and cloud deployment.",
    "top_k": 5,
    "min_similarity": 0.7
  }'
```

**Response:**
```json
{
  "matches": [
    {
      "id": "64f8a1b2c3d4e5f6a7b8c9d0",
      "filename": "john_doe_resume.pdf",
      "similarity_score": 0.89,
      "skills": ["Python", "FastAPI", "MongoDB", "Docker"],
      "experience_years": 4,
      "summary": "Senior Python developer with 4 years of experience...",
      "upload_date": "2024-01-15T10:30:00Z"
    }
  ],
  "total_matches": 1,
  "search_time": 0.45,
  "query": "We are looking for a Python developer..."
}
```

### 4. Get Resume Details

**GET** `/resumes/{id}`

Fetch detailed information about a specific resume.

```bash
curl -X GET "http://localhost:8000/resumes/64f8a1b2c3d4e5f6a7b8c9d0" \
  -H "X-API-Key: your-api-key"
```

**Response:**
```json
{
  "id": "64f8a1b2c3d4e5f6a7b8c9d0",
  "filename": "john_doe_resume.pdf",
  "upload_date": "2024-01-15T10:30:00Z",
  "status": "processed",
  "content": {
    "text": "Full extracted text...",
    "skills": ["Python", "FastAPI", "MongoDB", "Docker"],
    "experience": [
      {
        "company": "Tech Corp",
        "position": "Senior Developer",
        "duration": "2020-2024",
        "description": "Led backend development..."
      }
    ],
    "education": [
      {
        "degree": "BS Computer Science",
        "institution": "University of Technology",
        "year": "2020"
      }
    ]
  },
  "metadata": {
    "file_size": 245760,
    "pages": 2,
    "processing_time": 3.2
  }
}
```

### 5. Health Check

**GET** `/health`

Check service health and dependencies.

```bash
curl -X GET "http://localhost:8000/health"
```

**Response:**
```json
{
  "status": "healthy",
  "timestamp": "2024-01-15T10:30:00Z",
  "dependencies": {
    "mongodb": "connected",
    "redis": "connected",
    "openai": "connected",
    "vector_store": "connected"
  }
}
```

## Configuration

### Environment Variables

Copy `env.example` to `.env` and configure:

```env
# API Configuration
API_KEY=random uuid

# OpenAI Configuration
OPENAI_API_KEY=openai-api-key

# Pinecone Configuration (Vector Database)
PINECONE_API_KEY=pinecone-api-key
PINECONE_ENVIRONMENT=pinecone-reason
PINECONE_INDEX_NAME=pinecone-index-name
```

### Default Configuration

The application uses the following default configuration (from `app/config.py`):

```python
# API Configuration
api_key: str = os.getenv("API_KEY")
debug: bool = False
host: str = "0.0.0.0"
port: int = 8000

# MongoDB Configuration
mongodb_uri: str = "mongodb://localhost:27017/resume_screener"
mongodb_database: str = "resume_screener"

# Redis Configuration
redis_url: str = "redis://localhost:6379/0"

# OpenAI Configuration
openai_api_key: str = os.getenv("OPENAI_API_KEY")
openai_model: str = "text-embedding-ada-002"
openai_parsing_model: str = "gpt-4o-2024-08-06"
openai_chunk_size: int = 1000
openai_chunk_overlap: int = 200

# Pinecone Configuration
pinecone_api_key: Optional[str] = os.getenv("PINECONE_API_KEY")
pinecone_environment: str = os.getenv("PINECONE_ENVIRONMENT")
pinecone_index_name: str = os.getenv("PINECONE_INDEX_NAME")
pinecone_dimension: int = 1536

# Celery Configuration
celery_broker_url: str = "redis://localhost:6379/0"
celery_result_backend: str = "redis://localhost:6379/0"

# File Upload Configuration
max_file_size: int = 10 * 1024 * 1024  # 10MB
allowed_extensions: List[str] = ["pdf"]
upload_dir: str = os.getenv("UPLOAD_DIR", "uploads")

# Security Configuration
cors_origins: List[str] = ["http://localhost:3000", "http://localhost:8080"]
rate_limit_per_minute: int = 60
```

## Development

### Local Development Setup

1. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

2. **Start dependencies**
   ```bash
   docker-compose up -d mongodb redis
   ```

3. **Run the application**
   ```bash
   uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
   ```

4. **Run Celery worker**
   ```bash
   celery -A app.celery_app worker --loglevel=info
   ```

### Project Structure

```
resume-screener/
├── app/
│   ├── __init__.py
│   ├── main.py                 # FastAPI application
│   ├── celery_app.py          # Celery configuration
│   ├── config.py              # Configuration settings
│   ├── models/
│   │   ├── __init__.py
│   │   ├── resume.py          # Resume data models
│   │   └── search.py          # Search request/response models
│   ├── services/
│   │   ├── __init__.py
│   │   ├── parser.py          # PDF parsing service
│   │   ├── embedding.py       # OpenAI embedding service
│   │   ├── vector_store.py    # Vector database operations
│   │   └── database.py        # MongoDB operations
│   ├── api/
│   │   ├── __init__.py
│   │   ├── auth.py            # Authentication middleware
│   │   └── routes/
│   │       ├── __init__.py
│   │       ├── upload.py      # Upload endpoints
│   │       ├── search.py      # Search endpoints
│   │       └── resumes.py     # Resume CRUD endpoints
│   └── tasks/
│       ├── __init__.py
│       └── processing.py      # Celery tasks
├── docker-compose.yml
├── Dockerfile
├── requirements.txt
├── env.example
├── mongo-init.js
└── README.md
```

## Testing

### Run Tests
```bash
pytest tests/
```

### Test API Endpoints
```bash
# Test upload
curl -X POST "http://localhost:8000/upload/resume" \
  -H "X-API-Key: your-api-key" \
  -F "file=@test_resume.pdf"

# Test search
curl -X POST "http://localhost:8000/search/" \
  -H "X-API-Key: your-api-key" \
  -H "Content-Type: application/json" \
  -d '{"job_description": "Python developer", "top_k": 3}'
```

## Performance Considerations

- **Chunking**: Resumes are split into meaningful chunks (skills, experience, education) for better embedding
- **Async Processing**: PDF parsing and embedding generation happen in background
- **Caching**: Redis caches frequently accessed data
- **Batch Processing**: Multiple resumes can be processed concurrently

## Security

- API key authentication for all endpoints
- File upload validation and sanitization
- Rate limiting on API endpoints
- Secure environment variable handling

## Monitoring

- Health check endpoint for service monitoring
- Celery task monitoring via Flower (optional)
- MongoDB and Redis connection monitoring

## Troubleshooting

### Common Issues

1. **Pinecone Connection Error**
   - Verify API key and environment settings
   - Ensure index exists in Pinecone dashboard

2. **MongoDB Connection Error**
   - Check if MongoDB container is running
   - Verify connection string in .env

3. **Celery Worker Not Processing**
   - Ensure Redis is running
   - Check Celery worker logs

4. **PDF Parsing Issues**
   - Verify PDF file is not corrupted
   - Check if PDF is password protected

## Future Work

The following features are planned for future development to enhance the resume screener microservice:

### OCR Integration for Image-Based Resumes
- **Image Processing**: Integrate OCR (Optical Character Recognition) capabilities to extract text from image-based resumes (PNG, JPG, TIFF formats)
- **Multi-Format Support**: Support for scanned documents and screenshots of resumes
- **Text Extraction**: Use advanced OCR libraries like Tesseract or cloud-based OCR services (Google Vision API, AWS Textract)
- **Quality Enhancement**: Implement image preprocessing to improve OCR accuracy
- **Hybrid Processing**: Combine OCR with existing PDF parsing for comprehensive resume processing

### Cloud Storage Integration
- **AWS S3 Integration**: Replace local file storage with AWS S3 for scalable and reliable file management
- **File Upload/Download**: Implement secure file upload to S3 and download capabilities for processed resumes

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests
5. Submit a pull request

## License

MIT License - see LICENSE file for details. 