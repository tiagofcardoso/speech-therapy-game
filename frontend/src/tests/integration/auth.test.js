import React from 'react';
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import { BrowserRouter } from 'react-router-dom';
import Login from '../../pages/Login';

describe('Authentication Flow', () => {
    test('shows error message for invalid credentials', async () => {
        render(
            <BrowserRouter>
                <Login />
            </BrowserRouter>
        );

        // Fill in form with invalid credentials
        fireEvent.change(screen.getByLabelText(/username/i), {
            target: { value: 'wronguser' },
        });

        fireEvent.change(screen.getByLabelText(/password/i), {
            target: { value: 'wrongpass' },
        });

        // Submit the form
        fireEvent.click(screen.getByRole('button', { name: /login/i }));

        // Wait for error message to appear
        await waitFor(() => {
            expect(screen.getByText(/invalid username or password/i)).toBeInTheDocument();
        });
    });

    test('navigates to dashboard upon successful login', async () => {
        // Mock the navigate function
        const mockNavigate = jest.fn();
        jest.mock('react-router-dom', () => ({
            ...jest.requireActual('react-router-dom'),
            useNavigate: () => mockNavigate
        }));

        render(
            <BrowserRouter>
                <Login />
            </BrowserRouter>
        );

        // Fill in form with valid credentials
        fireEvent.change(screen.getByLabelText(/username/i), {
            target: { value: 'testuser' },
        });

        fireEvent.change(screen.getByLabelText(/password/i), {
            target: { value: 'password' },
        });

        // Submit the form
        fireEvent.click(screen.getByRole('button', { name: /login/i }));

        // Verify navigation happened
        await waitFor(() => {
            expect(mockNavigate).toHaveBeenCalledWith('/dashboard');
        });

        // Check token was stored in localStorage
        expect(localStorage.getItem('token')).toBe('fake-jwt-token');
    });
});