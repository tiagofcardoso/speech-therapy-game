import React from 'react';
import ReactDOM from 'react-dom';
import * as Sentry from '@sentry/react';
import { BrowserTracing } from '@sentry/tracing';
import App from './App';
import './index.css';

// Initialize Sentry
if (process.env.NODE_ENV === 'production' && process.env.REACT_APP_SENTRY_DSN) {
  Sentry.init({
    dsn: process.env.REACT_APP_SENTRY_DSN,
    integrations: [new BrowserTracing()],
    tracesSampleRate: 0.5,
    environment: process.env.REACT_APP_ENVIRONMENT || 'production',

    // Capture React component stack
    beforeSend(event) {
      // Check if it has a component stack trace
      if (event.exception && event.exception.values && event.exception.values[0]) {
        event.exception.values[0].stacktrace.frames.forEach(frame => {
          // Clean up the component stack trace
          frame.filename = frame.filename.replace(/[a-z]:\\.*\\node_modules\\/, 'node_modules/');
        });
      }
      return event;
    }
  });
}

ReactDOM.render(
  <React.StrictMode>
    <App />
  </React.StrictMode>,
  document.getElementById('root')
);