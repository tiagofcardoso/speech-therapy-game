import React, { useState, useRef } from 'react';
import axios from 'axios';
import { FaMicrophone, FaStop, FaVolumeUp } from 'react-icons/fa';

const SpeechControls = ({ word, onRecognitionComplete }) => {
    const [isRecording, setIsRecording] = useState(false);
    const [isPlaying, setIsPlaying] = useState(false);
    const [recordedAudio, setRecordedAudio] = useState(null);
    const mediaRecorderRef = useRef(null);
    const audioChunksRef = useRef([]);
    const audioRef = useRef(null);

    // Start recording audio
    const startRecording = async () => {
        audioChunksRef.current = [];

        try {
            const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
            const mediaRecorder = new MediaRecorder(stream);

            mediaRecorder.addEventListener('dataavailable', event => {
                audioChunksRef.current.push(event.data);
            });

            mediaRecorder.addEventListener('stop', () => {
                const audioBlob = new Blob(audioChunksRef.current, { type: 'audio/wav' });
                setRecordedAudio(audioBlob);

                // Send to server for speech recognition
                sendAudioForRecognition(audioBlob);

                // Stop all tracks on the stream to release the microphone
                stream.getTracks().forEach(track => track.stop());
            });

            mediaRecorderRef.current = mediaRecorder;
            mediaRecorder.start();
            setIsRecording(true);
        } catch (err) {
            console.error('Error accessing microphone:', err);
            alert('Could not access microphone. Please check your browser permissions.');
        }
    };

    // Stop recording audio
    const stopRecording = () => {
        if (mediaRecorderRef.current && isRecording) {
            mediaRecorderRef.current.stop();
            setIsRecording(false);
        }
    };

    // Play the demonstration audio for the current word
    const playDemonstration = async () => {
        try {
            setIsPlaying(true);

            const token = localStorage.getItem('token');
            const response = await axios.post(
                '/api/synthesize',
                { text: word },
                {
                    headers: {
                        'Authorization': `Bearer ${token}`,
                        'Content-Type': 'application/json'
                    }
                }
            );

            if (response.data && response.data.audio) {
                // Create an audio element and play the synthesized speech
                const audio = new Audio(`data:audio/mp3;base64,${response.data.audio}`);
                audioRef.current = audio;

                audio.addEventListener('ended', () => {
                    setIsPlaying(false);
                });

                audio.play();
            } else {
                setIsPlaying(false);
                console.error('No audio data received');
            }
        } catch (err) {
            setIsPlaying(false);
            console.error('Error playing demonstration:', err);
        }
    };

    // Send recorded audio to the server for speech recognition
    const sendAudioForRecognition = async (audioBlob) => {
        try {
            const formData = new FormData();
            formData.append('audio', audioBlob);

            const token = localStorage.getItem('token');
            const response = await axios.post('/api/recognize', formData, {
                headers: {
                    'Authorization': `Bearer ${token}`,
                    'Content-Type': 'multipart/form-data'
                }
            });

            if (response.data && response.data.recognized_text) {
                onRecognitionComplete(response.data.recognized_text);
            } else {
                onRecognitionComplete('');
                console.error('No recognized text received');
            }
        } catch (err) {
            onRecognitionComplete('');
            console.error('Error with speech recognition:', err);
        }
    };

    return (
        <div className="speech-controls">
            {/* Listen button - plays the demonstration */}
            <button
                className="btn btn-primary listen-btn"
                onClick={playDemonstration}
                disabled={isPlaying || isRecording}
            >
                <FaVolumeUp /> Listen
            </button>

            {/* Record button - toggles recording state */}
            {!isRecording ? (
                <button
                    className="btn btn-danger record-btn"
                    onClick={startRecording}
                    disabled={isPlaying}
                >
                    <FaMicrophone /> Record
                </button>
            ) : (
                <button
                    className="btn btn-warning stop-btn"
                    onClick={stopRecording}
                >
                    <FaStop /> Stop
                </button>
            )}

            {/* Status messages */}
            {isPlaying && <div className="status-message">Playing demonstration...</div>}
            {isRecording && <div className="status-message recording">Recording... Speak now!</div>}
        </div>
    );
};

export default SpeechControls;