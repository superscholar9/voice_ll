# Voice Cloning API Backend

Production-ready FastAPI backend for voice cloning using GPT-SoVITS.

## Features

- **FastAPI Framework**: Modern, fast, async API framework
- **Voice Synthesis**: Integration with GPT-SoVITS for voice cloning
- **API Key Authentication**: Secure endpoint protection
- **CORS Support**: Configurable cross-origin resource sharing
- **Request Validation**: Pydantic models for type safety
- **Error Handling**: Comprehensive error responses
- **Logging**: Structured logging for debugging
- **Health Checks**: Service availability monitoring
- **OpenAPI Documentation**: Auto-generated API docs

## Project Structure

```
backend/
├── app/
│   ├── __init__.py
│   ├── main.py                 # FastAPI application entry point
│   ├── api/
│   │   ├── __init__.py
│   │   └── routes/
│   │       ├── __init__.py
│   │       └── voice.py        # Voice synthesis endpoints
│   ├── core/
│   │   ├── __init__.py
│   │   ├── config.py           # Configuration management
│   │   └── security.py         # Authentication utilities
│   ├── services/
│   │   ├── __init__.py
│   │   └── sovits_client.py    # GPT-SoVITS client
│   └── models/
│       ├── __init__.py
│       └── schemas.py          # Pydantic models
├── requirements.txt
├── .env.example
└── README.md
```

## Prerequisites

- Python 3.9+
- GPT-SoVITS service running on localhost:9880 (or configured URL)
- Virtual environment (recommended)

## Installation

### 1. Create Virtual Environment

**Windows (Conda):**
```bash
conda create -n voice_api python=3.10
conda activate voice_api
```

**Windows (venv):**
```bash
python -m venv venv
venv\Scripts\activate
```

**Linux/Mac:**
```bash
python -m venv venv
source venv/bin/activate
```

### 2. Install Dependencies

```bash
cd backend
pip install -r requirements.txt
```

### 3. Configure Environment

```bash
# Copy example environment file
cp .env.example .env

# Edit .env and set your configuration
# IMPORTANT: Generate a secure API key
python -c "import secrets; print(secrets.token_urlsafe(32))"
```

**Required Configuration:**
- `API_KEY`: Your secure API key for authentication
- `SOVITS_BASE_URL`: GPT-SoVITS service URL (default: http://localhost:9880)

## Running the Server

### Development Mode

```bash
# From backend directory
python -m app.main

# Or using uvicorn directly
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

### Production Mode

```bash
# Set DEBUG=false in .env first
uvicorn app.main:app --host 0.0.0.0 --port 8000 --workers 4
```

The API will be available at:
- API: http://localhost:8000
- Interactive Docs: http://localhost:8000/docs
- ReDoc: http://localhost:8000/redoc

## API Endpoints

### Health Check

```bash
GET /health
```

Returns service health status and GPT-SoVITS availability.

### Voice Synthesis

```bash
POST /api/v1/voice/synthesize
Headers:
  X-API-Key: your-api-key
Form Data:
  text: "Text to synthesize"
  reference_audio: <audio file>
  language: "auto" | "zh" | "en" | "ja"
  speed: 1.0 (0.5-2.0)
  temperature: 0.7 (0.1-1.0)
```

Returns synthesized audio as WAV file.

### Voice Service Health

```bash
GET /api/v1/voice/health
Headers:
  X-API-Key: your-api-key
```

### AI Cover Jobs (Async)

```bash
# Create cover job
POST /api/v1/cover/jobs
Headers:
  X-API-Key: your-api-key
Form Data:
  reference_voice: <audio file>
  song: <audio file>
  model_id: <optional model id>
  pitch_shift: 0 (optional, -24 to 24)

# Query job
GET /api/v1/cover/jobs/{job_id}

# Download result
GET /api/v1/cover/jobs/{job_id}/result

# Cancel job
POST /api/v1/cover/jobs/{job_id}/cancel
```

## Usage Examples

### cURL

```bash
# Synthesize voice
curl -X POST "http://localhost:8000/api/v1/voice/synthesize" \
  -H "X-API-Key: your-api-key" \
  -F "text=Hello, this is a test" \
  -F "reference_audio=@reference.wav" \
  -F "language=en" \
  -F "speed=1.0" \
  -F "temperature=0.7" \
  --output synthesized.wav
```

### Python

```python
import httpx

async def synthesize_voice():
    async with httpx.AsyncClient() as client:
        with open("reference.wav", "rb") as audio_file:
            response = await client.post(
                "http://localhost:8000/api/v1/voice/synthesize",
                headers={"X-API-Key": "your-api-key"},
                files={"reference_audio": audio_file},
                data={
                    "text": "Hello, this is a test",
                    "language": "en",
                    "speed": 1.0,
                    "temperature": 0.7,
                }
            )

        if response.status_code == 200:
            with open("output.wav", "wb") as f:
                f.write(response.content)
```

### JavaScript/TypeScript

```typescript
const formData = new FormData();
formData.append('text', 'Hello, this is a test');
formData.append('reference_audio', audioFile);
formData.append('language', 'en');
formData.append('speed', '1.0');
formData.append('temperature', '0.7');

const response = await fetch('http://localhost:8000/api/v1/voice/synthesize', {
  method: 'POST',
  headers: {
    'X-API-Key': 'your-api-key',
  },
  body: formData,
});

const audioBlob = await response.blob();
```

## Configuration

### Environment Variables

| Variable | Description | Default |
|----------|-------------|---------|
| `API_KEY` | API authentication key | Required |
| `SOVITS_BASE_URL` | GPT-SoVITS service URL | http://localhost:9880 |
| `SOVITS_TIMEOUT` | Request timeout (seconds) | 300 |
| `MAX_UPLOAD_SIZE` | Max file size (bytes) | 10485760 (10MB) |
| `CORS_ORIGINS` | Allowed CORS origins | ["http://localhost:3000"] |
| `LOG_LEVEL` | Logging level | INFO |

## Error Handling

The API returns structured error responses:

```json
{
  "success": false,
  "error": "error_type",
  "message": "Human-readable error message",
  "details": {}
}
```

**Common Error Codes:**
- `401`: Missing or invalid API key
- `400`: Invalid request (validation error)
- `413`: File too large
- `504`: GPT-SoVITS service timeout
- `502`: GPT-SoVITS service error
- `500`: Internal server error

## Development

### Running Tests

```bash
pytest
```

### Running Celery Worker

```bash
celery -A app.tasks.cover_tasks worker --loglevel=INFO --queues=cover
```

Note: cover jobs require `COVER_SEPARATE_CMD_TEMPLATE` and `COVER_INFER_CMD_TEMPLATE`
to be configured in `.env` so worker can call your GPT-SoVITS runtime commands.

Recommended AutoDL values:

```bash
GPT_SOVITS_PYTHON=/root/miniconda3/envs/GPTSoVits/bin/python
GPT_SOVITS_PROJECT_ROOT=/root/GPT-SoVITS
COVER_UVR_MODEL=HP2_all_vocals
COVER_SEPARATE_CMD_TEMPLATE="{python_exec} scripts/gptsovits_separate.py --project-root {project_root} --input {song_input} --vocal {vocal_output} --inst {inst_output} --model {uvr_model} --device cuda --is-half true"
COVER_INFER_CMD_TEMPLATE="{python_exec} scripts/gptsovits_infer.py --project-root {project_root} --reference {reference_voice} --input {input_vocal} --output {output_vocal} --model-id {model_id} --pitch {pitch_shift}"
```

Important: `scripts/gptsovits_infer.py` now uses GPT-SoVITS official runtime inference (`TTS.run` + dynamic weight switching).
If you need better cover quality, tune ASR/transcription and inference parameters rather than changing route/task protocols.

### Code Formatting

```bash
black app/
```

### Type Checking

```bash
mypy app/
```

### Linting

```bash
flake8 app/
```

## Troubleshooting

### GPT-SoVITS Connection Issues

1. Verify GPT-SoVITS is running:
   ```bash
   curl http://localhost:9880/health
   ```

2. Check `SOVITS_BASE_URL` in `.env`

3. Review logs for connection errors

### Authentication Errors

1. Verify `X-API-Key` header is set
2. Check `API_KEY` in `.env` matches request header
3. Ensure API key is not empty or default value

### File Upload Issues

1. Check file size is under `MAX_UPLOAD_SIZE`
2. Verify file format is supported audio type
3. Ensure `Content-Type` is set correctly

## Security Considerations

1. **API Key**: Always use a strong, randomly generated API key in production
2. **HTTPS**: Use HTTPS in production (configure reverse proxy)
3. **CORS**: Restrict `CORS_ORIGINS` to trusted domains only
4. **File Validation**: The API validates file types and sizes
5. **Rate Limiting**: Consider adding rate limiting for production

## Performance Tips

1. **Workers**: Use multiple uvicorn workers in production
2. **Timeout**: Adjust `SOVITS_TIMEOUT` based on your needs
3. **File Size**: Limit `MAX_UPLOAD_SIZE` to prevent abuse
4. **Caching**: Consider caching frequently used reference voices

## License

MIT License

## Support

For issues and questions, please open an issue on the project repository.
