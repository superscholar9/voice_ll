# Voice Cloning Frontend

Modern React + TypeScript frontend for the voice cloning application.

## Features

- **Modern UI**: Bold cyberpunk-inspired design with smooth animations
- **TypeScript**: Full type safety throughout the application
- **Responsive**: Works seamlessly on desktop, tablet, and mobile
- **Real-time Feedback**: Loading states, error handling, and status indicators
- **Audio Player**: Custom audio player with playback controls and download
- **File Upload**: Drag-and-drop audio file upload with validation
- **API Integration**: Axios-based API client with error handling

## Tech Stack

- React 18
- TypeScript
- Vite
- Axios
- CSS3 (Custom styling, no framework dependencies)

## Getting Started

### Prerequisites

- Node.js 16+ and npm
- Backend server running on `http://localhost:8000`

### Installation

```bash
# Install dependencies
npm install

# Start development server
npm run dev

# Build for production
npm run build

# Preview production build
npm run preview
```

The application will be available at `http://localhost:3000`

## Project Structure

```
frontend/
├── src/
│   ├── components/          # React components
│   │   ├── VoiceClone.tsx   # Main component
│   │   ├── AudioUpload.tsx  # File upload component
│   │   ├── TextInput.tsx    # Text input component
│   │   └── AudioPlayer.tsx  # Audio playback component
│   ├── services/
│   │   └── api.ts           # API client
│   ├── types/
│   │   └── index.ts         # TypeScript types
│   ├── styles/
│   │   └── App.css          # Global styles
│   ├── App.tsx              # Root component
│   └── main.tsx             # Entry point
├── public/                  # Static assets
├── index.html               # HTML template
├── vite.config.ts           # Vite configuration
├── tsconfig.json            # TypeScript configuration
└── package.json             # Dependencies
```

## API Configuration

The frontend proxies API requests to the backend:

- Development: `/api` → `http://localhost:8000`
- Configured in `vite.config.ts`

## Components

### VoiceClone
Main component that orchestrates the voice cloning workflow:
- Backend health check
- Form state management
- API integration
- Error handling

### AudioUpload
Drag-and-drop file upload with:
- File validation (type, size)
- Visual feedback
- File preview

### TextInput
Text area for target text with:
- Character counter
- Validation
- Visual feedback

### AudioPlayer
Custom audio player with:
- Play/pause controls
- Seek bar
- Volume control
- Download functionality

## Styling

The application uses a bold cyberpunk aesthetic with:
- Neon color palette (cyan, magenta, green)
- Animated gradients and glows
- Smooth transitions
- Responsive design
- Dark theme

## Error Handling

- Network errors
- API errors
- File validation errors
- User-friendly error messages
- Retry functionality

## Browser Support

- Chrome/Edge (latest)
- Firefox (latest)
- Safari (latest)

## Development

```bash
# Run linter
npm run lint

# Type check
npx tsc --noEmit
```

## Production Build

```bash
npm run build
```

The optimized build will be in the `dist/` directory.

## Environment Variables

No environment variables required. API endpoint is configured via Vite proxy.

## License

MIT
