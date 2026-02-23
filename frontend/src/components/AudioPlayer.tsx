import React, { useRef, useState, useEffect } from 'react';
import type { AudioPlayerProps } from '../types';
import '../styles/AudioPlayer.css';

const AudioPlayer: React.FC<AudioPlayerProps> = ({ audioUrl, onClose }) => {
  const audioRef = useRef<HTMLAudioElement>(null);
  const modalRef = useRef<HTMLDivElement>(null);
  const analyserRef = useRef<AnalyserNode | null>(null);
  const animationFrameRef = useRef<number | null>(null);
  const canvasRef = useRef<HTMLCanvasElement>(null);

  const [isPlaying, setIsPlaying] = useState(false);
  const [currentTime, setCurrentTime] = useState(0);
  const [duration, setDuration] = useState(0);
  const [volume, setVolume] = useState(1);
  const [showVolumeSlider, setShowVolumeSlider] = useState(false);
  const [waveformHeights, setWaveformHeights] = useState<number[]>([0.3, 0.5, 0.7, 0.5, 0.3]);

  // Setup audio context and analyser for visualization
  useEffect(() => {
    const audio = audioRef.current;
    if (!audio) return;

    try {
      const audioContext = new (window.AudioContext || (window as any).webkitAudioContext)();
      const analyser = audioContext.createAnalyser();
      const source = audioContext.createMediaElementSource(audio);

      analyser.fftSize = 256;
      source.connect(analyser);
      analyser.connect(audioContext.destination);

      analyserRef.current = analyser;
    } catch (error) {
      console.warn('Audio visualization not available:', error);
    }

    return () => {
      if (animationFrameRef.current) {
        cancelAnimationFrame(animationFrameRef.current);
      }
    };
  }, []);

  // Animate waveform bars based on audio frequency data
  useEffect(() => {
    if (!isPlaying || !analyserRef.current) {
      setWaveformHeights([0.3, 0.5, 0.7, 0.5, 0.3]);
      return;
    }

    const analyser = analyserRef.current;
    const dataArray = new Uint8Array(analyser.frequencyBinCount);

    const animate = () => {
      analyser.getByteFrequencyData(dataArray);

      // Sample 5 frequency ranges for the 5 bars
      const bars = [
        dataArray[2] / 255,   // Low
        dataArray[8] / 255,   // Low-mid
        dataArray[16] / 255,  // Mid
        dataArray[24] / 255,  // Mid-high
        dataArray[32] / 255   // High
      ];

      // Add minimum height and smooth animation
      const heights = bars.map(val => Math.max(0.2, val * 0.8 + 0.2));
      setWaveformHeights(heights);

      animationFrameRef.current = requestAnimationFrame(animate);
    };

    animate();

    return () => {
      if (animationFrameRef.current) {
        cancelAnimationFrame(animationFrameRef.current);
      }
    };
  }, [isPlaying]);

  // Focus trap and Escape key handler
  useEffect(() => {
    const handleKeyDown = (e: KeyboardEvent) => {
      if (e.key === 'Escape') {
        onClose();
      }
    };

    document.addEventListener('keydown', handleKeyDown);
    modalRef.current?.focus();

    return () => {
      document.removeEventListener('keydown', handleKeyDown);
    };
  }, [onClose]);

  useEffect(() => {
    const audio = audioRef.current;
    if (!audio) return;

    const handleTimeUpdate = () => setCurrentTime(audio.currentTime);
    const handleDurationChange = () => setDuration(audio.duration);
    const handleEnded = () => setIsPlaying(false);

    audio.addEventListener('timeupdate', handleTimeUpdate);
    audio.addEventListener('durationchange', handleDurationChange);
    audio.addEventListener('ended', handleEnded);

    return () => {
      audio.removeEventListener('timeupdate', handleTimeUpdate);
      audio.removeEventListener('durationchange', handleDurationChange);
      audio.removeEventListener('ended', handleEnded);
    };
  }, []);

  const togglePlay = () => {
    const audio = audioRef.current;
    if (!audio) return;

    if (isPlaying) {
      audio.pause();
    } else {
      audio.play();
    }
    setIsPlaying(!isPlaying);
  };

  const handleSeek = (e: React.ChangeEvent<HTMLInputElement>) => {
    const audio = audioRef.current;
    if (!audio) return;

    const newTime = parseFloat(e.target.value);
    audio.currentTime = newTime;
    setCurrentTime(newTime);
  };

  const handleVolumeChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const audio = audioRef.current;
    if (!audio) return;

    const newVolume = parseFloat(e.target.value);
    audio.volume = newVolume;
    setVolume(newVolume);
  };

  const handleDownload = () => {
    if (!audioUrl) return;

    const link = document.createElement('a');
    link.href = audioUrl;
    link.download = `cloned-voice-${Date.now()}.wav`;
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
  };

  const formatTime = (time: number): string => {
    if (isNaN(time)) return '0:00';
    const minutes = Math.floor(time / 60);
    const seconds = Math.floor(time % 60);
    return `${minutes}:${seconds.toString().padStart(2, '0')}`;
  };

  if (!audioUrl) return null;

  const progressPercentage = duration > 0 ? (currentTime / duration) * 100 : 0;

  return (
    <div className="audio-player-overlay" role="dialog" aria-modal="true" aria-labelledby="player-title">
      <div className="audio-player-modal studio-theme" ref={modalRef} tabIndex={-1}>
        {/* Spectrum analyzer background */}
        <canvas ref={canvasRef} className="spectrum-background" aria-hidden="true" />

        <div className="player-header">
          <div className="header-content">
            <div className="studio-badge">
              <span className="badge-icon">🎚️</span>
              <span className="badge-text">AUDIO WORKSTATION</span>
            </div>
            <div className="header-text">
              <h3 id="player-title" className="studio-title">Master Track</h3>
              <p className="header-subtitle">Voice Clone Output</p>
            </div>
          </div>
          <button className="close-btn neon-btn" onClick={onClose} aria-label="Close audio player">
            ✕
          </button>
        </div>

        <div className="player-content">
          <audio ref={audioRef} src={audioUrl} preload="metadata" />

          {/* Professional waveform visualization */}
          <div className="waveform-container">
            <div className="waveform-display">
              {waveformHeights.map((height, index) => (
                <div
                  key={index}
                  className={`wave-bar ${isPlaying ? 'active' : ''}`}
                  style={{
                    height: `${height * 100}%`,
                    animationDelay: `${index * 0.1}s`
                  }}
                />
              ))}
            </div>
            <div className="waveform-label">FREQUENCY SPECTRUM</div>
          </div>

          {/* Professional progress bar with neon styling */}
          <div className="progress-section">
            <div className="progress-bar-wrapper">
              <div className="progress-bar-bg">
                <div
                  className="progress-bar-fill neon-progress"
                  style={{ width: `${progressPercentage}%` }}
                />
                <div className="progress-glow" style={{ width: `${progressPercentage}%` }} />
              </div>
              <input
                type="range"
                className="seek-slider"
                min="0"
                max={duration || 0}
                value={currentTime}
                onChange={handleSeek}
                step="0.1"
                aria-label="Audio progress"
                aria-valuemin={0}
                aria-valuemax={duration || 0}
                aria-valuenow={currentTime}
                aria-valuetext={`${formatTime(currentTime)} of ${formatTime(duration)}`}
              />
            </div>
            <div className="time-info">
              <div className="time-display digital-clock" aria-label="Current time">
                {formatTime(currentTime)}
              </div>
              <div className="progress-percentage">{Math.round(progressPercentage)}%</div>
              <div className="time-display digital-clock" aria-label="Total duration">
                {formatTime(duration)}
              </div>
            </div>
          </div>

          {/* Professional control panel */}
          <div className="player-controls">
            <button
              className={`play-btn neon-btn ${isPlaying ? 'playing' : ''}`}
              onClick={togglePlay}
              aria-label={isPlaying ? 'Pause audio' : 'Play audio'}
            >
              <span className="play-icon">{isPlaying ? '⏸' : '▶'}</span>
              <span className="btn-label">{isPlaying ? 'PAUSE' : 'PLAY'}</span>
            </button>

            <div className="volume-control">
              <button
                className="volume-btn neon-btn"
                onClick={() => setShowVolumeSlider(!showVolumeSlider)}
                aria-label={`Volume: ${Math.round(volume * 100)}%`}
                aria-expanded={showVolumeSlider}
              >
                <span className="volume-icon">
                  {volume === 0 ? '🔇' : volume < 0.5 ? '🔉' : '🔊'}
                </span>
                <span className="btn-label">VOLUME</span>
              </button>
              {showVolumeSlider && (
                <div className="volume-slider-wrapper">
                  <input
                    type="range"
                    className="volume-slider neon-slider"
                    min="0"
                    max="1"
                    value={volume}
                    onChange={handleVolumeChange}
                    step="0.01"
                    aria-label="Volume control"
                    aria-valuemin={0}
                    aria-valuemax={1}
                    aria-valuenow={volume}
                    aria-valuetext={`${Math.round(volume * 100)}%`}
                  />
                  <span className="volume-percentage digital-clock">{Math.round(volume * 100)}%</span>
                </div>
              )}
            </div>

            <button className="download-btn neon-btn export" onClick={handleDownload} aria-label="Download audio file">
              <span className="download-icon">⬇</span>
              <span className="btn-label">EXPORT MASTER</span>
            </button>
          </div>
        </div>
      </div>
    </div>
  );
};

export default AudioPlayer;
