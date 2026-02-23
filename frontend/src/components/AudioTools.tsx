import React, { useState } from 'react';
import { api } from '../services/api';
import { useToast } from '../contexts/ToastContext';
import ToolCard from './ToolCard';
import '../styles/AudioTools.css';

interface AudioToolsProps {
  onToolComplete?: (toolName: string, audioUrl: string) => void;
}

export const AudioTools: React.FC<AudioToolsProps> = ({ onToolComplete }) => {
  const [selectedFile, setSelectedFile] = useState<File | null>(null);
  const [isLoading, setIsLoading] = useState(false);
  const [audioInfo, setAudioInfo] = useState<any>(null);
  const [resultUrl, setResultUrl] = useState<string | null>(null);
  const [resultTool, setResultTool] = useState<string | null>(null);
  const { showToast } = useToast();

  const handleFileSelect = (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (file) {
      setSelectedFile(file);
      setAudioInfo(null);
      setResultUrl(null);
    }
  };

  const handleGetAudioInfo = async () => {
    if (!selectedFile) {
      showToast('Please select an audio file', 'error');
      return;
    }

    setIsLoading(true);
    try {
      const info = await api.getAudioInfo(selectedFile);
      setAudioInfo(info);
      showToast('Audio information extracted successfully', 'success');
    } catch (error: any) {
      showToast(error.message || 'Failed to extract audio info', 'error');
    } finally {
      setIsLoading(false);
    }
  };

  const handleConvertFormat = async (format: string) => {
    if (!selectedFile) {
      showToast('Please select an audio file', 'error');
      return;
    }

    setIsLoading(true);
    try {
      const url = await api.convertAudioFormat(selectedFile, format);
      setResultUrl(url);
      setResultTool(`Convert to ${format.toUpperCase()}`);
      onToolComplete?.(`convert_${format}`, url);
      showToast(`Audio converted to ${format.toUpperCase()} successfully`, 'success');
    } catch (error: any) {
      showToast(error.message || 'Failed to convert audio', 'error');
    } finally {
      setIsLoading(false);
    }
  };

  const handleAdjustSpeed = async (speed: number) => {
    if (!selectedFile) {
      showToast('Please select an audio file', 'error');
      return;
    }

    setIsLoading(true);
    try {
      const url = await api.adjustAudioSpeed(selectedFile, speed);
      setResultUrl(url);
      setResultTool(`Speed ${speed.toFixed(1)}x`);
      onToolComplete?.('adjust_speed', url);
      showToast(`Audio speed adjusted to ${speed.toFixed(1)}x successfully`, 'success');
    } catch (error: any) {
      showToast(error.message || 'Failed to adjust audio speed', 'error');
    } finally {
      setIsLoading(false);
    }
  };

  const handleAdjustVolume = async (volumeDb: number) => {
    if (!selectedFile) {
      showToast('Please select an audio file', 'error');
      return;
    }

    setIsLoading(true);
    try {
      const url = await api.adjustAudioVolume(selectedFile, volumeDb);
      setResultUrl(url);
      setResultTool(`Volume ${volumeDb > 0 ? '+' : ''}${volumeDb}dB`);
      onToolComplete?.('adjust_volume', url);
      showToast(`Audio volume adjusted by ${volumeDb}dB successfully`, 'success');
    } catch (error: any) {
      showToast(error.message || 'Failed to adjust audio volume', 'error');
    } finally {
      setIsLoading(false);
    }
  };

  const handleDownload = () => {
    if (!resultUrl) return;

    const link = document.createElement('a');
    link.href = resultUrl;
    link.download = `audio_${resultTool?.replace(/\s+/g, '_').toLowerCase()}.wav`;
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
  };

  return (
    <div className="audio-tools-container">
      <h2>Audio Tools</h2>

      <div className="audio-tools-upload">
        <label htmlFor="audio-file-input" className="file-input-label">
          <span className="upload-icon">📁</span>
          <span className="upload-text">
            {selectedFile ? selectedFile.name : 'Click to select audio file'}
          </span>
        </label>
        <input
          id="audio-file-input"
          type="file"
          accept="audio/*"
          onChange={handleFileSelect}
          disabled={isLoading}
          className="file-input"
        />
      </div>

      {selectedFile && (
        <button
          onClick={handleGetAudioInfo}
          disabled={isLoading}
          className="btn btn-primary"
        >
          {isLoading ? 'Analyzing...' : 'Get Audio Info'}
        </button>
      )}

      {audioInfo && (
        <div className="audio-info-display">
          <h3>Audio Information</h3>
          <div className="info-grid">
            <div className="info-item">
              <span className="info-label">Duration</span>
              <span className="info-value">{audioInfo.duration_seconds.toFixed(2)}s</span>
            </div>
            <div className="info-item">
              <span className="info-label">Channels</span>
              <span className="info-value">{audioInfo.channels}</span>
            </div>
            <div className="info-item">
              <span className="info-label">Sample Rate</span>
              <span className="info-value">{audioInfo.sample_rate}Hz</span>
            </div>
            <div className="info-item">
              <span className="info-label">File Size</span>
              <span className="info-value">{(audioInfo.file_size_bytes / 1024).toFixed(2)}KB</span>
            </div>
          </div>
        </div>
      )}

      {selectedFile && (
        <div className="tools-grid">
          <ToolCard
            title="Convert Format"
            description="Convert to WAV, MP3, FLAC, or OGG"
            icon="🔄"
            actions={[
              { label: 'WAV', onClick: () => handleConvertFormat('wav') },
              { label: 'MP3', onClick: () => handleConvertFormat('mp3') },
              { label: 'FLAC', onClick: () => handleConvertFormat('flac') },
              { label: 'OGG', onClick: () => handleConvertFormat('ogg') },
            ]}
            isLoading={isLoading}
          />

          <ToolCard
            title="Adjust Speed"
            description="Change playback speed (0.5x - 2.0x)"
            icon="⚡"
            actions={[
              { label: '0.5x', onClick: () => handleAdjustSpeed(0.5) },
              { label: '1.0x', onClick: () => handleAdjustSpeed(1.0) },
              { label: '1.5x', onClick: () => handleAdjustSpeed(1.5) },
              { label: '2.0x', onClick: () => handleAdjustSpeed(2.0) },
            ]}
            isLoading={isLoading}
          />

          <ToolCard
            title="Adjust Volume"
            description="Change volume level (-20dB to +20dB)"
            icon="🔊"
            actions={[
              { label: '-10dB', onClick: () => handleAdjustVolume(-10) },
              { label: '-5dB', onClick: () => handleAdjustVolume(-5) },
              { label: '+5dB', onClick: () => handleAdjustVolume(5) },
              { label: '+10dB', onClick: () => handleAdjustVolume(10) },
            ]}
            isLoading={isLoading}
          />
        </div>
      )}

      {resultUrl && (
        <div className="audio-result">
          <h3>Result: {resultTool}</h3>
          <audio controls src={resultUrl} />
          <button onClick={handleDownload} className="btn btn-secondary">
            Download Audio
          </button>
        </div>
      )}
    </div>
  );
};

export default AudioTools;
