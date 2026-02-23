import React, { useState } from 'react';
import { api } from '../services/api';
import { useToast } from '../contexts/ToastContext';
import '../styles/TTS.css';

interface TextToSpeechProps {
  onAudioGenerated?: (audioUrl: string) => void;
}

export const TextToSpeech: React.FC<TextToSpeechProps> = ({ onAudioGenerated }) => {
  const [text, setText] = useState('');
  const [language, setLanguage] = useState('auto');
  const [speed, setSpeed] = useState(1.0);
  const [temperature, setTemperature] = useState(0.7);
  const [isLoading, setIsLoading] = useState(false);
  const [audioUrl, setAudioUrl] = useState<string | null>(null);
  const { showToast } = useToast();

  const handleSynthesizeClick = async () => {
    if (!text.trim()) {
      showToast('Please enter text to synthesize', 'error');
      return;
    }

    setIsLoading(true);
    try {
      const url = await api.textToSpeech(text, language, speed, temperature);
      setAudioUrl(url);
      onAudioGenerated?.(url);
      showToast('Text-to-speech synthesis completed successfully', 'success');
    } catch (error: any) {
      showToast(error.message || 'Failed to synthesize text', 'error');
    } finally {
      setIsLoading(false);
    }
  };

  const handleDownload = () => {
    if (!audioUrl) return;

    const link = document.createElement('a');
    link.href = audioUrl;
    link.download = 'tts_output.wav';
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
  };

  return (
    <div className="tts-container">
      <h2>Text-to-Speech Synthesis</h2>

      <div className="tts-form">
        <div className="form-group">
          <label htmlFor="tts-text">Text to Synthesize</label>
          <textarea
            id="tts-text"
            value={text}
            onChange={(e) => setText(e.target.value)}
            placeholder="Enter text to convert to speech..."
            maxLength={5000}
            rows={4}
            disabled={isLoading}
          />
          <small>{text.length} / 5000 characters</small>
        </div>

        <div className="form-row">
          <div className="form-group">
            <label htmlFor="tts-language">Language</label>
            <select
              id="tts-language"
              value={language}
              onChange={(e) => setLanguage(e.target.value)}
              disabled={isLoading}
            >
              <option value="auto">Auto Detect</option>
              <option value="zh">Chinese</option>
              <option value="en">English</option>
              <option value="ja">Japanese</option>
            </select>
          </div>

          <div className="form-group">
            <label htmlFor="tts-speed">
              Speed: {speed.toFixed(1)}x
            </label>
            <input
              id="tts-speed"
              type="range"
              min="0.5"
              max="2.0"
              step="0.1"
              value={speed}
              onChange={(e) => setSpeed(parseFloat(e.target.value))}
              disabled={isLoading}
            />
          </div>

          <div className="form-group">
            <label htmlFor="tts-temperature">
              Temperature: {temperature.toFixed(1)}
            </label>
            <input
              id="tts-temperature"
              type="range"
              min="0.1"
              max="1.0"
              step="0.1"
              value={temperature}
              onChange={(e) => setTemperature(parseFloat(e.target.value))}
              disabled={isLoading}
            />
          </div>
        </div>

        <button
          onClick={handleSynthesizeClick}
          disabled={isLoading || !text.trim()}
          className="btn btn-primary"
        >
          {isLoading ? 'Synthesizing...' : 'Synthesize'}
        </button>
      </div>

      {audioUrl && (
        <div className="tts-result">
          <h3>Generated Audio</h3>
          <audio controls src={audioUrl} />
          <button onClick={handleDownload} className="btn btn-secondary">
            Download Audio
          </button>
        </div>
      )}
    </div>
  );
};

export default TextToSpeech;
