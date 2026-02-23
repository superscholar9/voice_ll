import React, { useState, useRef, useEffect } from 'react';
import type { TextInputProps } from '../types';

const TextInput: React.FC<TextInputProps> = ({
  value,
  onChange,
  disabled = false,
  maxLength = 500,
}) => {
  const [isFocused, setIsFocused] = useState(false);
  const [isTyping, setIsTyping] = useState(false);
  const textareaRef = useRef<HTMLTextAreaElement>(null);
  const typingTimeoutRef = useRef<ReturnType<typeof setTimeout> | null>(null);

  const handleChange = (e: React.ChangeEvent<HTMLTextAreaElement>) => {
    onChange(e.target.value);

    // Trigger typing animation
    setIsTyping(true);
    if (typingTimeoutRef.current) {
      clearTimeout(typingTimeoutRef.current);
    }
    typingTimeoutRef.current = setTimeout(() => {
      setIsTyping(false);
    }, 300);
  };

  useEffect(() => {
    return () => {
      if (typingTimeoutRef.current) {
        clearTimeout(typingTimeoutRef.current);
      }
    };
  }, []);

  const characterCount = value.length;
  const isNearLimit = characterCount > maxLength * 0.8;
  const isAtLimit = characterCount >= maxLength;
  const progress = (characterCount / maxLength) * 100;

  // Calculate line numbers
  const lines = value.split('\n');
  const lineCount = Math.max(lines.length, 6);
  const lineNumbers = Array.from({ length: lineCount }, (_, i) => i + 1);

  // VU meter segments (12 segments)
  const vuSegments = 12;
  const activeSegments = Math.ceil((progress / 100) * vuSegments);

  return (
    <div className="text-input studio-editor">
      <label className="input-label">
        <span className="label-icon">SCRIPT</span>
        <span className="label-text">Recording Script</span>
        <span className="required">*</span>
      </label>

      <div className={`editor-container ${isFocused ? 'focused' : ''} ${isTyping ? 'typing' : ''}`}>
        {/* Grid background */}
        <div className="grid-background" aria-hidden="true" />

        {/* Waveform animation overlay */}
        {isTyping && (
          <div className="waveform-overlay" aria-hidden="true">
            <div className="wave wave-1" />
            <div className="wave wave-2" />
            <div className="wave wave-3" />
          </div>
        )}

        <div className="editor-wrapper">
          {/* Line numbers */}
          <div className="line-numbers" aria-hidden="true">
            {lineNumbers.map((num) => (
              <div key={num} className="line-number">
                {num}
              </div>
            ))}
          </div>

          {/* Text area */}
          <textarea
            ref={textareaRef}
            className="text-area"
            value={value}
            onChange={handleChange}
            onFocus={() => setIsFocused(true)}
            onBlur={() => setIsFocused(false)}
            disabled={disabled}
            maxLength={maxLength}
            placeholder="// Enter your script here...&#10;// This text will be synthesized with the reference voice&#10;// Try something creative!"
            rows={6}
            aria-describedby="text-hint char-counter"
            aria-label="Recording script text input"
          />
        </div>

        {/* Focus indicator border */}
        <div className="focus-border" aria-hidden="true" />
      </div>

      {/* VU Meter and Character Count */}
      <div className="input-footer">
        <div className="input-hint" id="text-hint">
          <span className="hint-icon">REC</span>
          <span className="hint-text">Script will be synthesized with reference voice</span>
        </div>

        {/* VU Meter Style Character Counter */}
        <div className="vu-meter-container">
          <div className="vu-label">LEVEL</div>
          <div className="vu-meter" role="progressbar" aria-valuenow={progress} aria-valuemin={0} aria-valuemax={100}>
            {Array.from({ length: vuSegments }, (_, i) => {
              const isActive = i < activeSegments;
              const isWarning = i >= vuSegments * 0.8;
              const isDanger = i >= vuSegments * 0.95;

              return (
                <div
                  key={i}
                  className={`vu-segment ${isActive ? 'active' : ''} ${isWarning && isActive ? 'warning' : ''} ${isDanger && isActive ? 'danger' : ''}`}
                  aria-hidden="true"
                />
              );
            })}
          </div>
          <div
            className={`char-count ${isNearLimit ? 'near-limit' : ''} ${isAtLimit ? 'at-limit' : ''} ${characterCount === 0 ? 'empty' : ''}`}
            id="char-counter"
            aria-live="polite"
          >
            <span className="count-current">{characterCount}</span>
            <span className="count-separator">/</span>
            <span className="count-max">{maxLength}</span>
          </div>
        </div>
      </div>
    </div>
  );
};

export default TextInput;
