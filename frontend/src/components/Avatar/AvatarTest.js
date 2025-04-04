import React, { useState } from 'react';
import AvatarRenderer from './AvatarRenderer';

const AvatarTest = () => {
    const [playing, setPlaying] = useState(false);

    // Sample lipsync data for testing
    const sampleLipsyncData = [
        { start: 0.0, end: 0.5, value: 'X' },  // Neutral
        { start: 0.5, end: 1.0, value: 'A' },  // 'A' sound
        { start: 1.0, end: 1.5, value: 'B' },  // 'B' sound
        { start: 1.5, end: 2.0, value: 'C' },  // 'C' sound
        { start: 2.0, end: 2.5, value: 'D' },  // 'D' sound
        { start: 2.5, end: 3.0, value: 'X' }   // Back to neutral
    ];

    // Use a built-in browser sound for testing
    const testAudioSrc = 'data:audio/wav;base64,UklGRl9vT19XQVZFZm10IBAAAAABAAEAQB8AAEAfAAABAAgAZGF0YU...';

    return (
        <div className="avatar-test">
            <h2>Avatar Test</h2>

            <AvatarRenderer
                audioSrc={testAudioSrc}
                lipsyncData={sampleLipsyncData}
                modelUrl="/models/default_avatar.glb"
                onPlayComplete={() => setPlaying(false)}
            />

            <button
                onClick={() => setPlaying(true)}
                disabled={playing}
            >
                Test Animation
            </button>

            <div className="debug-info">
                <h3>Debug Information:</h3>
                <p>Check the browser console for detailed logs about model loading and viseme changes.</p>
            </div>
        </div>
    );
};

export default AvatarTest;