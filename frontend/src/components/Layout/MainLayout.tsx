import React, { useState, useEffect } from 'react';
import api from '../../services/api';
import SynthesisHistoryList from '../SynthesisHistoryList';
import type { HealthResponse } from '../../types';

interface MainLayoutProps {
  children: React.ReactNode;
}

interface Stats {
  totalSyntheses: number;
  avgProcessingTime: string;
  uptime: string;
}

export const MainLayout: React.FC<MainLayoutProps> = ({ children }) => {
  const [backendHealth, setBackendHealth] = useState<HealthResponse | null>(null);
  const [backendStatus, setBackendStatus] = useState<'checking' | 'online' | 'offline'>('checking');
  const [stats, setStats] = useState<Stats>({
    totalSyntheses: 0,
    avgProcessingTime: '0s',
    uptime: '0m',
  });

  useEffect(() => {
    checkBackendHealth();
    const interval = setInterval(checkBackendHealth, 30000); // Check every 30s
    return () => clearInterval(interval);
  }, []);

  const checkBackendHealth = async () => {
    try {
      const health = await api.checkHealth();
      setBackendHealth(health);
      setBackendStatus('online');

      // Update stats from health response
      if (health.uptime_seconds) {
        const minutes = Math.floor(health.uptime_seconds / 60);
        const hours = Math.floor(minutes / 60);
        const days = Math.floor(hours / 24);

        let uptimeStr = '';
        if (days > 0) uptimeStr = `${days}d ${hours % 24}h`;
        else if (hours > 0) uptimeStr = `${hours}h ${minutes % 60}m`;
        else uptimeStr = `${minutes}m`;

        setStats(prev => ({ ...prev, uptime: uptimeStr }));
      }

    } catch (error) {
      setBackendStatus('offline');
      setBackendHealth(null);
    }
  };

  return (
    <main id="main-content" className="main-layout-asymmetric" role="main">
      {/* Hero Section (Left 60%) + Status Panel (Right 40%) */}
      <div className="layout-hero-section">
        <div className="hero-content">
          <div className="hero-badge">
            <span className="badge-icon">AI</span>
            <span className="badge-text">Powered by GPT-SoVITS</span>
          </div>
          <h1 className="hero-title">Voice Cloning Studio</h1>
          <p className="hero-subtitle">
            Transform any voice into speech with AI-powered voice cloning technology.
            Upload reference audio and generate high-quality synthesized speech in seconds.
          </p>
          <div className="hero-features">
            <div className="feature-item">
              <span className="feature-icon">⚡</span>
              <span className="feature-text">Fast Processing</span>
            </div>
            <div className="feature-item">
              <span className="feature-icon">🎯</span>
              <span className="feature-text">High Accuracy</span>
            </div>
            <div className="feature-item">
              <span className="feature-icon">🌐</span>
              <span className="feature-text">Multi-Language</span>
            </div>
          </div>
        </div>

        <div className="status-panel">
          <div className="status-panel-header">
            <h3 className="status-panel-title">System Status</h3>
            <button
              className="status-refresh-btn"
              onClick={checkBackendHealth}
              aria-label="Refresh status"
            >
              ↻
            </button>
          </div>

          {/* Backend Status Indicator */}
          <div className="status-card">
            <div className="status-card-header">
              <span className="status-card-label">Backend</span>
              <div className={`status-badge status-${backendStatus}`}>
                <span className="status-dot"></span>
                <span className="status-text">
                  {backendStatus === 'checking' && 'Checking...'}
                  {backendStatus === 'online' && 'Online'}
                  {backendStatus === 'offline' && 'Offline'}
                </span>
              </div>
            </div>
            {backendHealth && (
              <div className="status-card-details">
                <div className="status-detail-item">
                  <span className="detail-label">Version</span>
                  <span className="detail-value">{backendHealth.version}</span>
                </div>
                <div className="status-detail-item">
                  <span className="detail-label">SoVITS</span>
                  <span className="detail-value">
                    {backendHealth.sovits_available ? 'Available' : 'Unavailable'}
                  </span>
                </div>
              </div>
            )}
          </div>

          {/* Quick Stats */}
          <div className="stats-grid">
            <div className="stat-card">
              <div className="stat-icon">📊</div>
              <div className="stat-content">
                <div className="stat-value">{stats.totalSyntheses}</div>
                <div className="stat-label">Total Syntheses</div>
              </div>
            </div>
            <div className="stat-card">
              <div className="stat-icon">⏱</div>
              <div className="stat-content">
                <div className="stat-value">{stats.avgProcessingTime}</div>
                <div className="stat-label">Avg Time</div>
              </div>
            </div>
            <div className="stat-card">
              <div className="stat-icon">🕐</div>
              <div className="stat-content">
                <div className="stat-value">{stats.uptime}</div>
                <div className="stat-label">Uptime</div>
              </div>
            </div>
          </div>

          {/* Recent Activity */}
          <div className="activity-section">
            <h4 className="activity-title">Recent Activity</h4>
            <SynthesisHistoryList limit={5} />
          </div>
        </div>
      </div>

      {/* Main Content Area - Diagonal Grid */}
      <div className="layout-main-content">
        <div className="content-wrapper">
          {children}
        </div>
      </div>
    </main>
  );
};

export default MainLayout;
