import React, { useState, useEffect } from 'react';
import './AccessibilityControls.css';

const AccessibilityControls = () => {
    const [isOpen, setIsOpen] = useState(false);
    const [fontSize, setFontSize] = useState(localStorage.getItem('fontSize') || 'medium');
    const [contrast, setContrast] = useState(localStorage.getItem('contrast') || 'standard');
    const [animations, setAnimations] = useState(localStorage.getItem('animations') !== 'disabled');
    const [sounds, setSounds] = useState(localStorage.getItem('sounds') !== 'disabled');

    useEffect(() => {
        // Aplicar configurações ao carregar o componente
        applyAccessibilitySettings();
    }, [fontSize, contrast, animations, sounds]);

    const applyAccessibilitySettings = () => {
        // Ajustar tamanho da fonte
        document.documentElement.classList.remove('font-small', 'font-medium', 'font-large', 'font-extra-large');
        document.documentElement.classList.add(`font-${fontSize}`);
        localStorage.setItem('fontSize', fontSize);

        // Ajustar contraste
        document.documentElement.classList.remove('contrast-standard', 'contrast-high');
        document.documentElement.classList.add(`contrast-${contrast}`);
        localStorage.setItem('contrast', contrast);

        // Configurar animações
        if (animations) {
            document.documentElement.classList.remove('animations-disabled');
            localStorage.removeItem('animations');
        } else {
            document.documentElement.classList.add('animations-disabled');
            localStorage.setItem('animations', 'disabled');
        }

        // Configurar sons
        if (sounds) {
            localStorage.removeItem('sounds');
        } else {
            localStorage.setItem('sounds', 'disabled');
        }
    };

    const togglePanel = () => {
        setIsOpen(!isOpen);
    };

    return (
        <div className={`accessibility-panel ${isOpen ? 'open' : ''}`}>
            <button
                className="accessibility-toggle"
                onClick={togglePanel}
                aria-label="Configurações de acessibilidade"
            >
                <span role="img" aria-hidden="true">⚙️</span>
            </button>

            <div className="accessibility-content">
                <h3>Acessibilidade</h3>

                <div className="accessibility-option">
                    <label htmlFor="font-size">Tamanho do texto</label>
                    <select
                        id="font-size"
                        value={fontSize}
                        onChange={(e) => setFontSize(e.target.value)}
                    >
                        <option value="small">Pequeno</option>
                        <option value="medium">Médio</option>
                        <option value="large">Grande</option>
                        <option value="extra-large">Extra grande</option>
                    </select>
                </div>

                <div className="accessibility-option">
                    <label htmlFor="contrast">Contraste</label>
                    <select
                        id="contrast"
                        value={contrast}
                        onChange={(e) => setContrast(e.target.value)}
                    >
                        <option value="standard">Normal</option>
                        <option value="high">Alto contraste</option>
                    </select>
                </div>

                <div className="accessibility-option">
                    <label>
                        <input
                            type="checkbox"
                            checked={animations}
                            onChange={() => setAnimations(!animations)}
                        />
                        Animações
                    </label>
                </div>

                <div className="accessibility-option">
                    <label>
                        <input
                            type="checkbox"
                            checked={sounds}
                            onChange={() => setSounds(!sounds)}
                        />
                        Sons
                    </label>
                </div>

                <button
                    className="close-panel"
                    onClick={() => setIsOpen(false)}
                >
                    Fechar
                </button>
            </div>
        </div>
    );
};

export default AccessibilityControls;