import React, { useState, useEffect, useRef } from 'react';
import { FaMicrophone, FaStop, FaRedo, FaExclamationTriangle } from 'react-icons/fa';
import axios from 'axios';
import './SpeechControls.css';

const SpeechControls = ({ word, onRecognitionComplete, isLoading }) => {
    const [isRecording, setIsRecording] = useState(false);
    const [audioBlob, setAudioBlob] = useState(null);
    const [recognizedText, setRecognizedText] = useState('');
    const [recognitionFailed, setRecognitionFailed] = useState(false);
    const mediaRecorder = useRef(null);
    const audioChunks = useRef([]);

    const startRecording = async () => {
        try {
            setRecognitionFailed(false);
            setRecognizedText('');
            audioChunks.current = [];

            const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
            mediaRecorder.current = new MediaRecorder(stream);

            mediaRecorder.current.ondataavailable = (event) => {
                if (event.data.size > 0) {
                    audioChunks.current.push(event.data);
                }
            };

            mediaRecorder.current.onstop = () => {
                const audioBlob = new Blob(audioChunks.current, { type: 'audio/wav' });
                setAudioBlob(audioBlob);
                processAudio(audioBlob);
            };

            mediaRecorder.current.start();
            setIsRecording(true);
        } catch (error) {
            console.error('Error starting recording:', error);
            alert('Failed to access microphone. Please make sure you have granted permission.');
        }
    };

    const stopRecording = () => {
        if (mediaRecorder.current && isRecording) {
            mediaRecorder.current.stop();
            setIsRecording(false);
            // Stop all audio tracks
            mediaRecorder.current.stream.getTracks().forEach(track => track.stop());
        }
    };

    const processAudio = async (blob) => {
        try {
            const formData = new FormData();
            formData.append('audio', blob, 'recording.wav');

            const token = localStorage.getItem('token');
            const response = await axios.post('/api/recognize', formData, {
                headers: {
                    'Authorization': `Bearer ${token}`,
                    'Content-Type': 'multipart/form-data'
                }
            });

            const text = response.data.recognized_text || '';
            setRecognizedText(text);

            // Check if the text is actually recognized
            if (text === '' || text.toLowerCase().includes('não reconhecido')) {
                setRecognitionFailed(true);
                // Don't call onRecognitionComplete - we'll retry instead
            } else {
                setRecognitionFailed(false);
                onRecognitionComplete(text, blob);
            }
        } catch (error) {
            console.error('Error processing audio:', error);
            setRecognitionFailed(true);
        }
    };

    const retryRecording = () => {
        // Reset state and start again
        setRecognitionFailed(false);
        setRecognizedText('');
        startRecording();
    };

    return (
        <div className="speech-controls">
            {recognitionFailed ? (
                <div className="recognition-error">
                    <div className="error-icon-container">
                        <FaExclamationTriangle className="error-icon" />
                    </div>
                    <p className="error-message">Não consegui entender o que disseste. Por favor, tenta novamente.</p>
                    <button
                        className="retry-button"
                        onClick={retryRecording}
                        disabled={isLoading}
                    >
                        <FaRedo /> Tentar Novamente
                    </button>
                </div>
            ) : (
                <>
                    {isRecording ? (
                        <button
                            className="recording-button"
                            onClick={stopRecording}
                            disabled={isLoading}
                        >
                            <FaStop /> Parar
                        </button>
                    ) : (
                        <button
                            className="start-button"
                            onClick={startRecording}
                            disabled={isLoading}
                        >
                            <FaMicrophone /> Gravar
                        </button>
                    )}
                </>
            )}

            {recognizedText && !recognitionFailed && (
                <div className="recognized-text-container">
                    <p>Texto reconhecido: <span className="recognized-text">{recognizedText}</span></p>
                </div>
            )}
        </div>
    );
};

export default SpeechControls;