import React, { useState } from 'react';
import { useAuth } from '../../contexts/AuthContext';
import { AuthModal } from '../Auth/AuthModal';
import { UserMenu } from './UserMenu';
import '../../styles/Navbar.css';

export const Navbar: React.FC = () => {
  const { user, isAuthenticated, logout } = useAuth();
  const [showAuthModal, setShowAuthModal] = useState(false);
  const [authTab, setAuthTab] = useState<'login' | 'register'>('login');

  const handleLogout = async () => {
    await logout();
  };

  const openLogin = () => {
    setAuthTab('login');
    setShowAuthModal(true);
  };

  const openRegister = () => {
    setAuthTab('register');
    setShowAuthModal(true);
  };

  return (
    <header className="navbar" role="banner">
      <div className="navbar-content">
        <div className="logo">
          <a href="/" aria-label="VoiceClone.ai Home">
            VoiceClone.ai
          </a>
        </div>

        <nav aria-label="Main navigation">
          <ul role="list">
            <li><a href="#tts">Text to Speech</a></li>
            <li><a href="#clone">Voice Cloning</a></li>
            <li><a href="#tools">Audio Tools</a></li>
          </ul>
        </nav>

        <div className="navbar-actions">
          {isAuthenticated ? (
            <UserMenu username={user?.username || 'User'} onLogout={handleLogout} />
          ) : (
            <>
              <button className="btn btn-ghost" onClick={openLogin}>Login</button>
              <button className="btn btn-primary" onClick={openRegister}>Get Started</button>
            </>
          )}
        </div>
      </div>

      <AuthModal
        isOpen={showAuthModal}
        onClose={() => setShowAuthModal(false)}
        initialTab={authTab}
      />
    </header>
  );
};

export default Navbar;
