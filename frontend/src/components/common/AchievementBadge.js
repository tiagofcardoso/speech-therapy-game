import React from 'react';
import './AchievementBadge.css';

const AchievementBadge = ({ icon, label, variant = 'default' }) => {
    return (
        <div className={`achievement-badge ${variant}`}>
            <span className="achievement-icon">{icon}</span>
            <span className="achievement-label">{label}</span>
        </div>
    );
};

export default AchievementBadge;