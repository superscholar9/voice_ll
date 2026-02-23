import React, { useState } from 'react';
import { useAuth } from '../../contexts/AuthContext';

interface RegisterProps {
  onSuccess?: () => void;
}

export const Register: React.FC<RegisterProps> = ({ onSuccess }) => {
  const { register } = useAuth();
  const [formData, setFormData] = useState({
    username: '',
    email: '',
    password: '',
    confirmPassword: '',
  });
  const [showPassword, setShowPassword] = useState(false);
  const [showConfirm, setShowConfirm] = useState(false);
  const [error, setError] = useState('');
  const [success, setSuccess] = useState('');
  const [isLoading, setIsLoading] = useState(false);

  const handleChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    setFormData({ ...formData, [e.target.name]: e.target.value });
    setError('');
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (formData.password !== formData.confirmPassword) {
      setError('两次输入的密码不一致');
      return;
    }
    if (formData.password.length < 6) {
      setError('密码长度至少为 6 位');
      return;
    }
    setIsLoading(true);
    try {
      await register(formData.username, formData.email, formData.password, '');
      setSuccess('注册成功！请查收验证邮件。');
      setFormData({ username: '', email: '', password: '', confirmPassword: '' });
      if (onSuccess) {
        setTimeout(() => onSuccess(), 2000);
      }
    } catch (err: any) {
      setError(err.message || '注册失败，请稍后重试');
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <form className="auth-form" onSubmit={handleSubmit}>
      {error && <div className="auth-error">{error}</div>}
      {success && <div className="auth-success">{success}</div>}

      <div className="auth-field">
        <label htmlFor="register-username">用户名</label>
        <div className="auth-input-wrapper">
          <span className="auth-input-icon">
            <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round">
              <path d="M20 21v-2a4 4 0 0 0-4-4H8a4 4 0 0 0-4 4v2" />
              <circle cx="12" cy="7" r="4" />
            </svg>
          </span>
          <input
            id="register-username"
            type="text"
            name="username"
            placeholder="请输入用户名"
            value={formData.username}
            onChange={handleChange}
            autoComplete="username"
            required
          />
        </div>
      </div>

      <div className="auth-field">
        <label htmlFor="register-email">邮箱地址</label>
        <div className="auth-input-wrapper">
          <span className="auth-input-icon">
            <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round">
              <rect x="2" y="4" width="20" height="16" rx="2" />
              <path d="M22 4L12 13 2 4" />
            </svg>
          </span>
          <input
            id="register-email"
            type="email"
            name="email"
            placeholder="请输入邮箱地址"
            value={formData.email}
            onChange={handleChange}
            autoComplete="email"
            spellCheck={false}
            required
          />
        </div>
      </div>

      <div className="auth-field">
        <label htmlFor="register-password">密码</label>
        <div className="auth-input-wrapper">
          <span className="auth-input-icon">
            <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round">
              <rect x="3" y="11" width="18" height="11" rx="2" ry="2" />
              <path d="M7 11V7a5 5 0 0 1 10 0v4" />
            </svg>
          </span>
          <input
            id="register-password"
            type={showPassword ? 'text' : 'password'}
            name="password"
            placeholder="请设置密码（至少 6 位）"
            value={formData.password}
            onChange={handleChange}
            autoComplete="new-password"
            required
          />
          <button
            type="button"
            className="auth-toggle-password"
            onClick={() => setShowPassword(!showPassword)}
            aria-label={showPassword ? '隐藏密码' : '显示密码'}
          >
            {showPassword ? (
              <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round">
                <path d="M17.94 17.94A10.07 10.07 0 0 1 12 20c-7 0-11-8-11-8a18.45 18.45 0 0 1 5.06-5.94" />
                <path d="M9.9 4.24A9.12 9.12 0 0 1 12 4c7 0 11 8 11 8a18.5 18.5 0 0 1-2.16 3.19" />
                <line x1="1" y1="1" x2="23" y2="23" />
              </svg>
            ) : (
              <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round">
                <path d="M1 12s4-8 11-8 11 8 11 8-4 8-11 8-11-8-11-8z" />
                <circle cx="12" cy="12" r="3" />
              </svg>
            )}
          </button>
        </div>
      </div>

      <div className="auth-field">
        <label htmlFor="register-confirm">确认密码</label>
        <div className="auth-input-wrapper">
          <span className="auth-input-icon">
            <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round">
              <path d="M12 22s8-4 8-10V5l-8-3-8 3v7c0 6 8 10 8 10z" />
            </svg>
          </span>
          <input
            id="register-confirm"
            type={showConfirm ? 'text' : 'password'}
            name="confirmPassword"
            placeholder="请再次输入密码"
            value={formData.confirmPassword}
            onChange={handleChange}
            autoComplete="new-password"
            required
          />
          <button
            type="button"
            className="auth-toggle-password"
            onClick={() => setShowConfirm(!showConfirm)}
            aria-label={showConfirm ? '隐藏密码' : '显示密码'}
          >
            {showConfirm ? (
              <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round">
                <path d="M17.94 17.94A10.07 10.07 0 0 1 12 20c-7 0-11-8-11-8a18.45 18.45 0 0 1 5.06-5.94" />
                <path d="M9.9 4.24A9.12 9.12 0 0 1 12 4c7 0 11 8 11 8a18.5 18.5 0 0 1-2.16 3.19" />
                <line x1="1" y1="1" x2="23" y2="23" />
              </svg>
            ) : (
              <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round">
                <path d="M1 12s4-8 11-8 11 8 11 8-4 8-11 8-11-8-11-8z" />
                <circle cx="12" cy="12" r="3" />
              </svg>
            )}
          </button>
        </div>
      </div>

      <button type="submit" className="auth-submit" disabled={isLoading}>
        {isLoading ? (
          <span className="auth-spinner"></span>
        ) : (
          '创建账户'
        )}
      </button>

      <p className="auth-terms">
        注册即表示您同意我们的
        <a href="#" onClick={(e) => e.preventDefault()}>服务条款</a>
        和
        <a href="#" onClick={(e) => e.preventDefault()}>隐私政策</a>
      </p>
    </form>
  );
};
