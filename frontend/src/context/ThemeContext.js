import React, { createContext, useState, useContext, useEffect } from 'react';

// Define the available themes
const themes = [
    {
        id: 'default',
        name: 'Padrão',
        colors: {
            primary: '#6200ea',
            primaryLight: '#9d46ff',
            primaryDark: '#0a00b6',
            secondary: '#00e676',
            secondaryLight: '#66ffa6',
            secondaryDark: '#00b248',
            accent: '#ff9100',
            background: '#f0f7ff',
            surface: '#ffffff'
        }
    },
    {
        id: 'ocean',
        name: 'Oceano',
        colors: {
            primary: '#0277bd',
            primaryLight: '#58a5f0',
            primaryDark: '#004c8c',
            secondary: '#26c6da',
            secondaryLight: '#6ff9ff',
            secondaryDark: '#0095a8',
            accent: '#00b8d4',
            background: '#e0f7fa',
            surface: '#ffffff'
        }
    },
    {
        id: 'forest',
        name: 'Floresta',
        colors: {
            primary: '#2e7d32',
            primaryLight: '#60ad5e',
            primaryDark: '#005005',
            secondary: '#66bb6a',
            secondaryLight: '#98ee99',
            secondaryDark: '#338a3e',
            accent: '#7cb342',
            background: '#e8f5e9',
            surface: '#ffffff'
        }
    },
    {
        id: 'candy',
        name: 'Doceria',
        colors: {
            primary: '#d81b60',
            primaryLight: '#ff5c8d',
            primaryDark: '#a00037',
            secondary: '#ec407a',
            secondaryLight: '#ff77a9',
            secondaryDark: '#b4004e',
            accent: '#f50057',
            background: '#fce4ec',
            surface: '#ffffff'
        }
    },
    {
        id: 'space',
        name: 'Espaço',
        colors: {
            primary: '#311b92',
            primaryLight: '#6746c3',
            primaryDark: '#000063',
            secondary: '#7c4dff',
            secondaryLight: '#b47cff',
            secondaryDark: '#3f1dcb',
            accent: '#651fff',
            background: '#ede7f6',
            surface: '#ffffff'
        }
    }
];

// Create context
const ThemeContext = createContext();

// Theme provider component
const ThemeProvider = ({ children }) => {
    // Get theme from localStorage or use default
    const [currentTheme, setCurrentTheme] = useState(() => {
        const savedTheme = localStorage.getItem('theme');
        return savedTheme || 'default';
    });

    // Update CSS variables when theme changes
    useEffect(() => {
        const theme = themes.find(t => t.id === currentTheme);

        if (theme) {
            const root = document.documentElement;

            root.style.setProperty('--primary-color', theme.colors.primary);
            root.style.setProperty('--primary-light', theme.colors.primaryLight);
            root.style.setProperty('--primary-dark', theme.colors.primaryDark);
            root.style.setProperty('--secondary-color', theme.colors.secondary);
            root.style.setProperty('--secondary-light', theme.colors.secondaryLight);
            root.style.setProperty('--secondary-dark', theme.colors.secondaryDark);
            root.style.setProperty('--accent-color', theme.colors.accent);
            root.style.setProperty('--background-color', theme.colors.background);
            root.style.setProperty('--surface-color', theme.colors.surface);

            // Also update RGB values for transparency usage
            const hexToRgb = (hex) => {
                const result = /^#?([a-f\d]{2})([a-f\d]{2})([a-f\d]{2})$/i.exec(hex);
                return result ?
                    `${parseInt(result[1], 16)}, ${parseInt(result[2], 16)}, ${parseInt(result[3], 16)}` : null;
            };

            root.style.setProperty('--primary-color-rgb', hexToRgb(theme.colors.primary));
            root.style.setProperty('--secondary-color-rgb', hexToRgb(theme.colors.secondary));
            root.style.setProperty('--accent-color-rgb', hexToRgb(theme.colors.accent));
        }

        // Save theme preference
        localStorage.setItem('theme', currentTheme);
    }, [currentTheme]);

    // Change theme
    const changeTheme = (themeId) => {
        setCurrentTheme(themeId);
    };

    return (
        <ThemeContext.Provider value={{
            currentTheme,
            changeTheme,
            themes
        }}>
            {children}
        </ThemeContext.Provider>
    );
};

// Custom hook to use the theme
export const useTheme = () => {
    const context = useContext(ThemeContext);
    if (!context) {
        throw new Error('useTheme must be used within a ThemeProvider');
    }
    return context;
};

export default ThemeProvider;