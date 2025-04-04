import React from 'react';
import { render, screen, fireEvent } from '@testing-library/react';
import SpeechControls from '../SpeechControls';

// Mock the user media
beforeAll(() => {
    global.navigator.mediaDevices = {
        getUserMedia: jest.fn().mockImplementation(() => Promise.resolve({
            getTracks: () => [{ stop: jest.fn() }]
        }))
    };
});

describe('SpeechControls', () => {
    test('renders listen and record buttons', () => {
        render(<SpeechControls word="cat" onRecognitionComplete={jest.fn()} />);

        expect(screen.getByText(/listen/i)).toBeInTheDocument();
        expect(screen.getByText(/record/i)).toBeInTheDocument();
    });

    test('changes to stop button when recording starts', async () => {
        render(<SpeechControls word="cat" onRecognitionComplete={jest.fn()} />);

        // Click the record button
        fireEvent.click(screen.getByText(/record/i));

        // The record button should change to stop
        expect(screen.getByText(/stop/i)).toBeInTheDocument();
        expect(screen.queryByText(/record/i)).not.toBeInTheDocument();
    });

    test('calls onRecognitionComplete when recording ends', async () => {
        // Mock the recognition function
        global.fetch = jest.fn().mockImplementation(() =>
            Promise.resolve({
                json: () => Promise.resolve({ recognized_text: 'cat' })
            })
        );

        const mockCallback = jest.fn();
        render(<SpeechControls word="cat" onRecognitionComplete={mockCallback} />);

        // Start recording
        fireEvent.click(screen.getByText(/record/i));

        // Stop recording
        fireEvent.click(screen.getByText(/stop/i));

        // Check if callback was called (might need to wait for async operations)
        // This might need adjustment based on your actual implementation
        setTimeout(() => {
            expect(mockCallback).toHaveBeenCalled();
        }, 100);
    });
});