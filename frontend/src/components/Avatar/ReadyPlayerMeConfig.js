import React, { useState } from 'react';

const ReadyPlayerMeConfig = ({ onAvatarCreated }) => {
    const [isFrameOpen, setIsFrameOpen] = useState(false);

    const handleAvatarCreated = (url) => {
        if (onAvatarCreated) {
            onAvatarCreated(url);
        }
        setIsFrameOpen(false);
    };

    const openFrame = () => {
        setIsFrameOpen(true);

        const iframe = document.getElementById('readyplayerme-iframe');

        window.addEventListener('message', (event) => {
            if (event.data.type === 'avatar_export') {
                handleAvatarCreated(event.data.data.url);
            }
        });
    };

    return (
        <div className="avatar-creator">
            <button onClick={openFrame}>Criar Avatar Personalizado</button>

            {isFrameOpen && (
                <div className="iframe-container">
                    <iframe
                        id="readyplayerme-iframe"
                        src="https://demo.readyplayer.me/avatar?clearCache=true"
                        allow="camera"
                        className="avatar-iframe"
                        title="Ready Player Me Avatar Creator"
                    ></iframe>
                </div>
            )}
        </div>
    );
};

export default ReadyPlayerMeConfig;