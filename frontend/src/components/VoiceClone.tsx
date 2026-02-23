import React, { useState, useEffect } from 'react';
import AudioUpload from './AudioUpload';
import TextInput from './TextInput';
import AudioPlayer from './AudioPlayer';
import api from '../services/api';
import type { VoiceCloneFormState } from '../types';

const VoiceClone: React.FC = () => {
  const [formState, setFormState] = useState<VoiceCloneFormState>({
    referenceAudio: null,
    targetText: '',
    isLoading: false,
    error: null,
    generatedAudioUrl: null,
  });

  const [language, setLanguage] = useState<string>('auto');
  const [speed, setSpeed] = useState<number>(1.0);
  const [temperature, setTemperature] = useState<number>(0.7);
  const [showAdvanced, setShowAdvanced] = useState<boolean>(false);

  // Cleanup blob URL on unmount
  useEffect(() => {
    return () => {
      if (formState.generatedAudioUrl) {
        URL.revokeObjectURL(formState.generatedAudioUrl);
      }
    };
  }, [formState.generatedAudioUrl]);

  const handleFileSelect = (file: File | null) => {
    setFormState((prev) => ({
      ...prev,
      referenceAudio: file,
      error: null,
    }));
  };

  const handleTextChange = (text: string) => {
    setFormState((prev) => ({
      ...prev,
      targetText: text,
      error: null,
    }));
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();

    // Validation
    if (!formState.referenceAudio) {
      setFormState((prev) => ({
        ...prev,
        error: 'Please upload a reference audio file',
      }));
      return;
    }

    if (!formState.targetText.trim()) {
      setFormState((prev) => ({
        ...prev,
        error: 'Please enter the target text',
      }));
      return;
    }

    setFormState((prev) => ({
      ...prev,
      isLoading: true,
      error: null,
      generatedAudioUrl: null,
    }));

    try {
      const blobUrl = await api.cloneVoice(
        formState.referenceAudio,
        formState.targetText,
        language,
        speed,
        temperature
      );

      setFormState((prev) => ({
        ...prev,
        isLoading: false,
        generatedAudioUrl: blobUrl,
      }));
    } catch (error: any) {
      setFormState((prev) => ({
        ...prev,
        isLoading: false,
        error: error.message || 'An unexpected error occurred',
      }));
    }
  };

  const handleReset = () => {
    setFormState({
      referenceAudio: null,
      targetText: '',
      isLoading: false,
      error: null,
      generatedAudioUrl: null,
    });
  };

  const handleClosePlayer = () => {
    // Revoke blob URL to free memory
    if (formState.generatedAudioUrl) {
      URL.revokeObjectURL(formState.generatedAudioUrl);
    }
    setFormState((prev) => ({
      ...prev,
      generatedAudioUrl: null,
    }));
  };

  const isFormValid = formState.referenceAudio && formState.targetText.trim();

  return (
    <div className="voice-clone-container">
      <form className="clone-form" onSubmit={handleSubmit}>
        <div className="form-grid">
          <AudioUpload
            onFileSelect={handleFileSelect}
            selectedFile={formState.referenceAudio}
            disabled={formState.isLoading}
          />

          <TextInput
            value={formState.targetText}
            onChange={handleTextChange}
            disabled={formState.isLoading}
          />
        </div>

        <div className="advanced-options-wrapper">
          <button
            type="button"
            className="advanced-toggle"
            onClick={() => setShowAdvanced(!showAdvanced)}
            aria-expanded={showAdvanced}
          >
            <span className="toggle-icon">{showAdvanced ? '▼' : '▶'}</span>
            Advanced Options
          </button>

          {showAdvanced && (
            <div className="advanced-options">
              <div className="options-grid">
                <div className="option-group">
                  <label htmlFor="language">
                    <span className="option-icon">🌐</span>
                    Language
                  </label>
                  <select
                    id="language"
                    value={language}
                    onChange={(e) => setLanguage(e.target.value)}
                    disabled={formState.isLoading}
                    className="option-select"
                  >
                    <option value="auto">Auto Detect</option>
                    <option value="zh">Chinese</option>
                    <option value="en">English</option>
                    <option value="ja">Japanese</option>
                  </select>
                </div>

                <div className="option-group">
                  <label htmlFor="speed">
                    <span className="option-icon">⚡</span>
                    Speed: <strong>{speed.toFixed(1)}x</strong>
                  </label>
                  <input
                    id="speed"
                    type="range"
                    min="0.5"
                    max="2.0"
                    step="0.1"
                    value={speed}
                    onChange={(e) => setSpeed(parseFloat(e.target.value))}
                    disabled={formState.isLoading}
                    className="option-slider"
                    aria-valuetext={`${speed.toFixed(1)} times speed`}
                  />
                  <div className="slider-labels">
                    <span>0.5x</span>
                    <span>1.0x</span>
                    <span>2.0x</span>
                  </div>
                </div>

                <div className="option-group">
                  <label htmlFor="temperature">
                    <span className="option-icon">🎚</span>
                    Temperature: <strong>{temperature.toFixed(1)}</strong>
                  </label>
                  <input
                    id="temperature"
                    type="range"
                    min="0.1"
                    max="1.0"
                    step="0.1"
                    value={temperature}
                    onChange={(e) => setTemperature(parseFloat(e.target.value))}
                    disabled={formState.isLoading}
                    className="option-slider"
                    aria-valuetext={`Temperature ${temperature.toFixed(1)}`}
                  />
                  <div className="slider-labels">
                    <span>0.1</span>
                    <span>0.5</span>
                    <span>1.0</span>
                  </div>
                </div>
              </div>
            </div>
          )}
        </div>

        {formState.error && (
          <div className="error-banner" role="alert">
            <span className="error-icon" aria-hidden="true">⚠</span>
            <span className="error-text">{formState.error}</span>
          </div>
        )}

        <div className="form-actions">
          <button
            type="button"
            className="btn btn-secondary"
            onClick={handleReset}
            disabled={formState.isLoading}
          >
            Reset
          </button>
          <button
            type="submit"
            className="btn btn-primary"
            disabled={!isFormValid || formState.isLoading}
          >
            {formState.isLoading ? (
              <>
                <span className="spinner"></span>
                Cloning Voice…
              </>
            ) : (
              'Clone Voice'
            )}
          </button>
        </div>
      </form>

      {formState.generatedAudioUrl && (
        <AudioPlayer
          audioUrl={formState.generatedAudioUrl}
          onClose={handleClosePlayer}
        />
      )}
    </div>
  );
};

export default VoiceClone;
