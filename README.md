# Voice Cloning Web Application

A full-stack voice cloning application with frontend/backend separation that integrates with GPT-SoVITS for high-quality voice synthesis.

## Architecture

```
┌─────────────────┐      HTTP/REST      ┌──────────────────┐
│  React Frontend │ ◄──────────────────► │  FastAPI Backend │
│   (Port 3000)   │                      │   (Port 8000)    │
└─────────────────┘                      └────────┬─────────┘
                                                  │ HTTP API
                                                  ▼
                                         ┌──────────────────┐
                                         │  GPT-SoVITS API  │
                                         │   (Port 9880)    │
                                         └──────────────────┘
```

## Features

- **Voice Cloning**: Upload reference audio and generate speech with cloned voice
- **Modern UI**: React + TypeScript with cyberpunk aesthetic
- **REST API**: FastAPI backend with OpenAPI documentation
- **Authentication**: API key-based security
- **File Upload**: Drag-and-drop audio file upload with validation
- **Audio Playback**: Custom audio player with controls
- **Health Monitoring**: Real-time backend health status
- **Error Handling**: Comprehensive error handling and user feedback

## Tech Stack

### Backend
- **FastAPI**: Modern Python web framework
- **Pydantic**: Data validation and settings management
- **httpx**: Async HTTP client for GPT-SoVITS integration
- **uvicorn**: ASGI server

### Frontend
- **React 18**: UI library
- **TypeScript**: Type-safe JavaScript
- **Vite**: Fast build tool and dev server
- **Axios**: HTTP client
- **CSS3**: Custom styling with animations

### External Service
- **GPT-SoVITS**: Voice cloning and TTS engine

## Prerequisites

- **Python**: 3.10+ (Conda recommended)
- **Node.js**: 16+ with npm
- **GPT-SoVITS**: Installed and running on localhost:9880

## Quick Start

### 1. Setup GPT-SoVITS

```bash
# Clone GPT-SoVITS repository
git clone https://github.com/RVC-Boss/GPT-SoVITS.git
cd GPT-SoVITS

# Follow their installation instructions
# Start the API server (typically on port 9880)
python api.py
```

### 2. Setup Backend

```bash
# Navigate to backend directory
cd backend

# Create conda environment
conda create -n voice_api python=3.10
conda activate voice_api

# Install dependencies
pip install -r requirements.txt

# Configure environment
copy .env.example .env
# Edit .env and set API_KEY and SOVITS_BASE_URL

# Generate API key
python -c "import secrets; print(secrets.token_urlsafe(32))"

# Start backend server
uvicorn app.main:app --reload --port 8000
```

Backend will be available at: http://localhost:8000

### 3. Setup Frontend

```bash
# Navigate to frontend directory
cd frontend

# Install dependencies
npm install

# Start development server
npm run dev
```

Frontend will be available at: http://localhost:3000

## Usage

1. **Access the application** at http://localhost:3000
2. **Check backend status** - Green indicator means backend is healthy
3. **Upload reference audio** - Drag and drop or click to select (WAV/MP3/OGG, max 50MB)
4. **Enter text** - Type the text you want to synthesize (max 500 characters)
5. **Select language** - Choose from Auto, Chinese, English, or Japanese
6. **Adjust parameters** (optional):
   - Speed: 0.5 to 2.0 (default: 1.0)
   - Temperature: 0.0 to 1.0 (default: 0.7)
7. **Click "Clone Voice"** - Wait for synthesis to complete
8. **Play or download** - Use the audio player to listen or download the result

## API Documentation

Once the backend is running, access the interactive API documentation:

- **Swagger UI**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc

### API Endpoints

#### Health Check
```
GET /health
```

#### Voice Synthesis
```
POST /api/v1/voice/synthesize
Headers: X-API-Key: <your-api-key>
Body: multipart/form-data
  - reference_audio: file (WAV/MP3/OGG)
  - text: string (max 500 chars)
  - language: string (auto/zh/en/ja)
  - speed: float (0.5-2.0, optional)
  - temperature: float (0.0-1.0, optional)
```

## Project Structure

```
voice_ll/
├── backend/              # FastAPI application
│   ├── app/
│   │   ├── main.py      # Application entry point
│   │   ├── api/         # API routes
│   │   ├── core/        # Configuration and security
│   │   ├── services/    # GPT-SoVITS client
│   │   └── models/      # Pydantic schemas
│   ├── requirements.txt
│   ├── .env.example
│   └── README.md
├── frontend/            # React + Vite application
│   ├── src/
│   │   ├── App.tsx
│   │   ├── components/  # React components
│   │   ├── services/    # API client
│   │   ├── types/       # TypeScript types
│   │   └── styles/      # CSS styles
│   ├── package.json
│   ├── vite.config.ts
│   └── README.md
├── CLAUDE.md           # Development guide for Claude Code
└── README.md           # This file
```

## Configuration

### Backend Configuration (.env)

```env
# API Security
API_KEY=your-secure-api-key-here

# GPT-SoVITS Service
SOVITS_BASE_URL=http://localhost:9880

# CORS Settings
ALLOWED_ORIGINS=http://localhost:3000,http://localhost:5173

# File Upload
MAX_UPLOAD_SIZE=52428800  # 50MB in bytes
```

### Frontend Configuration

API key is configured in `frontend/src/services/api.ts`. Update the `API_KEY` constant with your backend API key.

## Development

### Backend Development

```bash
cd backend
conda activate voice_api

# Run with auto-reload
uvicorn app.main:app --reload --port 8000

# View logs in terminal
```

### Frontend Development

```bash
cd frontend

# Run dev server with hot reload
npm run dev

# Build for production
npm run build

# Preview production build
npm run preview

# Lint code
npm run lint
```

## Troubleshooting

### Backend Issues

**Problem**: Backend can't connect to GPT-SoVITS
- Verify GPT-SoVITS is running: `curl http://localhost:9880/health`
- Check `SOVITS_BASE_URL` in `.env`

**Problem**: CORS errors in browser
- Add frontend URL to `ALLOWED_ORIGINS` in `.env`
- Restart backend after changing `.env`

**Problem**: "Unauthorized" errors
- Verify API key matches between backend `.env` and frontend `api.ts`

### Frontend Issues

**Problem**: API calls fail
- Ensure backend is running on port 8000
- Check browser console for detailed errors

**Problem**: File upload fails
- Check file size (max 50MB) and format (WAV/MP3/OGG)
- Verify file is not corrupted

**Problem**: Audio won't play
- Try a different browser (Chrome/Firefox/Edge)
- Check browser console for codec errors

### GPT-SoVITS Issues

**Problem**: Synthesis takes too long or times out
- Check GPT-SoVITS server logs
- Verify GPU is available (if required)
- Reduce text length

## Security

- **API Keys**: Never commit `.env` files. Use strong, random keys.
- **CORS**: Restrict origins to trusted domains in production.
- **File Upload**: Size and type validation enforced. Consider virus scanning.
- **HTTPS**: Use reverse proxy (nginx/caddy) with SSL in production.
- **Rate Limiting**: Consider adding rate limiting for production deployment.

## Performance

- **Synthesis Time**: 5-30 seconds depending on text length and hardware
- **File Upload**: Max 50MB, consider compression for large files
- **Concurrent Requests**: GPT-SoVITS may have limited capacity, implement queuing if needed

## License

This project is provided as-is for educational and internal use.

## Acknowledgments

- **GPT-SoVITS**: https://github.com/RVC-Boss/GPT-SoVITS
- Voice cloning technology powered by GPT-SoVITS team

## Support

For issues and questions:
1. Check the troubleshooting section above
2. Review backend logs and browser console
3. Consult GPT-SoVITS documentation for service-specific issues
4. See `CLAUDE.md` for detailed development guidance
