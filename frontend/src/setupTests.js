import '@testing-library/jest-dom';
import { server } from './mocks/server';

// Start the MSW server before tests
beforeAll(() => server.listen());

// Reset handlers after each test
afterEach(() => server.resetHandlers());

// Clean up after all tests
afterAll(() => server.close());

const config = {
    "name": "speech-therapy-game",
    "version": "1.0.0",
    "private": true,
    "dependencies": {
        "react": "^17.0.2",
        "react-dom": "^17.0.2",
        "react-router-dom": "^6.2.1",
        "axios": "^0.24.0",
        "react-icons": "^4.3.1",
        "react-scripts": "5.0.0"
    },
    "scripts": {
        "start": "react-scripts start",
        "build": "react-scripts build",
        "test": "jest",
        "eject": "react-scripts eject"
    }
};

export default config;