import React from 'react';
import '../styles/AudioTools.css';

interface ToolAction {
  label: string;
  onClick: () => void;
}

interface ToolCardProps {
  title: string;
  description: string;
  icon: string;
  actions: ToolAction[];
  isLoading?: boolean;
}

export const ToolCard: React.FC<ToolCardProps> = ({
  title,
  description,
  icon,
  actions,
  isLoading = false,
}) => {
  return (
    <div className="tool-card">
      <div className="tool-card-header">
        <span className="tool-icon">{icon}</span>
        <div className="tool-info">
          <h4 className="tool-title">{title}</h4>
          <p className="tool-description">{description}</p>
        </div>
      </div>

      <div className="tool-actions">
        {actions.map((action, index) => (
          <button
            key={index}
            onClick={action.onClick}
            disabled={isLoading}
            className="tool-action-btn"
          >
            {action.label}
          </button>
        ))}
      </div>
    </div>
  );
};

export default ToolCard;
