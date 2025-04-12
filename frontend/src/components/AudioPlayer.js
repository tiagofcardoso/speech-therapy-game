import React, { useState, useRef, useEffect } from 'react';
import { FaPlay, FaPause, FaVolumeUp, FaVolumeMute } from 'react-icons/fa';
import './AudioPlayer.css';

const AudioPlayer = ({ audioData, autoPlay = false, onPlayComplete = null }) => {
    const [isPlaying, setIsPlaying] = useState(false);
    const [isMuted, setIsMuted] = useState(false);
    const [volume, setVolume] = useState(0.8);
    const audioRef = useRef(null);

    useEffect(() => {
        if (audioData && autoPlay) {
            playAudio();
        }
    }, [audioData]);

    useEffect(() => {
        // Create audio element when component mounts
        const audio = new Audio();
        audioRef.current = audio;

        // Set up event listeners
        audio.addEventListener('ended', handleEnded);
        audio.addEventListener('error', handleError);

        // Cleanup on unmount
        return () => {
            audio.pause();
            audio.removeEventListener('ended', handleEnded);
            audio.removeEventListener('error', handleError);
        };
    }, []);

    useEffect(() => {
        if (audioRef.current) {
            audioRef.current.volume = isMuted ? 0 : volume;
        }
    }, [volume, isMuted]);

    const playAudio = () => {
        if (!audioData || !audioRef.current) return;

        try {
            // Update audio source if needed
            if (!isPlaying || audioRef.current.src !== getAudioSource()) {
                audioRef.current.src = getAudioSource();
            }

            // Play the audio
            audioRef.current.play()
                .then(() => setIsPlaying(true))
                .catch(error => {
                    console.error('Error playing audio:', error);
                    setIsPlaying(false);
                });
        } catch (error) {
            console.error('Error playing audio:', error);
        }
    };

    const pauseAudio = () => {
        if (audioRef.current && !audioRef.current.paused) {
            audioRef.current.pause();
            setIsPlaying(false);
        }
    };

    const togglePlay = () => {
        if (isPlaying) {
            pauseAudio();
        } else {
            playAudio();
        }
    };

    const toggleMute = () => {
        setIsMuted(!isMuted);
    };

    const handleVolumeChange = (e) => {
        const newVolume = parseFloat(e.target.value);
        setVolume(newVolume);
    };

    const handleEnded = () => {
        setIsPlaying(false);
        if (onPlayComplete) {
            onPlayComplete();
        }
    };

    const handleError = (e) => {
        console.error('Audio playback error:', e);
        setIsPlaying(false);
    };

    const getAudioSource = () => {
        // Create a data URL from the base64-encoded audio
        return `data:audio/mp3;base64,${audioData}`;
    };

    if (!audioData) {
        return null;
    }

    return (
        <div className="audio-player">
            <button
                className={`play-button ${isPlaying ? 'playing' : ''}`}
                onClick={togglePlay}
                aria-label={isPlaying ? "Pause" : "Play"}
            >
                {isPlaying ? <FaPause /> : <FaPlay />}
            </button>

            <div className="volume-controls">
                <button
                    className="mute-button"
                    onClick={toggleMute}
                    aria-label={isMuted ? "Unmute" : "Mute"}
                >
                    {isMuted ? <FaVolumeMute /> : <FaVolumeUp />}
                </button>

                <input
                    type="range"
                    min="0"
                    max="1"
                    step="0.01"
                    value={volume}
                    onChange={handleVolumeChange}
                    className="volume-slider"
                    aria-label="Volume"
                />
            </div>
        </div>
    );
};

export default AudioPlayer;