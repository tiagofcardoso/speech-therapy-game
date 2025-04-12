import React, { useState, useEffect, useRef } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import api from '../services/api';
import { FaMicrophone, FaStop } from 'react-icons/fa';
import './GamePlay.css';
import AudioPlayer from './AudioPlayer';

const GamePlay = () => {
    const { gameId } = useParams();
    const navigate = useNavigate();
    const [game, setGame] = useState(null);
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState(null);
    const [currentExerciseIndex, setCurrentExerciseIndex] = useState(0);
    const [feedback, setFeedback] = useState(null);
    const [score, setScore] = useState(0);
    const [gameComplete, setGameComplete] = useState(false);
    const [recording, setRecording] = useState(false);
    const [audioBlob, setAudioBlob] = useState(null);
    const [isSpeaking, setIsSpeaking] = useState(false);
    const [audioVolume, setAudioVolume] = useState(0);
    const [audioLevels, setAudioLevels] = useState(Array(10).fill(0));
    const [feedbackAudio, setFeedbackAudio] = useState(null);
    const mediaRecorderRef = useRef(null);
    const audioChunksRef = useRef([]);
    const audioAnalyzerRef = useRef(null);
    const audioContextRef = useRef(null);
    const analyserIntervalRef = useRef(null);

    useEffect(() => {
        // Fetch game data when component mounts
        const fetchGame = async () => {
            try {
                setLoading(true);
                const response = await api.get(`/api/games/${gameId}`);
                if (response.data.success) {
                    console.log("Game data received:", response.data.game);
                    setGame(response.data.game);
                } else {
                    setError("Não foi possível carregar o jogo");
                }
            } catch (err) {
                console.error("Error fetching game:", err);
                setError("Erro ao carregar o jogo: " + (err.response?.data?.message || err.message));
            } finally {
                setLoading(false);
            }
        };

        fetchGame();
    }, [gameId]);

    const startRecording = async () => {
        try {
            // Criar o AudioContext e a MediaStream
            audioContextRef.current = new (window.AudioContext || window.webkitAudioContext)();
            const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
            const mediaRecorder = new MediaRecorder(stream);

            // Configurar o analisador de áudio
            const audioSource = audioContextRef.current.createMediaStreamSource(stream);
            const analyser = audioContextRef.current.createAnalyser();
            analyser.fftSize = 256;
            audioSource.connect(analyser);
            audioAnalyzerRef.current = analyser;

            // Iniciar a análise de volume para detecção de fala
            startVolumeAnalysis();

            // Configuração do MediaRecorder
            mediaRecorderRef.current = mediaRecorder;
            audioChunksRef.current = [];

            mediaRecorder.ondataavailable = (e) => {
                if (e.data.size > 0) {
                    audioChunksRef.current.push(e.data);
                }
            };

            mediaRecorder.onstop = () => {
                // Parar a análise quando a gravação parar
                stopVolumeAnalysis();

                // Criar o Blob e processar
                const audioBlob = new Blob(audioChunksRef.current, {
                    type: 'audio/webm'
                });
                setAudioBlob(audioBlob);
                evaluateResponse(audioBlob);
            };

            mediaRecorder.start();
            setRecording(true);
        } catch (err) {
            console.error("Erro ao acessar microfone:", err);
            setError("Não foi possível acessar o microfone. Verifique as permissões.");
        }
    };

    const stopRecording = () => {
        if (mediaRecorderRef.current && recording) {
            mediaRecorderRef.current.stop();
            setRecording(false);
            stopVolumeAnalysis();
        }
    };

    // Função para iniciar a análise de volume
    const startVolumeAnalysis = () => {
        if (!audioAnalyzerRef.current) return;

        const bufferLength = audioAnalyzerRef.current.frequencyBinCount;
        const dataArray = new Uint8Array(bufferLength);

        // Atualizar a análise de volume a cada 100ms
        analyserIntervalRef.current = setInterval(() => {
            audioAnalyzerRef.current.getByteFrequencyData(dataArray);

            // Calcular o volume médio
            let sum = 0;
            for (let i = 0; i < bufferLength; i++) {
                sum += dataArray[i];
            }
            const avgVolume = sum / bufferLength;

            // Atualizar o estado apenas se houver mudança significativa
            if (Math.abs(avgVolume - audioVolume) > 2) {
                setAudioVolume(avgVolume);
            }

            // Determinar se o usuário está falando (com threshold)
            const speaking = avgVolume > 15; // Ajuste este valor conforme necessário
            setIsSpeaking(speaking);

            // Atualizar os níveis de áudio para visualização
            const newLevels = Array(10).fill(0).map(() => {
                return Math.min(1, Math.random() * (avgVolume / 50));
            });
            setAudioLevels(newLevels);

        }, 100);
    };

    // Função para parar a análise de volume
    const stopVolumeAnalysis = () => {
        if (analyserIntervalRef.current) {
            clearInterval(analyserIntervalRef.current);
            analyserIntervalRef.current = null;
        }
        setIsSpeaking(false);
        setAudioLevels(Array(10).fill(0));
    };

    const evaluateResponse = async (audioBlob) => {
        try {
            const formData = new FormData();
            formData.append("audio", audioBlob);

            const currentExercise = getCurrentExercise();
            if (!currentExercise) {
                console.error("No current exercise found");
                setError("Erro: Não foi possível encontrar o exercício atual");
                return;
            }

            console.log("Sending evaluation for word:", currentExercise.word);
            formData.append("expected_word", currentExercise.word);

            // Enviar para o backend para avaliação
            const response = await api.post('/api/evaluate-pronunciation', formData, {
                headers: {
                    'Content-Type': 'multipart/form-data'
                }
            });

            console.log("Evaluation response:", response.data);

            const { isCorrect, score, feedback, audio_feedback, recognized_text } = response.data;

            setFeedback({
                correct: isCorrect,
                message: feedback || (isCorrect
                    ? "Muito bem! A tua pronúncia está correta."
                    : "Tenta novamente. Presta atenção na pronúncia."),
                recognizedText: recognized_text || "Texto não reconhecido"
            });

            // Armazenar o áudio de feedback para reprodução
            setFeedbackAudio(audio_feedback);

            if (isCorrect) {
                setScore(prev => prev + score);
            }
        } catch (err) {
            console.error("Erro ao avaliar pronúncia:", err);
            setError("Erro ao avaliar sua resposta: " + (err.response?.data?.message || err.message));
        }
    };

    const moveToNextExercise = () => {
        if (currentExerciseIndex < (game.content?.length || 0) - 1) {
            setCurrentExerciseIndex(prev => prev + 1);
            setFeedback(null);
            setFeedbackAudio(null);
        } else {
            // Game complete
            setGameComplete(true);
        }
    };

    const getCurrentExercise = () => {
        if (!game || !game.content || game.content.length === 0) return null;
        return game.content[currentExerciseIndex];
    };

    const returnToDashboard = () => {
        navigate('/dashboard');
    };

    const AudioVisualization = () => {
        return (
            <div className="audio-visualization">
                {audioLevels.map((level, index) => (
                    <div
                        key={index}
                        className={`audio-bar ${isSpeaking ? 'active' : ''}`}
                        style={{
                            height: isSpeaking ? `${10 + level * 30}px` : '10px',
                        }}
                    />
                ))}
            </div>
        );
    };

    const renderRecordingButton = () => {
        return (
            <div className="recording-controls">
                <button
                    onClick={recording ? stopRecording : startRecording}
                    className={`record-button ${recording ? 'recording' : ''} ${isSpeaking && recording ? 'speaking' : ''}`}
                >
                    {recording ? (
                        <>
                            <FaStop /> Parar Gravação
                        </>
                    ) : (
                        <>
                            <FaMicrophone /> Iniciar Gravação
                        </>
                    )}
                </button>

                {recording && <AudioVisualization />}

                <p className="recording-instruction">
                    {recording
                        ? "A falar... Clica em parar quando terminares."
                        : "Clica para iniciar a gravação e pronuncia a palavra."
                    }
                </p>
            </div>
        );
    };

    if (loading) {
        return (
            <div className="game-play-loading">
                <div className="game-play-spinner"></div>
                <p>Carregando jogo...</p>
            </div>
        );
    }

    if (error) {
        return (
            <div className="game-play-error">
                <h3>Houve um problema</h3>
                <p>{error}</p>
                <button onClick={returnToDashboard}>Voltar ao Início</button>
            </div>
        );
    }

    if (gameComplete) {
        return (
            <div className="game-play-complete">
                <div className="game-complete-header">
                    <span className="game-complete-emoji">🎉</span>
                    <h2>Parabéns!</h2>
                </div>

                <p>Você completou o jogo "{game.title}" com sucesso!</p>

                <div className="game-score">
                    <h3>Sua pontuação: {score}</h3>
                    <div className="score-bar">
                        <div
                            className="score-fill"
                            style={{ width: `${Math.min(100, (score / ((game.content?.length || 1) * 10)) * 100)}%` }}
                        ></div>
                    </div>
                </div>

                <div className="game-complete-actions">
                    <button onClick={returnToDashboard}>Voltar ao Início</button>
                    <button
                        onClick={() => {
                            setCurrentExerciseIndex(0);
                            setScore(0);
                            setGameComplete(false);
                            setFeedback(null);
                            setFeedbackAudio(null);
                        }}
                        className="play-again-button"
                    >
                        Jogar Novamente
                    </button>
                </div>
            </div>
        );
    }

    const currentExercise = getCurrentExercise();
    if (!currentExercise) {
        return (
            <div className="game-play-error">
                <h3>Houve um problema</h3>
                <p>Não foi possível carregar os exercícios do jogo.</p>
                <button onClick={returnToDashboard}>Voltar ao Início</button>
            </div>
        );
    }

    return (
        <div className="game-play-container">
            <div className="game-play-header">
                <h2>{game.title}</h2>
                <div className="game-progress">
                    <span>Exercício {currentExerciseIndex + 1} de {game.content?.length || 0}</span>
                    <div className="progress-bar">
                        <div
                            className="progress-fill"
                            style={{ width: `${((currentExerciseIndex + 1) / (game.content?.length || 1)) * 100}%` }}
                        ></div>
                    </div>
                </div>
            </div>

            <div className="exercise-container">
                <h3>{currentExercise.word || "Exercício de pronúncia"}</h3>

                <div className="exercise-details">
                    <p className="exercise-description">{currentExercise.prompt || currentExercise.description || "Pronuncie a palavra corretamente"}</p>

                    {currentExercise.hint && (
                        <div className="hint-box">
                            <span className="hint-label">Dica:</span>
                            <span className="hint-text">{currentExercise.hint}</span>
                        </div>
                    )}

                    <div className="word-display">
                        <h2 className="highlight-word">{currentExercise.word}</h2>
                    </div>

                    <div className="activity-instructions">
                        <h4>Atividade:</h4>
                        <p>{currentExercise.activity || "Diga esta palavra em voz alta, prestando atenção na pronúncia."}</p>
                    </div>
                </div>

                {feedback ? (
                    <div className={`feedback-container ${feedback.correct ? 'correct' : 'incorrect'}`}>
                        <p>{feedback.message}</p>

                        {feedbackAudio && (
                            <AudioPlayer
                                audioData={feedbackAudio}
                                autoPlay={true}
                            />
                        )}

                        {feedback.recognizedText && (
                            <div className="recognition-result">
                                <p><strong>Texto reconhecido:</strong> {feedback.recognizedText || "Nenhum texto reconhecido"}</p>
                            </div>
                        )}

                        <button
                            onClick={moveToNextExercise}
                            className="next-exercise-button"
                        >
                            {currentExerciseIndex < (game.content?.length || 0) - 1 ? 'Próximo Exercício' : 'Finalizar Jogo'}
                        </button>
                    </div>
                ) : (
                    renderRecordingButton()
                )}
            </div>

            <div className="game-play-footer">
                <button onClick={returnToDashboard} className="exit-button">
                    Sair do Jogo
                </button>
                <div className="score-display">
                    <span>Pontuação:</span>
                    <span className="score-value">{score}</span>
                </div>
            </div>
        </div>
    );
};

export default GamePlay;