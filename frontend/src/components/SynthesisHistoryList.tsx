import React, { useState, useEffect } from 'react';
import { api } from '../services/api';
import { useToast } from '../contexts/ToastContext';
import '../styles/History.css';

interface HistoryItem {
  id: string;
  job_type: string;
  status: string;
  input_text: string;
  language: string;
  speed: number;
  temperature: number;
  duration_seconds?: number;
  error_message?: string;
  created_at: string;
}

interface SynthesisHistoryListProps {
  limit?: number;
}

export const SynthesisHistoryList: React.FC<SynthesisHistoryListProps> = ({
  limit = 20,
}) => {
  const [items, setItems] = useState<HistoryItem[]>([]);
  const [isLoading, setIsLoading] = useState(false);
  const [offset, setOffset] = useState(0);
  const [total, setTotal] = useState(0);
  const { showToast } = useToast();

  useEffect(() => {
    loadHistory();
  }, []);

  const loadHistory = async () => {
    setIsLoading(true);
    try {
      const response = await api.getHistory(limit, offset);
      setItems(response.items || []);
      setTotal(response.total || 0);
    } catch (error: any) {
      showToast(error.message || 'Failed to load history', 'error');
    } finally {
      setIsLoading(false);
    }
  };

  const handleLoadMore = () => {
    setOffset(offset + limit);
  };

  const formatDate = (dateString: string) => {
    const date = new Date(dateString);
    return date.toLocaleString();
  };

  const getJobTypeLabel = (jobType: string) => {
    return jobType === 'clone' ? 'Voice Clone' : 'Text-to-Speech';
  };

  const getStatusBadge = (status: string) => {
    return status === 'success' ? 'success' : 'error';
  };

  if (isLoading && items.length === 0) {
    return <div className="history-loading">Loading history...</div>;
  }

  if (items.length === 0) {
    return (
      <div className="history-empty">
        <p>No synthesis history yet. Start by creating some audio!</p>
      </div>
    );
  }

  return (
    <div className="history-container">
      <h3>Synthesis History</h3>
      <div className="history-list">
        {items.map((item) => (
          <div key={item.id} className="history-item">
            <div className="history-header">
              <div className="history-title">
                <span className="job-type">{getJobTypeLabel(item.job_type)}</span>
                <span className={`status-badge status-${getStatusBadge(item.status)}`}>
                  {item.status}
                </span>
              </div>
              <div className="history-date">{formatDate(item.created_at)}</div>
            </div>

            <div className="history-content">
              <div className="history-text">
                <strong>Text:</strong> {item.input_text.substring(0, 100)}
                {item.input_text.length > 100 ? '...' : ''}
              </div>

              <div className="history-details">
                <span className="detail">Language: {item.language}</span>
                <span className="detail">Speed: {item.speed.toFixed(1)}x</span>
                <span className="detail">Temperature: {item.temperature.toFixed(1)}</span>
                {item.duration_seconds && (
                  <span className="detail">Duration: {item.duration_seconds.toFixed(1)}s</span>
                )}
              </div>

              {item.error_message && (
                <div className="history-error">
                  <strong>Error:</strong> {item.error_message}
                </div>
              )}
            </div>
          </div>
        ))}
      </div>

      {offset + limit < total && (
        <button
          onClick={handleLoadMore}
          disabled={isLoading}
          className="btn btn-secondary"
        >
          {isLoading ? 'Loading...' : 'Load More'}
        </button>
      )}

      <div className="history-footer">
        Showing {items.length} of {total} items
      </div>
    </div>
  );
};

export default SynthesisHistoryList;
