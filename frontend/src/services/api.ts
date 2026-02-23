import axios, { AxiosError, AxiosInstance } from 'axios';
import type { HealthResponse, ApiError } from '../types';

const API_BASE_URL = '/api';

// Create axios instance with default config
const apiClient: AxiosInstance = axios.create({
  baseURL: API_BASE_URL,
  timeout: 120000, // 2 minutes for voice cloning
  headers: {
    'Content-Type': 'application/json',
  },
});

// JWT interceptor - add token to requests
apiClient.interceptors.request.use(
  (config) => {
    const token = localStorage.getItem('access_token');
    if (token) {
      config.headers.Authorization = `Bearer ${token}`;
    }
    return config;
  },
  (error) => {
    return Promise.reject(error);
  }
);

// Response interceptor - handle token refresh
apiClient.interceptors.response.use(
  (response) => response,
  async (error: AxiosError) => {
    const originalRequest = error.config as any;

    // If 401 and not already retried, try to refresh token
    if (error.response?.status === 401 && !originalRequest._retry) {
      originalRequest._retry = true;

      try {
        const refreshToken = localStorage.getItem('refresh_token');
        if (refreshToken) {
          const response = await axios.post(`${API_BASE_URL}/v1/auth/refresh`, {
            refresh_token: refreshToken,
          });

          const { access_token, refresh_token } = response.data;
          localStorage.setItem('access_token', access_token);
          localStorage.setItem('refresh_token', refresh_token);

          // Retry original request with new token
          originalRequest.headers.Authorization = `Bearer ${access_token}`;
          return apiClient(originalRequest);
        }
      } catch (refreshError) {
        // Refresh failed, clear tokens and redirect to login
        localStorage.removeItem('access_token');
        localStorage.removeItem('refresh_token');
        window.location.href = '/login';
      }
    }

    return Promise.reject(error);
  }
);

// Error handler
const handleApiError = (error: AxiosError): ApiError => {
  if (error.response) {
    // Server responded with error status
    const data = error.response.data as any;
    return {
      message: data.detail || data.message || 'Server error occurred',
      status: error.response.status,
      details: data.error || JSON.stringify(data),
    };
  } else if (error.request) {
    // Request made but no response
    return {
      message: 'No response from server. Please check if the backend is running.',
      details: 'Network error or server is down',
    };
  } else {
    // Error in request setup
    return {
      message: error.message || 'An unexpected error occurred',
      details: 'Request configuration error',
    };
  }
};

// API Methods
export const api = {
  /**
   * Check backend health status
   */
  async checkHealth(): Promise<HealthResponse> {
    try {
      const response = await axios.get<HealthResponse>('/health');
      return response.data;
    } catch (error) {
      throw handleApiError(error as AxiosError);
    }
  },

  /**
   * Clone voice with reference audio and target text
   * Returns a blob URL for the generated audio
   */
  async cloneVoice(
    referenceAudio: File,
    targetText: string,
    language: string = 'auto',
    speed: number = 1.0,
    temperature: number = 0.7
  ): Promise<string> {
    try {
      const formData = new FormData();
      formData.append('reference_audio', referenceAudio);
      formData.append('text', targetText);
      formData.append('language', language);
      formData.append('speed', speed.toString());
      formData.append('temperature', temperature.toString());

      const response = await apiClient.post(
        '/v1/voice/synthesize',
        formData,
        {
          headers: {
            'Content-Type': 'multipart/form-data',
          },
          responseType: 'blob', // Receive binary data
        }
      );

      // Create a blob URL from the binary data
      const audioBlob = new Blob([response.data], { type: 'audio/wav' });
      const blobUrl = URL.createObjectURL(audioBlob);

      return blobUrl;
    } catch (error) {
      throw handleApiError(error as AxiosError);
    }
  },

  /**
   * Get full URL for audio file
   */
  getAudioUrl(relativePath: string): string {
    // Remove leading slash if present
    const cleanPath = relativePath.startsWith('/')
      ? relativePath.slice(1)
      : relativePath;
    return `${API_BASE_URL}/${cleanPath}`;
  },

  /**
   * Register new user
   */
  async register(username: string, email: string, password: string, turnstileToken: string): Promise<{ message: string }> {
    try {
      const response = await apiClient.post('/v1/auth/register', {
        username,
        email,
        password,
        turnstile_token: turnstileToken,
      });
      return response.data;
    } catch (error) {
      throw handleApiError(error as AxiosError);
    }
  },

  /**
   * Login user
   */
  async login(username: string, password: string, turnstileToken: string): Promise<{ access_token: string; refresh_token: string }> {
    try {
      const response = await apiClient.post('/v1/auth/login', {
        username,
        password,
        turnstile_token: turnstileToken,
      });
      return response.data;
    } catch (error) {
      throw handleApiError(error as AxiosError);
    }
  },

  /**
   * Refresh access token
   */
  async refreshToken(refreshToken: string): Promise<{ access_token: string; refresh_token: string }> {
    try {
      const response = await apiClient.post('/v1/auth/refresh', {
        refresh_token: refreshToken,
      });
      return response.data;
    } catch (error) {
      throw handleApiError(error as AxiosError);
    }
  },

  /**
   * Logout user
   */
  async logout(refreshToken: string): Promise<{ message: string }> {
    try {
      const response = await apiClient.post('/v1/auth/logout', {
        refresh_token: refreshToken,
      });
      return response.data;
    } catch (error) {
      throw handleApiError(error as AxiosError);
    }
  },

  /**
   * Get current user info
   */
  async getCurrentUser(accessToken: string): Promise<any> {
    try {
      const response = await apiClient.get('/v1/users/me', {
        headers: {
          Authorization: `Bearer ${accessToken}`,
        },
      });
      return response.data;
    } catch (error) {
      throw handleApiError(error as AxiosError);
    }
  },

  /**
   * Get synthesis history
   */
  async getHistory(limit: number = 20, offset: number = 0): Promise<any> {
    try {
      const response = await apiClient.get('/v1/history', {
        params: { limit, offset },
      });
      return response.data;
    } catch (error) {
      throw handleApiError(error as AxiosError);
    }
  },

  /**
   * Get audio file information
   */
  async getAudioInfo(audioFile: File): Promise<any> {
    try {
      const formData = new FormData();
      formData.append('audio_file', audioFile);

      const response = await apiClient.post('/v1/audio/info', formData, {
        headers: {
          'Content-Type': 'multipart/form-data',
        },
      });
      return response.data;
    } catch (error) {
      throw handleApiError(error as AxiosError);
    }
  },

  /**
   * Convert audio format
   */
  async convertAudioFormat(audioFile: File, targetFormat: string): Promise<string> {
    try {
      const formData = new FormData();
      formData.append('audio_file', audioFile);
      formData.append('target_format', targetFormat);

      const response = await apiClient.post('/v1/audio/convert', formData, {
        headers: {
          'Content-Type': 'multipart/form-data',
        },
        responseType: 'blob',
      });

      const audioBlob = new Blob([response.data], { type: `audio/${targetFormat}` });
      const blobUrl = URL.createObjectURL(audioBlob);
      return blobUrl;
    } catch (error) {
      throw handleApiError(error as AxiosError);
    }
  },

  /**
   * Adjust audio speed
   */
  async adjustAudioSpeed(audioFile: File, speedFactor: number): Promise<string> {
    try {
      const formData = new FormData();
      formData.append('audio_file', audioFile);
      formData.append('speed_factor', speedFactor.toString());

      const response = await apiClient.post('/v1/audio/adjust-speed', formData, {
        headers: {
          'Content-Type': 'multipart/form-data',
        },
        responseType: 'blob',
      });

      const audioBlob = new Blob([response.data], { type: 'audio/wav' });
      const blobUrl = URL.createObjectURL(audioBlob);
      return blobUrl;
    } catch (error) {
      throw handleApiError(error as AxiosError);
    }
  },

  /**
   * Adjust audio volume
   */
  async adjustAudioVolume(audioFile: File, volumeDb: number): Promise<string> {
    try {
      const formData = new FormData();
      formData.append('audio_file', audioFile);
      formData.append('volume_db', volumeDb.toString());

      const response = await apiClient.post('/v1/audio/adjust-volume', formData, {
        headers: {
          'Content-Type': 'multipart/form-data',
        },
        responseType: 'blob',
      });

      const audioBlob = new Blob([response.data], { type: 'audio/wav' });
      const blobUrl = URL.createObjectURL(audioBlob);
      return blobUrl;
    } catch (error) {
      throw handleApiError(error as AxiosError);
    }
  },

  /**
   * Text-to-speech synthesis
   */
  async textToSpeech(
    text: string,
    language: string = 'auto',
    speed: number = 1.0,
    temperature: number = 0.7
  ): Promise<string> {
    try {
      const formData = new FormData();
      formData.append('text', text);
      formData.append('language', language);
      formData.append('speed', speed.toString());
      formData.append('temperature', temperature.toString());

      const response = await apiClient.post('/v1/voice/tts', formData, {
        headers: {
          'Content-Type': 'multipart/form-data',
        },
        responseType: 'blob',
      });

      const audioBlob = new Blob([response.data], { type: 'audio/wav' });
      const blobUrl = URL.createObjectURL(audioBlob);
      return blobUrl;
    } catch (error) {
      throw handleApiError(error as AxiosError);
    }
  },
};

export default api;
