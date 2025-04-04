import React from 'react';
import './ProgressTracker.css';

const ProgressTracker = ({ current, total }) => {
    const progress = ((current + 1) / total) * 100;

    // Generate progress circles
    const circles = [];
    for (let i = 0; i < total; i++) {
        const className = i < current ? 'complete' :
            i === current ? 'current' : 'incomplete';

        circles.push(
            <div key={i} className={`progress-circle ${className}`}>
                {i + 1}
            </div>
        );
    }

    return (
        <div className="progress-tracker">
            <div className="progress-bar">
                <div
                    className="progress-fill"
                    style={{ width: `${progress}%` }}
                ></div>
            </div>

            <div className="progress-circles">
                {circles}
            </div>

            <div className="progress-text">
                Exercise {current + 1} of {total}
            </div>
        </div>
    );
};

export default ProgressTracker;