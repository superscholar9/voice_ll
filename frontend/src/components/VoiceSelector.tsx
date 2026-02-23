import React, { useState } from 'react';
import '../styles/TTS.css';

interface VoiceSelectorProps {
  onVoiceSelect?: (voiceId: string) => void;
  disabled?: boolean;
}

export const VoiceSelector: React.FC<VoiceSelectorProps> = ({
  onVoiceSelect,
  disabled = false,
}) => {
  const [selectedVoice, setSelectedVoice] = useState('default');

  const voices = [
    { id: 'default', name: 'Default Voice', description: 'Standard voice' },
    { id: 'female', name: 'Female Voice', description: 'Female speaker' },
    { id: 'male', name: 'Male Voice', description: 'Male speaker' },
    { id: 'child', name: 'Child Voice', description: 'Child speaker' },
  ];

  const handleVoiceChange = (voiceId: string) => {
    setSelectedVoice(voiceId);
    onVoiceSelect?.(voiceId);
  };

  return (
    <div className="voice-selector">
      <h3>Select Voice</h3>
      <div className="voice-options">
        {voices.map((voice) => (
          <div key={voice.id} className="voice-option">
            <input
              type="radio"
              id={`voice-${voice.id}`}
              name="voice"
              value={voice.id}
              checked={selectedVoice === voice.id}
              onChange={() => handleVoiceChange(voice.id)}
              disabled={disabled}
            />
            <label htmlFor={`voice-${voice.id}`}>
              <div className="voice-name">{voice.name}</div>
              <div className="voice-description">{voice.description}</div>
            </label>
          </div>
        ))}
      </div>
    </div>
  );
};

export default VoiceSelector;
