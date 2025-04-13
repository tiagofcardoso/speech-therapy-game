import React, { useState, useEffect, useCallback, createContext, useContext } from 'react';
import './SimpleToast.css';

// Create a context for managing notifications globally
const ToastContext = createContext();

export const ToastProvider = ({ children }) => {
    const [toasts, setToasts] = useState([]);

    // Add a new toast notification
    const addToast = useCallback((message, type = 'info', duration = 5000) => {
        const id = Date.now();

        setToasts(prevToasts => [
            ...prevToasts,
            { id, message, type, duration }
        ]);

        return id;
    }, []);

    // Remove a toast notification by ID
    const removeToast = useCallback((id) => {
        setToasts(prevToasts =>
            prevToasts.filter(toast => toast.id !== id)
        );
    }, []);

    // Helper functions for different toast types
    const showInfo = useCallback((message, duration) =>
        addToast(message, 'info', duration), [addToast]);

    const showSuccess = useCallback((message, duration) =>
        addToast(message, 'success', duration), [addToast]);

    const showWarning = useCallback((message, duration) =>
        addToast(message, 'warning', duration), [addToast]);

    const showError = useCallback((message, duration) =>
        addToast(message, 'error', duration), [addToast]);

    return (
        <ToastContext.Provider
            value={{
                toasts,
                addToast,
                removeToast,
                showInfo,
                showSuccess,
                showWarning,
                showError
            }}
        >
            {children}
            <ToastContainer />
        </ToastContext.Provider>
    );
};

// Custom hook to use the toast context
export const useToast = () => {
    const context = useContext(ToastContext);
    if (!context) {
        throw new Error('useToast must be used within a ToastProvider');
    }
    return context;
};

// Individual toast notification component
const Toast = ({ id, message, type, duration, onRemove }) => {
    useEffect(() => {
        if (duration <= 0) return;

        const timer = setTimeout(() => {
            onRemove(id);
        }, duration);

        return () => clearTimeout(timer);
    }, [id, duration, onRemove]);

    return (
        <div className={`simple-toast simple-toast-${type}`}>
            <div className="simple-toast-content">
                {getToastIcon(type)}
                <p>{message}</p>
            </div>
            <button
                className="simple-toast-close"
                onClick={() => onRemove(id)}
                aria-label="Close notification"
            >
                ×
            </button>
        </div>
    );
};

// Container for all active toast notifications
const ToastContainer = () => {
    const { toasts, removeToast } = useContext(ToastContext);

    return (
        <div className="simple-toast-container">
            {toasts.map(toast => (
                <Toast
                    key={toast.id}
                    id={toast.id}
                    message={toast.message}
                    type={toast.type}
                    duration={toast.duration}
                    onRemove={removeToast}
                />
            ))}
        </div>
    );
};

// Helper function to get the appropriate icon for each toast type
const getToastIcon = (type) => {
    switch (type) {
        case 'success':
            return <span className="toast-icon">✓</span>;
        case 'error':
            return <span className="toast-icon">✕</span>;
        case 'warning':
            return <span className="toast-icon">⚠</span>;
        case 'info':
        default:
            return <span className="toast-icon">ℹ</span>;
    }
};

export default ToastContainer;