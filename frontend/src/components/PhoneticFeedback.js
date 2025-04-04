import React from 'react';
import './PhoneticFeedback.css';

const PhoneticFeedback = ({ analysis, word }) => {
    if (!analysis) return null;

    const renderPhoneticComparison = () => {
        // Se não houver análise fonética, não mostrar nada
        if (!analysis.phonetics) return null;

        const { original, spoken } = analysis.phonetics;

        // Destacar diferenças entre pronúncia original e falada
        const maxLength = Math.max(original.length, spoken.length);
        const charComparison = [];

        for (let i = 0; i < maxLength; i++) {
            const originalChar = original[i] || '';
            const spokenChar = spoken[i] || '';
            const isMatch = originalChar.toLowerCase() === spokenChar.toLowerCase();

            charComparison.push(
                <div key={i} className="phonetic-char-comparison">
                    <span className={`original-char ${isMatch ? 'match' : 'mismatch'}`}>
                        {originalChar || ' '}
                    </span>
                    <span className="comparison-arrow">↓</span>
                    <span className={`spoken-char ${isMatch ? 'match' : 'mismatch'}`}>
                        {spokenChar || ' '}
                    </span>
                </div>
            );
        }

        return (
            <div className="phonetic-comparison">
                <div className="phonetic-row original">
                    <div className="phonetic-label">Esperado:</div>
                    <div className="phonetic-text">{original}</div>
                </div>
                <div className="phonetic-row spoken">
                    <div className="phonetic-label">Ouvido:</div>
                    <div className="phonetic-text">{spoken}</div>
                </div>
                <div className="char-by-char">
                    {charComparison}
                </div>
            </div>
        );
    };

    // Sugestões para melhorar a pronúncia
    const renderPronunciationTips = () => {
        // Não mostrar dicas se o usuário acertou
        if (analysis.match) return null;

        const tips = [];

        // Dicas baseadas em erros comuns
        if (analysis.possibleErrors && analysis.possibleErrors.length > 0) {
            analysis.possibleErrors.forEach((error, index) => {
                tips.push(
                    <li key={`error-${index}`}>
                        Tente prestar atenção especial ao som <strong>"{error.type.replace(/[\/\^$]/g, '')}"</strong> no início da palavra.
                    </li>
                );
            });
        }

        // Dicas genéricas
        if (word.includes('r') && !analysis.match) {
            tips.push(<li key="tip-r">Tente pronunciar o "R" rolando a língua no céu da boca.</li>);
        }

        if (word.includes('lh') && !analysis.match) {
            tips.push(<li key="tip-lh">Para o som "LH", coloque a língua no céu da boca e deixe o ar passar pelos lados.</li>);
        }

        return tips.length > 0 ? (
            <div className="pronunciation-tips">
                <h4>Dicas para melhorar:</h4>
                <ul>{tips}</ul>
            </div>
        ) : null;
    };

    return (
        <div className="phonetic-feedback">
            <div className="similarity-score">
                <div className="score-label">Similaridade:</div>
                <div className="score-meter">
                    <div
                        className="score-fill"
                        style={{ width: `${analysis.similarity}%` }}
                    >
                        {analysis.similarity}%
                    </div>
                </div>
            </div>

            {renderPhoneticComparison()}
            {renderPronunciationTips()}
        </div>
    );
};

export default PhoneticFeedback;