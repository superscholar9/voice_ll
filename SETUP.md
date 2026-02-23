# Setup Guide

Complete step-by-step guide to set up the Voice Cloning application.

## Prerequisites Checklist

- [ ] Python 3.10+ installed (Conda recommended)
- [ ] Node.js 16+ with npm installed
- [ ] Git installed
- [ ] At least 4GB free disk space
- [ ] GPU recommended for GPT-SoVITS (optional, CPU works but slower)

## Step 1: Clone and Setup GPT-SoVITS

### 1.1 Clone Repository

```bash
# Navigate to a suitable directory
cd D:\projects

# Clone GPT-SoVITS
git clone https://github.com/RVC-Boss/GPT-SoVITS.git
cd GPT-SoVITS
```

### 1.2 Install GPT-SoVITS Dependencies

Follow the official GPT-SoVITS installation guide:
- https://github.com/RVC-Boss/GPT-SoVITS#installation

Typical steps:
```bash
# Create conda environment
conda create -n gptsovits python=3.10
conda activate gptsovits

# Install dependencies
pip install -r requirements.txt
```

### 1.3 Download Models

Download required models as per GPT-SoVITS documentation.

### 1.4 Start GPT-SoVITS API Server

```bash
conda activate gptsovits
python api.py
```

Verify it's running:
```bash
curl http://localhost:9880/health
```

## Step 2: Setup Backend

### 2.1 Navigate to Backend Directory

```bash
cd D:\pythonproject\voice_ll\backend
```

### 2.2 Create Conda Environment

```bash
conda create -n voice_api python=3.10
conda activate voice_api
```

### 2.3 Install Dependencies

```bash
pip install -r requirements.txt
```

### 2.4 Configure Environment

```bash
# Copy environment template
copy .env.example .env
```

### 2.5 Generate API Key

```bash
python -c "import secrets; print(secrets.token_urlsafe(32))"
```

Copy the output.

### 2.6 Edit .env File

Open `.env` in a text editor and update:

```env
API_KEY=<paste-generated-key-here>
SOVITS_BASE_URL=http://localhost:9880
ALLOWED_ORIGINS=http://localhost:3000,http://localhost:5173
MAX_UPLOAD_SIZE=52428800
```

### 2.7 Test Backend

```bash
# Start server
uvicorn app.main:app --reload --port 8000
```

Open browser to http://localhost:8000/docs - you should see API documentation.

## Step 3: Setup Frontend

### 3.1 Navigate to Frontend Directory

Open a new terminal:
```bash
cd D:\pythonproject\voice_ll\frontend
```

### 3.2 Install Dependencies

```bash
npm install
```

This may take a few minutes.

### 3.3 Configure API Key

Edit `src/services/api.ts` and update the API_KEY constant with the key you generated in Step 2.5:

```typescript
const API_KEY = 'your-generated-api-key-here';
```

### 3.4 Start Development Server

```bash
npm run dev
```

Frontend will start on http://localhost:3000

## Step 4: Verify Everything Works

### 4.1 Check All Services

You should have 3 terminals running:

1. **GPT-SoVITS**: Port 9880
2. **Backend**: Port 8000
3. **Frontend**: Port 3000

### 4.2 Test the Application

1. Open http://localhost:3000 in your browser
2. Check that the backend health indicator is green
3. Prepare a test audio file (WAV or MP3, a few seconds of speech)
4. Upload the audio file
5. Enter some test text (e.g., "Hello, this is a test")
6. Click "Clone Voice"
7. Wait for synthesis to complete
8. Play the generated audio

## Troubleshooting

### GPT-SoVITS Not Starting

**Problem**: Import errors or missing dependencies
- **Solution**: Ensure you activated the correct conda environment
- Reinstall dependencies: `pip install -r requirements.txt`

**Problem**: Model files not found
- **Solution**: Download required models as per GPT-SoVITS docs

### Backend Issues

**Problem**: `ModuleNotFoundError`
- **Solution**: Activate environment: `conda activate voice_api`
- Reinstall: `pip install -r requirements.txt`

**Problem**: Port 8000 already in use
- **Solution**: Kill existing process or use different port:
  ```bash
  uvicorn app.main:app --reload --port 8001
  ```
  Update frontend proxy in `vite.config.ts`

### Frontend Issues

**Problem**: `npm install` fails
- **Solution**: Clear cache and retry:
  ```bash
  npm cache clean --force
  npm install
  ```

**Problem**: Port 3000 already in use
- **Solution**: Vite will automatically try port 3001, 3002, etc.

**Problem**: API calls fail with CORS errors
- **Solution**: Check `ALLOWED_ORIGINS` in backend `.env`
- Ensure it includes your frontend URL

## Next Steps

Once everything is working:

1. **Customize**: Modify UI colors, text, or layout in `frontend/src/`
2. **Add Features**: Extend API endpoints in `backend/app/api/routes/`
3. **Deploy**: Consider containerization with Docker
4. **Secure**: Add user authentication, rate limiting
5. **Monitor**: Add logging and error tracking

## Quick Reference

### Start All Services

**Terminal 1 - GPT-SoVITS**:
```bash
cd D:\projects\GPT-SoVITS
conda activate gptsovits
python api.py
```

**Terminal 2 - Backend**:
```bash
cd D:\pythonproject\voice_ll\backend
conda activate voice_api
uvicorn app.main:app --reload --port 8000
```

**Terminal 3 - Frontend**:
```bash
cd D:\pythonproject\voice_ll\frontend
npm run dev
```

### URLs

- Frontend: http://localhost:3000
- Backend API: http://localhost:8000
- API Docs: http://localhost:8000/docs
- GPT-SoVITS: http://localhost:9880

## Support

- See `README.md` for general information
- See `CLAUDE.md` for development guidance
- Check backend logs in terminal for errors
- Check browser console (F12) for frontend errors
