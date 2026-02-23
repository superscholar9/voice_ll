import React, { useRef, useState, useEffect } from 'react';
import type { AudioUploadProps } from '../types';
import '../styles/AudioUpload.css';

const AudioUpload: React.FC<AudioUploadProps> = ({
  onFileSelect,
  selectedFile,
  disabled = false,
}) => {
  const fileInputRef = useRef<HTMLInputElement>(null);
  const [dragActive, setDragActive] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [ripples, setRipples] = useState<Array<{ id: number; x: number; y: number }>>([]);
  const [justUploaded, setJustUploaded] = useState(false);

  const ALLOWED_TYPES = ['audio/wav', 'audio/mpeg', 'audio/mp3', 'audio/ogg', 'audio/flac'];
  const MAX_SIZE = 10 * 1024 * 1024; // 10MB (matches backend limit)

  // Get file type badge
  const getFileTypeBadge = (file: File): string => {
    const type = file.type.split('/')[1]?.toUpperCase();
    if (type === 'MPEG') return 'MP3';
    if (type === 'X-FLAC') return 'FLAC';
    return type || 'AUDIO';
  };

  // Format file size
  const formatFileSize = (bytes: number): string => {
    if (bytes < 1024) return `${bytes} B`;
    if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(1)} KB`;
    return `${(bytes / 1024 / 1024).toFixed(2)} MB`;
  };

  const validateFile = (file: File): string | null => {
    if (!ALLOWED_TYPES.includes(file.type)) {
      return 'Please upload a valid audio file (WAV, MP3, FLAC, or OGG)';
    }
    if (file.size > MAX_SIZE) {
      return 'File size must be less than 10 MB';
    }
    return null;
  };

  const handleFile = (file: File) => {
    const validationError = validateFile(file);
    if (validationError) {
      setError(validationError);
      onFileSelect(null);
      return;
    }
    setError(null);
    setJustUploaded(true);
    onFileSelect(file);

    // Reset animation after delay
    setTimeout(() => setJustUploaded(false), 600);
  };

  // Ripple effect on drag
  useEffect(() => {
    if (ripples.length > 0) {
      const timer = setTimeout(() => {
        setRipples([]);
      }, 1000);
      return () => clearTimeout(timer);
    }
  }, [ripples]);

  const handleFileChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (file) {
      handleFile(file);
    }
  };

  const handleDrag = (e: React.DragEvent) => {
    e.preventDefault();
    e.stopPropagation();
    if (e.type === 'dragenter' || e.type === 'dragover') {
      setDragActive(true);
    } else if (e.type === 'dragleave') {
      setDragActive(false);
    }
  };

  const handleDrop = (e: React.DragEvent) => {
    e.preventDefault();
    e.stopPropagation();
    setDragActive(false);

    // Create ripple effect at drop position
    const rect = e.currentTarget.getBoundingClientRect();
    const x = ((e.clientX - rect.left) / rect.width) * 100;
    const y = ((e.clientY - rect.top) / rect.height) * 100;
    setRipples([{ id: Date.now(), x, y }]);

    const file = e.dataTransfer.files?.[0];
    if (file) {
      handleFile(file);
    }
  };

  const handleClick = () => {
    fileInputRef.current?.click();
  };

  const handleRemove = (e: React.MouseEvent) => {
    e.stopPropagation();
    setError(null);
    onFileSelect(null);
    if (fileInputRef.current) {
      fileInputRef.current.value = '';
    }
  };

  return (
    <div className="audio-upload">
      <label className="upload-label" htmlFor="audio-file-input">
        <span className="label-icon">🎤</span>
        Reference Audio
        <span className="required">*</span>
      </label>
      <div
        className={`upload-zone ${dragActive ? 'drag-active' : ''} ${
          selectedFile ? 'has-file' : ''
        } ${disabled ? 'disabled' : ''} ${error ? 'has-error' : ''} ${
          justUploaded ? 'just-uploaded' : ''
        }`}
        onDragEnter={handleDrag}
        onDragLeave={handleDrag}
        onDragOver={handleDrag}
        onDrop={handleDrop}
        onClick={disabled ? undefined : handleClick}
        role="button"
        tabIndex={disabled ? -1 : 0}
        aria-label="Upload reference audio file"
        aria-describedby="upload-hint"
        onKeyDown={(e) => {
          if ((e.key === 'Enter' || e.key === ' ') && !disabled) {
            e.preventDefault();
            handleClick();
          }
        }}
      >
        {/* Waveform border SVG */}
        <svg className="waveform-border" viewBox="0 0 400 200" preserveAspectRatio="none">
          <defs>
            <linearGradient id="waveGradient" x1="0%" y1="0%" x2="100%" y2="0%">
              <stop offset="0%" stopColor="#667eea" stopOpacity="0.3" />
              <stop offset="50%" stopColor="#764ba2" stopOpacity="0.6" />
              <stop offset="100%" stopColor="#667eea" stopOpacity="0.3" />
            </linearGradient>
          </defs>
          <path
            className="waveform-path"
            d="M0,100 Q10,80 20,100 T40,100 T60,100 T80,100 T100,100 T120,100 T140,100 T160,100 T180,100 T200,100 T220,100 T240,100 T260,100 T280,100 T300,100 T320,100 T340,100 T360,100 T380,100 L400,100"
            fill="none"
            stroke="url(#waveGradient)"
            strokeWidth="2"
          />
        </svg>

        {/* Ripple effects */}
        {ripples.map((ripple) => (
          <div
            key={ripple.id}
            className="ripple"
            style={{
              left: `${ripple.x}%`,
              top: `${ripple.y}%`,
            }}
          />
        ))}

        <input
          ref={fileInputRef}
          id="audio-file-input"
          type="file"
          accept="audio/*"
          onChange={handleFileChange}
          disabled={disabled}
          style={{ display: 'none' }}
          aria-label="Choose audio file"
        />

        {selectedFile ? (
          <div className="file-info">
            <div className="file-icon-wrapper">
              <div className="file-icon">🎵</div>
              <div className="file-checkmark">
                <svg width="24" height="24" viewBox="0 0 24 24" fill="none">
                  <circle cx="12" cy="12" r="10" fill="#10b981" />
                  <path
                    d="M8 12l3 3 5-6"
                    stroke="white"
                    strokeWidth="2"
                    strokeLinecap="round"
                    strokeLinejoin="round"
                  />
                </svg>
              </div>
            </div>
            <div className="file-details">
              <div className="file-name" title={selectedFile.name}>
                {selectedFile.name}
              </div>
              <div className="file-meta">
                <span className="file-size">{formatFileSize(selectedFile.size)}</span>
                <span className="file-type-badge">{getFileTypeBadge(selectedFile)}</span>
              </div>
            </div>
            {!disabled && (
              <button
                className="remove-btn"
                onClick={handleRemove}
                type="button"
                aria-label="Remove file"
              >
                <svg width="20" height="20" viewBox="0 0 20 20" fill="currentColor">
                  <path
                    fillRule="evenodd"
                    d="M4.293 4.293a1 1 0 011.414 0L10 8.586l4.293-4.293a1 1 0 111.414 1.414L11.414 10l4.293 4.293a1 1 0 01-1.414 1.414L10 11.414l-4.293 4.293a1 1 0 01-1.414-1.414L8.586 10 4.293 5.707a1 1 0 010-1.414z"
                    clipRule="evenodd"
                  />
                </svg>
              </button>
            )}
          </div>
        ) : (
          <div className="upload-prompt">
            <div className="upload-icon-animated">
              <svg className="upload-icon-svg" width="64" height="64" viewBox="0 0 64 64" fill="none">
                <circle cx="32" cy="32" r="30" stroke="currentColor" strokeWidth="2" strokeDasharray="4 4" />
                <path
                  d="M32 20v24M20 32h24"
                  stroke="currentColor"
                  strokeWidth="3"
                  strokeLinecap="round"
                />
                <path
                  className="upload-arrow-path"
                  d="M32 44V20M24 28l8-8 8 8"
                  stroke="currentColor"
                  strokeWidth="2.5"
                  strokeLinecap="round"
                  strokeLinejoin="round"
                />
              </svg>
            </div>
            <div className="upload-text">
              <strong>Drop audio file here</strong> or click to browse
            </div>
            <div className="upload-hint" id="upload-hint">
              Supports WAV, MP3, FLAC, OGG • Maximum 10 MB
            </div>
          </div>
        )}
      </div>

      {error && (
        <div className="error-message" role="alert">
          <svg className="error-icon" width="20" height="20" viewBox="0 0 20 20" fill="currentColor">
            <path
              fillRule="evenodd"
              d="M10 18a8 8 0 100-16 8 8 0 000 16zM8.707 7.293a1 1 0 00-1.414 1.414L8.586 10l-1.293 1.293a1 1 0 101.414 1.414L10 11.414l1.293 1.293a1 1 0 001.414-1.414L11.414 10l1.293-1.293a1 1 0 00-1.414-1.414L10 8.586 8.707 7.293z"
              clipRule="evenodd"
            />
          </svg>
          {error}
        </div>
      )}
    </div>
  );
};

export default AudioUpload;
