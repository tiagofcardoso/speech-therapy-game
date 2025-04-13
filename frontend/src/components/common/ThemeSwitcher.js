import React, { useState } from 'react';
import { useTheme } from '../../context/ThemeContext';
import './ThemeSwitcher.css';

const ThemeSwitcher = () => {
    const { themes, changeTheme, currentTheme } = useTheme();
    const [isOpen, setIsOpen] = useState(false);

    const toggleThemePanel = () => {
        setIsOpen(!isOpen);
    };

    return (
        <div className={`theme-switcher ${isOpen ? 'open' : ''}`}>
            <button
                className="theme-toggle"
                onClick={toggleThemePanel}
                aria-label="Mudar tema"
            >
                <span role="img" aria-hidden="true">🎨</span>
            </button>

            <div className="theme-panel">
                <h3>Escolha um Tema</h3>
                <div className="theme-options">
                    {themes.map(theme => (
                        <button
                            key={theme.id}
                            className={`theme-option ${currentTheme === theme.id ? 'active' : ''}`}
                            onClick={() => {
                                changeTheme(theme.id);
                                setIsOpen(false);
                            }}
                            data-theme={theme.id}
                        >
                            <span className="theme-color"></span>
                            <span className="theme-name">{theme.name}</span>
                        </button>
                    ))}
                </div>
            </div>
        </div>
    );
};

export default ThemeSwitcher;