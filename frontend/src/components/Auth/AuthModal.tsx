import React, { useEffect, useState } from 'react';
import { createPortal } from 'react-dom';
import { Login } from './Login';
import { Register } from './Register';
import '../../styles/Auth.css';

interface AuthModalProps {
  isOpen: boolean;
  onClose: () => void;
  initialTab?: 'login' | 'register';
  children?: React.ReactNode;
}

export const AuthModal: React.FC<AuthModalProps> = ({
  isOpen,
  onClose,
  initialTab = 'login',
}) => {
  const [activeTab, setActiveTab] = useState<'login' | 'register'>(initialTab);

  useEffect(() => {
    if (isOpen) {
      setActiveTab(initialTab);
      document.body.style.overflow = 'hidden';
    }
    return () => {
      document.body.style.overflow = '';
    };
  }, [isOpen, initialTab]);

  useEffect(() => {
    if (!isOpen) return;
    const handleEscape = (e: KeyboardEvent) => {
      if (e.key === 'Escape') onClose();
    };
    document.addEventListener('keydown', handleEscape);
    return () => document.removeEventListener('keydown', handleEscape);
  }, [isOpen, onClose]);

  if (!isOpen) return null;

  const modalContent = (
    <div className="auth-fullscreen" role="dialog" aria-modal="true">
      {/* Left branding panel */}
      <div className="auth-brand-panel">
        <button className="auth-back-btn" onClick={onClose} aria-label="返回">
          <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
            <path d="M19 12H5M12 19l-7-7 7-7" />
          </svg>
          <span>返回首页</span>
        </button>

        <div className="auth-brand-logo">
          <svg width="28" height="28" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.5">
            <path d="M12 1a3 3 0 0 0-3 3v8a3 3 0 0 0 6 0V4a3 3 0 0 0-3-3z" />
            <path d="M19 10v2a7 7 0 0 1-14 0v-2" />
            <line x1="12" y1="19" x2="12" y2="23" />
            <line x1="8" y1="23" x2="16" y2="23" />
          </svg>
          <span>VoiceClone</span>
        </div>

        <div className="auth-brand-content">
          <h1 className="auth-brand-title">
            AI 驱动的<br />语音克隆平台
          </h1>
          <p className="auth-brand-subtitle">
            上传参考音频，输入任意文本，即刻生成高质量克隆语音。
            支持中英日多语言，毫秒级响应，让创作更自由。
          </p>
        </div>

        <div className="auth-brand-features">
          <div className="auth-feature-item">
            <div className="auth-feature-icon">
              <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.5">
                <path d="M12 1a3 3 0 0 0-3 3v8a3 3 0 0 0 6 0V4a3 3 0 0 0-3-3z" />
                <path d="M19 10v2a7 7 0 0 1-14 0v-2" />
              </svg>
            </div>
            <div>
              <div className="auth-feature-title">高保真克隆</div>
              <div className="auth-feature-desc">基于 GPT-SoVITS 深度学习模型</div>
            </div>
          </div>
          <div className="auth-feature-item">
            <div className="auth-feature-icon">
              <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.5">
                <circle cx="12" cy="12" r="10" />
                <path d="M2 12h20M12 2a15.3 15.3 0 0 1 4 10 15.3 15.3 0 0 1-4 10 15.3 15.3 0 0 1-4-10 15.3 15.3 0 0 1 4-10z" />
              </svg>
            </div>
            <div>
              <div className="auth-feature-title">多语言支持</div>
              <div className="auth-feature-desc">支持中文、英文、日文自动识别</div>
            </div>
          </div>
          <div className="auth-feature-item">
            <div className="auth-feature-icon">
              <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.5">
                <polygon points="13 2 3 14 12 14 11 22 21 10 12 10 13 2" />
              </svg>
            </div>
            <div>
              <div className="auth-feature-title">极速响应</div>
              <div className="auth-feature-desc">秒级生成，实时预览播放</div>
            </div>
          </div>
        </div>
      </div>

      {/* Right form panel */}
      <div className="auth-form-panel">
        <div className="auth-form-container">
          <div className="auth-form-header">
            <div className="auth-form-icon">
              <svg width="32" height="32" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.5">
                <path d="M12 1a3 3 0 0 0-3 3v8a3 3 0 0 0 6 0V4a3 3 0 0 0-3-3z" />
                <path d="M19 10v2a7 7 0 0 1-14 0v-2" />
                <line x1="12" y1="19" x2="12" y2="23" />
                <line x1="8" y1="23" x2="16" y2="23" />
              </svg>
            </div>
            <h2 className="auth-form-title">
              {activeTab === 'login' ? '欢迎回来' : '创建账户'}
            </h2>
            <p className="auth-form-subtitle">
              {activeTab === 'login'
                ? '登录您的账户开始语音创作'
                : '注册新账户，开启 AI 语音之旅'}
            </p>
          </div>

          <div className="auth-tabs">
            <button
              className={`auth-tab ${activeTab === 'login' ? 'active' : ''}`}
              onClick={() => setActiveTab('login')}
            >
              登录
            </button>
            <button
              className={`auth-tab ${activeTab === 'register' ? 'active' : ''}`}
              onClick={() => setActiveTab('register')}
            >
              注册
            </button>
          </div>

          {activeTab === 'login' ? (
            <Login onSuccess={onClose} />
          ) : (
            <Register onSuccess={onClose} />
          )}
        </div>
      </div>
    </div>
  );

  return createPortal(modalContent, document.body);
};
