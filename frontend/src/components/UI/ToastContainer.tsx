import React from 'react';
import { createPortal } from 'react-dom';
import { useToast } from '../../contexts/ToastContext';
import Toast from './Toast';
import '../../styles/Toast.css';

const ToastContainer: React.FC = () => {
  const { toasts, removeToast } = useToast();

  return createPortal(
    <div className="toast-container" aria-live="polite" aria-atomic="false">
      {toasts.map((toast) => (
        <Toast key={toast.id} toast={toast} onClose={removeToast} />
      ))}
    </div>,
    document.body
  );
};

export default ToastContainer;
