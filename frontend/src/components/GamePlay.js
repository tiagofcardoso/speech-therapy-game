import React, { useState, useEffect, useRef } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import api from '../services/api';
import { FaMicrophone, FaStop } from 'react-icons/fa';
import './GamePlay.css';
import AudioPlayer from './AudioPlayer';
import GameMascot from './GameMascot';

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
    const [sessionId, setSessionId] = useState(null); // New state to store the session ID
    const [mascotMood, setMascotMood] = useState('neutral');
    const [mascotMessage, setMascotMessage] = useState(null);
    const [wordAudio, setWordAudio] = useState(null); // State to store the current word audio
    const [isLoadingAudio, setIsLoadingAudio] = useState(false); // State to indicate audio loading
    const mediaRecorderRef = useRef(null);
    const audioChunksRef = useRef([]);
    const audioAnalyzerRef = useRef(null);
    const audioContextRef = useRef(null);
    const analyserIntervalRef = useRef(null);

    useEffect(() => {
        // Tentar restaurar sessionId do localStorage para jogo em andamento
        const savedSessionId = localStorage.getItem(`game_session_${gameId}`);
        if (savedSessionId) {
            console.log(`📋 Restaurando sessão salva para o jogo ${gameId}: ${savedSessionId}`);
            setSessionId(savedSessionId);
        }

        // Fetch game data when component mounts
        const fetchGame = async () => {
            try {
                setLoading(true);
                const response = await api.get(`/api/games/${gameId}`);
                if (response.data.success) {
                    console.log("Game data received:", response.data.game);
                    setGame(response.data.game);

                    // Create a game session after loading the game
                    const sessionId = await createGameSession(response.data.game);

                    // Pré-carregar o áudio da primeira palavra após criar a sessão
                    if (response.data.game.content && response.data.game.content.length > 0) {
                        const firstWord = response.data.game.content[0].word;
                        if (firstWord) {
                            console.log("🎯 Pré-carregando áudio da primeira palavra:", firstWord);
                            fetchAudioForWord(firstWord);
                        }
                    }
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

    // Function to create a game session
    const createGameSession = async (gameData) => {
        try {
            console.log("🎮 Criando sessão de jogo:", gameData.title);
            console.log("🆔 Game ID:", gameId);

            // Verificar se já temos um sessionId
            if (sessionId) {
                console.log("Já existe uma sessão ativa:", sessionId);
                return sessionId;
            }

            // Dados para criar a sessão
            const sessionData = {
                game_id: gameId,
                difficulty: gameData.difficulty || 'iniciante',
                title: gameData.title,
                game_type: gameData.game_type || 'exercícios de pronúncia',
            };

            console.log("📤 Enviando dados para criar sessão:", sessionData);

            // Create a session specifically linked to this game
            const response = await api.post('/api/start_game', sessionData);

            console.log("📥 Resposta da criação de sessão:", response.data);

            // Verificar se a resposta contém um session_id
            if (response.data && response.data.session_id) {
                const newSessionId = response.data.session_id;
                console.log(`✅ Session ID recebido e salvo: ${newSessionId}`);
                setSessionId(newSessionId);

                // Salvar o sessionId no localStorage para persistência
                localStorage.setItem(`game_session_${gameId}`, newSessionId);

                return newSessionId;
            } else {
                console.error("❌ Nenhum session_id encontrado na resposta:", response.data);

                // Verificar se há outro formato possível na resposta
                if (response.data && response.data.id) {
                    console.log("✅ Encontrado ID alternativo na resposta:", response.data.id);
                    setSessionId(response.data.id);
                    localStorage.setItem(`game_session_${gameId}`, response.data.id);
                    return response.data.id;
                }

                throw new Error("Formato de resposta inválido - session_id não encontrado");
            }
        } catch (err) {
            console.error("❌ Erro ao criar sessão de jogo:", err);
            console.error("Detalhes do erro:", err.response?.data || err.message);
            // Tente uma abordagem alternativa se a API falhar
            const fallbackSessionId = `fallback_${gameId}_${Date.now()}`;
            console.warn("⚠️ Usando session ID de fallback:", fallbackSessionId);
            setSessionId(fallbackSessionId);
            return fallbackSessionId;
        }
    };

    useEffect(() => {
        const fetchWordAudio = async () => {
            const currentExercise = getCurrentExercise();
            if (!currentExercise || !currentExercise.word) return;

            try {
                setIsLoadingAudio(true);
                console.log(`🔊 Solicitando áudio para a palavra: "${currentExercise.word}"`);

                const response = await api.post('/api/synthesize-speech', {
                    text: currentExercise.word,
                    voice_settings: {
                        language_code: 'pt-PT' // ou 'pt-BR' dependendo da variante desejada
                    }
                });

                console.log('📨 Resposta da API de síntese:', response.status, response.statusText);

                if (response.data && response.data.audio_data) {
                    console.log('✅ Áudio recebido com sucesso para a palavra:', currentExercise.word);
                    setWordAudio(response.data.audio_data);
                } else {
                    console.warn('⚠️ Resposta da API não contém dados de áudio:', response.data);
                }
            } catch (err) {
                console.error("❌ Erro ao obter áudio da palavra:", err);
                console.error("Detalhes:", err.response?.data || err.message);

                // Tentar novamente após um curto atraso
                setTimeout(() => {
                    console.log("🔄 Tentando novamente buscar o áudio...");
                    fetchWordAudio();
                }, 2000);
            } finally {
                setIsLoadingAudio(false);
            }
        };

        // Chamar imediatamente quando o exercício atual mudar
        fetchWordAudio();
    }, [currentExerciseIndex]);

    // Função auxiliar para buscar áudio para uma palavra específica
    const fetchAudioForWord = async (word) => {
        if (!word) return;

        try {
            setIsLoadingAudio(true);
            console.log(`🎧 Buscando áudio para a palavra "${word}"`);

            const response = await api.post('/api/synthesize-speech', {
                text: word,
                voice_settings: {
                    language_code: 'pt-PT'
                }
            });

            console.log(`👂 Resposta da API para "${word}":`, response.status);

            if (response.data && response.data.success && response.data.audio_data) {
                console.log(`🎵 Áudio recebido para "${word}" - autoplay iniciará em breve`);
                setWordAudio(response.data.audio_data);

                // Definir um mascot message para incentivar a primeira interação
                if (!mascotMessage) {
                    setMascotMood('happy');
                    setMascotMessage(`Vamos praticar! Escuta a palavra "${word}" e depois repete-a.`);
                }
            } else {
                console.warn(`⚠️ Não foi possível obter áudio para "${word}"`, response.data);
            }
        } catch (err) {
            console.error(`❌ Erro ao buscar áudio para "${word}":`, err);
            // Tentar novamente após um curto atraso se falhar
            setTimeout(() => {
                console.log(`🔁 Tentando novamente obter áudio para "${word}"...`);
                fetchAudioForWord(word);
            }, 3000);
        } finally {
            setIsLoadingAudio(false);
        }
    };

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

    const evaluatePronunciation = async (audioBlob, expectedWord) => {
        if (!expectedWord) {
            console.error("Missing expected word for pronunciation evaluation");
            return;
        }

        const formData = new FormData();
        formData.append('audio', audioBlob);
        formData.append('expected_word', expectedWord);

        try {
            const response = await api.post('/api/evaluate-pronunciation', formData);
            return response.data;
        } catch (error) {
            console.error("Pronunciation evaluation error:", error);
            throw error;
        }
    };

    const evaluateResponse = async (audioBlob) => {
        try {
            const currentExercise = getCurrentExercise();
            if (!currentExercise) {
                console.error("No current exercise found");
                setError("Erro: Não foi possível encontrar o exercício atual");
                return;
            }

            console.log("Sending evaluation for word:", currentExercise.word);

            // Montrer la mascotte en train de réfléchir pendant l'évaluation
            setMascotMood('thinking');
            setMascotMessage("Estou a avaliar a tua pronúncia...");

            // Enviar para o backend para avaliação
            const response = await evaluatePronunciation(audioBlob, currentExercise.word);

            console.log("Evaluation response:", response);

            const { isCorrect, score, feedback, audio_feedback, recognized_text } = response;

            setFeedback({
                correct: isCorrect,
                message: feedback || (isCorrect
                    ? "Muito bem! A tua pronúncia está correta."
                    : "Tenta novamente. Presta atenção na pronúncia."),
                recognizedText: recognized_text || "Texto não reconhecido"
            });

            // Armazenar o áudio de feedback para reprodução
            setFeedbackAudio(audio_feedback);

            // Mettre à jour l'humeur de la mascotte en fonction du résultat
            if (isCorrect) {
                setScore(prev => prev + score);
                setMascotMood('happy');
                setMascotMessage("Muito bem! Continua assim!");
            } else {
                setMascotMood('sad');
                setMascotMessage("Quase lá! Tenta de novo, tu consegues!");
            }
        } catch (err) {
            console.error("Erro ao avaliar pronúncia:", err);
            setError("Erro ao avaliar sua resposta: " + (err.response?.data?.message || err.message));

            // Mettre à jour la mascotte en cas d'erreur
            setMascotMood('sad');
            setMascotMessage("Ocorreu um erro. Vamos tentar de novo?");
        }
    };

    const moveToNextExercise = () => {
        // Sempre logar o clique no botão
        console.log("Botão clicado: moveToNextExercise");
        console.log("Estado atual: exercício", currentExerciseIndex + 1, "de", game.content?.length || 0);

        if (currentExerciseIndex < (game.content?.length || 0) - 1) {
            console.log("Avançando para o próximo exercício...");
            setCurrentExerciseIndex(prev => prev + 1);
            setFeedback(null);
            setFeedbackAudio(null);
        } else {
            // Game complete - salvar progresso
            console.log("***** BOTÃO FINALIZAR JOGO CLICADO *****");
            console.log("Completando jogo com:", {
                gameId: gameId,
                sessionId: sessionId,
                currentExerciseIndex: currentExerciseIndex,
                totalExercises: game.content?.length,
                score: score
            });

            saveGameProgress('complete')
                .then((response) => {
                    console.log("Progresso salvo com sucesso:", response);
                    console.log("Exibindo tela de conclusão do jogo");
                    setGameComplete(true);
                })
                .catch(err => {
                    console.error("ERRO AO SALVAR PROGRESSO:", err);
                    console.error("Detalhes do erro:", err.response?.data || err.message);
                    // Ainda mostra a tela de conclusão mesmo se falhar
                    console.warn("Exibindo tela de conclusão mesmo com erro");
                    setGameComplete(true);
                });
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

    // Função para salvar o progresso e a pontuação na base de dados
    const saveGameProgress = async (completionOption) => {
        try {
            if (!sessionId) {
                console.warn('No session ID available, cannot save game progress');
                console.warn('Dados da sessão não disponíveis:', {
                    gameId: gameId,
                    game: game?.title
                });
                return;
            }

            // Calcular a pontuação final como porcentagem
            const finalScore = Math.min(100, (score / ((game.content?.length || 1) * 10)) * 100);

            console.log(`----- INICIANDO SALVAMENTO DE PROGRESSO ------`);
            console.log(`Dados do jogo:\n- ID do jogo: ${gameId}\n- ID da sessão: ${sessionId}\n- Pontuação: ${finalScore}\n- Opção: ${completionOption}`);

            // Criar objeto de dados para maior clareza
            const requestData = {
                session_id: sessionId,
                completed_manually: true,
                completion_option: completionOption,
                final_score: finalScore
            };

            console.log("Enviando dados para o backend:", JSON.stringify(requestData, null, 2));
            console.log("Chamando endpoint: /api/game/finish");

            // Enviar dados para o backend com cabeçalhos de autenticação explícitos
            const authToken = localStorage.getItem('token');
            console.log("Token de autenticação disponível:", !!authToken);

            const response = await api.post('/api/game/finish', requestData, {
                headers: {
                    'Content-Type': 'application/json',
                    'Authorization': `Bearer ${authToken}`
                }
            });

            console.log('RESPOSTA DO SERVIDOR:', response.status);
            console.log('Dados da resposta:', response.data);
            return response.data;
        } catch (err) {
            console.error('⚠️ ERRO AO SALVAR PROGRESSO DO JOGO ⚠️');
            console.error('URL da requisição:', err.config?.url);
            console.error('Método da requisição:', err.config?.method);
            console.error('Status de erro:', err.response?.status);
            console.error('Mensagem de erro:', err.response?.data || err.message);

            if (err.response) {
                console.error('Detalhes da resposta de erro:', err.response.data);
            } else if (err.request) {
                console.error('Sem resposta recebida. Detalhes da requisição:', err.request);
            }

            throw err;
        }
    };

    // Função para iniciar um novo jogo
    const startNewGame = async () => {
        try {
            console.log("Starting new game...");
            // Salvar o progresso do jogo atual
            await saveGameProgress('next_game');
            console.log("Progress saved with 'next_game' option, redirecting to game selection");

            // Redirecionar para a página de geração de jogos
            navigate('/gigi-games');
        } catch (err) {
            console.error('Erro ao iniciar novo jogo:', err);
            // Still redirect even if saving fails
            navigate('/gigi-games');
        }
    };

    // Função para jogar novamente o mesmo jogo
    const playAgain = async () => {
        try {
            console.log("Restarting game...");
            // Salvar o progresso do jogo atual
            await saveGameProgress('play_again');
            console.log("Progress saved with 'play_again' option, resetting game state");

            // Reiniciar o jogo atual
            setCurrentExerciseIndex(0);
            setScore(0);
            setGameComplete(false);
            setFeedback(null);
            setFeedbackAudio(null);
        } catch (err) {
            console.error('Erro ao reiniciar jogo:', err);
            // Still reset the game even if saving fails
            setCurrentExerciseIndex(0);
            setScore(0);
            setGameComplete(false);
            setFeedback(null);
            setFeedbackAudio(null);
        }
    };

    // Função para voltar ao dashboard
    const handleReturnToDashboard = async () => {
        try {
            console.log("Returning to dashboard...");
            // Salvar o progresso do jogo atual
            await saveGameProgress('return_to_dashboard');
            console.log("Progress saved with 'return_to_dashboard' option, navigating to dashboard");

            // Voltar ao dashboard
            returnToDashboard();
        } catch (err) {
            console.error('Erro ao voltar ao dashboard:', err);
            returnToDashboard(); // Voltar mesmo se houver erro
        }
    };

    if (gameComplete) {
        return (
            <div className="game-play-complete">
                <div className="game-complete-header">
                    <span className="game-complete-emoji">🎉</span>
                    <h2>Parabéns!</h2>
                    {/* Ajout d'une animation de confettis */}
                    <div className="confetti-container">
                        {Array.from({ length: 50 }).map((_, index) => (
                            <div
                                key={index}
                                className="confetti"
                                style={{
                                    left: `${Math.random() * 100}%`,
                                    animationDelay: `${Math.random() * 3}s`,
                                    backgroundColor: `hsl(${Math.random() * 360}, 70%, 60%)`
                                }}
                            />
                        ))}
                    </div>
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

                {/* Nouvelle section d'affichage des récompenses */}
                <div className="reward-section">
                    <h3>Récompenses débloquées:</h3>
                    <div className="rewards-container">
                        {score > 70 && <div className="reward-badge">🏆 Champion de prononciation</div>}
                        {score > 50 && <div className="reward-badge">⭐ Étoile montante</div>}
                        {score > 30 && <div className="reward-badge">🎯 Bon effort</div>}
                    </div>
                </div>

                <div className="game-complete-actions">
                    <button onClick={handleReturnToDashboard}>Voltar ao Início</button>
                    <button
                        onClick={playAgain}
                        className="play-again-button"
                    >
                        Jogar Novamente
                    </button>
                    <button
                        onClick={startNewGame}
                        className="next-game-button"
                    >
                        Próximo Jogo
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

                {/* Affichage de la mascotte avec son message */}
                <GameMascot
                    mood={mascotMood}
                    message={mascotMessage}
                    name="default"
                />

                {/* Reprodutor de áudio para a palavra atual - movido para depois do mascote */}
                {wordAudio && (
                    <div className="word-audio-player">
                        <p>Ouça a pronúncia correta:</p>
                        <AudioPlayer
                            audioData={wordAudio}
                            autoPlay={true}
                            onPlayComplete={() => console.log("Reprodução da palavra concluída")}
                        />
                        <button
                            className="repeat-audio-button"
                            onClick={() => {
                                // Recria o componente AudioPlayer forçando-o a tocar novamente
                                setWordAudio(null);
                                setTimeout(() => {
                                    setWordAudio(wordAudio);
                                }, 50);
                            }}
                        >
                            Ouvir novamente
                        </button>
                    </div>
                )}

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
                <button onClick={handleReturnToDashboard} className="exit-button">
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