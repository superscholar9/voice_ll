import { useState } from 'react';
import { AuthProvider } from './contexts/AuthContext';
import { ToastProvider } from './contexts/ToastContext';
import { Navbar } from './components/Layout/Navbar';
import { MainLayout } from './components/Layout/MainLayout';
import { Tabs, Tab } from './components/UI/Tabs';
import VoiceClone from './components/VoiceClone';
import TextToSpeech from './components/TextToSpeech';
import AudioTools from './components/AudioTools';
import ToastContainer from './components/UI/ToastContainer';
import './styles/App.css';
import './styles/animations.css';
import './styles/design-tokens.css';

function App() {
  const [activeTab, setActiveTab] = useState('clone');

  const tabs: Tab[] = [
    { id: 'clone', label: 'Voice Cloning' },
    { id: 'tts', label: 'Text to Speech' },
    { id: 'tools', label: 'Audio Tools' },
  ];

  return (
    <AuthProvider>
      <ToastProvider>
        <div className="app-shell">
          <a href="#main-content" className="skip-link">
            Skip to main content
          </a>

          <Navbar />

          <MainLayout>
            <div className="tabs-wrapper">
              <Tabs items={tabs} active={activeTab} onChange={setActiveTab} />
            </div>

            <div className="tab-content">
              {activeTab === 'clone' && (
                <div
                  role="tabpanel"
                  id="tabpanel-clone"
                  aria-labelledby="tab-clone"
                  className="tab-panel"
                >
                  <VoiceClone />
                </div>
              )}

              {activeTab === 'tts' && (
                <div
                  role="tabpanel"
                  id="tabpanel-tts"
                  aria-labelledby="tab-tts"
                  className="tab-panel"
                >
                  <TextToSpeech />
                </div>
              )}

              {activeTab === 'tools' && (
                <div
                  role="tabpanel"
                  id="tabpanel-tools"
                  aria-labelledby="tab-tools"
                  className="tab-panel"
                >
                  <AudioTools />
                </div>
              )}
            </div>
          </MainLayout>
        </div>
        <ToastContainer />
      </ToastProvider>
    </AuthProvider>
  );
}

export default App;
