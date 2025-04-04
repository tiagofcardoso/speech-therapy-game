import React from 'react';
import { render, screen } from '@testing-library/react';
import ProgressTracker from '../ProgressTracker';

describe('ProgressTracker', () => {
    test('renders the correct number of progress circles', () => {
        render(<ProgressTracker current={2} total={5} />);

        // Find all elements with progress-circle class (could use a data-testid in production)
        const circles = document.querySelectorAll('.progress-circle');
        expect(circles.length).toBe(5);
    });

    test('shows the correct progress text', () => {
        render(<ProgressTracker current={2} total={5} />);

        // Check for the progress text
        const progressText = screen.getByText('Exercise 3 of 5');
        expect(progressText).toBeInTheDocument();
    });

    test('marks the correct circles as complete, current, and incomplete', () => {
        render(<ProgressTracker current={2} total={5} />);

        const circles = document.querySelectorAll('.progress-circle');

        // First two circles should be complete
        expect(circles[0]).toHaveClass('complete');
        expect(circles[1]).toHaveClass('complete');

        // Third circle should be current
        expect(circles[2]).toHaveClass('current');

        // Last two circles should be incomplete
        expect(circles[3]).toHaveClass('incomplete');
        expect(circles[4]).toHaveClass('incomplete');
    });
});