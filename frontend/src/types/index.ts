// API Response Types
export interface CloneResponse {
  success: boolean;
  audio_url?: string;
  message?: string;
  error?: string;
}

export interface HealthResponse {
  status: string;
  version: string;
  sovits_available: boolean;
  uptime_seconds: number;
}

// Component Props Types
export interface AudioUploadProps {
  onFileSelect: (file: File | null) => void;
  selectedFile: File | null;
  disabled?: boolean;
}

export interface TextInputProps {
  value: string;
  onChange: (value: string) => void;
  disabled?: boolean;
  maxLength?: number;
}

export interface AudioPlayerProps {
  audioUrl: string | null;
  onClose: () => void;
}

// Form State Types
export interface VoiceCloneFormState {
  referenceAudio: File | null;
  targetText: string;
  isLoading: boolean;
  error: string | null;
  generatedAudioUrl: string | null;
}

// API Error Type
export interface ApiError {
  message: string;
  status?: number;
  details?: string;
}
