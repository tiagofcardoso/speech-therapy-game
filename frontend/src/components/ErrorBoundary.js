import React from 'react';
import * as Sentry from '@sentry/react';

class ErrorBoundary extends React.Component {
    constructor(props) {
        super(props);
        this.state = { hasError: false, error: null };
    }

    static getDerivedStateFromError(error) {
        return { hasError: true, error };
    }

    componentDidCatch(error, errorInfo) {
        console.error("Error caught by ErrorBoundary:", error, errorInfo);

        // Report error to Sentry
        Sentry.captureException(error);
    }

    render() {
        if (this.state.hasError) {
            return (
                <div className="error-container">
                    <h2>Oops, something went wrong!</h2>
                    <p>We're sorry, but there was a problem loading this page.</p>
                    <p>Our team has been notified and we're working to fix it.</p>
                    <button
                        className="refresh-button"
                        onClick={() => window.location.reload()}
                    >
                        Try again
                    </button>
                </div>
            );
        }

        return this.props.children;
    }
}

export default ErrorBoundary;