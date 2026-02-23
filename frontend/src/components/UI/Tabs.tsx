import React, { useRef } from 'react';

export interface Tab {
  id: string;
  label: string;
  icon?: React.ReactNode;
}

interface TabsProps {
  items: Tab[];
  active: string;
  onChange: (id: string) => void;
}

export const Tabs: React.FC<TabsProps> = ({ items, active, onChange }) => {
  const tabListRef = useRef<HTMLDivElement>(null);

  const handleKeyDown = (e: React.KeyboardEvent, index: number) => {
    let newIndex = index;

    switch (e.key) {
      case 'ArrowLeft':
        e.preventDefault();
        newIndex = index > 0 ? index - 1 : items.length - 1;
        break;
      case 'ArrowRight':
        e.preventDefault();
        newIndex = index < items.length - 1 ? index + 1 : 0;
        break;
      case 'Home':
        e.preventDefault();
        newIndex = 0;
        break;
      case 'End':
        e.preventDefault();
        newIndex = items.length - 1;
        break;
      default:
        return;
    }

    const newTab = items[newIndex];
    onChange(newTab.id);

    // Focus the new tab
    const tabButtons = tabListRef.current?.querySelectorAll('[role="tab"]');
    if (tabButtons && tabButtons[newIndex]) {
      (tabButtons[newIndex] as HTMLElement).focus();
    }
  };

  return (
    <div className="tabs-container">
      <div
        ref={tabListRef}
        className="tabs-list"
        role="tablist"
        aria-label="Voice tools"
      >
        {items.map((tab, index) => {
          const isActive = tab.id === active;
          return (
            <button
              key={tab.id}
              role="tab"
              aria-selected={isActive}
              aria-controls={`tabpanel-${tab.id}`}
              id={`tab-${tab.id}`}
              tabIndex={isActive ? 0 : -1}
              className="tab"
              onClick={() => onChange(tab.id)}
              onKeyDown={(e) => handleKeyDown(e, index)}
            >
              {tab.icon && <span className="tab-icon">{tab.icon}</span>}
              {tab.label}
            </button>
          );
        })}
      </div>
    </div>
  );
};

export default Tabs;
