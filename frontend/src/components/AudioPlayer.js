import React, { useState, useRef, useEffect } from 'react';
import './AudioPlayer.css';
import api from '../services/api';
import audioManager from '../utils/AudioManager';

// Modificar a função loadAudio
const loadAudio = async (text, usePolly = true) => {
    console.log(`🔊 loadAudio chamado para: "${text}" (usePolly: ${usePolly})`);
    try {
        // Choose the appropriate endpoint based on whether we want to use AWS Polly
        const endpoint = usePolly ? '/api/synthesize' : '/api/synthesize-speech';
        const payload = usePolly
            ? { text, voice_id: 'Ines', language_code: 'pt-PT' }
            : { text, voice_settings: { language_code: 'pt-PT' } };

        console.log(`Solicitando síntese de fala para: "${text}" via ${endpoint}`);

        const response = await api.post(endpoint, payload, {
            headers: {
                'Content-Type': 'application/json',
                'Accept': 'application/json'
            },
            timeout: 10000
        });

        console.log("Resposta da API:", response.status);

        if (!response.data) {
            throw new Error("Resposta vazia do servidor");
        }

        // Log detalhado da resposta
        console.log("📦 Resposta completa:", {
            status: response.status,
            success: response.data.success,
            hasAudio: !!response.data.audio_data || !!response.data.audio,
            audioLength: (response.data.audio_data || response.data.audio || "").length
        });

        // Handle different response formats
        let audioData = response.data.audio_data || response.data.audio;

        if (audioData) {
            // Validar string base64
            if (!/^[A-Za-z0-9+/=]+$/.test(audioData)) {
                console.warn("⚠️ Dados de áudio em formato não padrão, tentando limpar");
                // Try to clean up the data by removing non-base64 characters
                audioData = audioData.replace(/[^A-Za-z0-9+/=]/g, '');
                if (!/^[A-Za-z0-9+/=]+$/.test(audioData)) {
                    throw new Error("Dados de áudio inválidos mesmo após limpeza");
                }
            }

            const audioUrl = `data:audio/mp3;base64,${audioData}`;
            return audioUrl;
        } else {
            throw new Error(response.data.error || "Falha na síntese de fala");
        }
    } catch (err) {
        console.error("Erro na síntese:", err);
        console.error("Detalhes do erro:", {
            message: err.message,
            response: err.response,
            request: err.request
        });
        return null;
    }
};

const AudioPlayer = ({
    audioData,
    autoPlay = false,
    onPlayComplete = null,
    playerId = null,
    allowOverlap = false, // New prop to control whether this audio can overlap others
    loadingDelay = 0 // Delay before starting playback (useful for sequencing)
}) => {
    const [isPlaying, setIsPlaying] = useState(false);
    const [error, setError] = useState(null);
    const audioRef = useRef(null);
    const idRef = useRef(playerId || `audio-player-${Math.random().toString(36).substring(2, 9)}`);
    const [isReady, setIsReady] = useState(false);

    // Register with AudioManager when component mounts
    useEffect(() => {
        // Create audio element if it doesn't exist
        if (!audioRef.current) {
            audioRef.current = new Audio();
        }

        // Use the stable ID from ref
        const stableId = idRef.current;

        // Register with audio manager
        const unregister = audioManager.register(
            stableId,
            audioRef.current,
            (playing) => setIsPlaying(playing),
            onPlayComplete
        );

        // Enhance cleanup to include complete state reset
        return () => {
            unregister();
            if (audioRef.current) {
                audioRef.current.pause();
                audioRef.current.src = '';
            }
        };
    }, [onPlayComplete]);

    // Setup the audio element when audioData changes
    useEffect(() => {
        // Don't reset isReady if we're just re-mounting with same audio
        if (!audioData) {
            console.log(`AudioPlayer ${idRef.current}: Sem dados de áudio`);
            return;
        }

        // Only reset ready state and reconfigure if audio data actually changed
        if (audioRef.current.dataset.lastAudioHash !== String(audioData.length)) {
            setIsReady(false);

            try {
                console.log(`AudioPlayer ${idRef.current}: Configurando áudio (${typeof audioData} com tamanho ${typeof audioData === 'string' ? audioData.length : 'N/A'})`);

                // Configure audio source
                let audioSrc;
                if (typeof audioData === 'string') {
                    if (audioData.startsWith('http') || audioData.startsWith('blob:') || audioData.startsWith('data:')) {
                        audioSrc = audioData;
                    } else {
                        audioSrc = `data:audio/mp3;base64,${audioData}`;
                    }

                    console.log(`AudioPlayer ${idRef.current}: URL do áudio configurada: ${audioSrc.substring(0, 40)}...`);

                    // Set the source and load the audio
                    audioRef.current.src = audioSrc;
                    audioRef.current.load();

                    // Store a hash of the audio data to detect changes
                    audioRef.current.dataset.lastAudioHash = String(audioData.length);

                    // Mark as ready after a short delay
                    const readyTimer = setTimeout(() => {
                        setIsReady(true);

                        // Try to autoplay if requested, after loadingDelay
                        if (autoPlay) {
                            const playTimer = setTimeout(() => {
                                try {
                                    console.log(`AudioPlayer ${idRef.current}: Tentando autoplay`);
                                    audioManager.play(idRef.current, allowOverlap)
                                        .catch(err => {
                                            if (err.name !== 'AbortError') {
                                                console.warn(`AudioPlayer ${idRef.current}: Erro em autoplay:`, err);
                                                setError(`Falha ao reproduzir: ${err.message}`);
                                            }
                                        });
                                } catch (err) {
                                    console.error(`AudioPlayer ${idRef.current}: Erro ao executar autoplay:`, err);
                                }
                            }, loadingDelay);

                            return () => clearTimeout(playTimer);
                        }
                    }, 100);

                    return () => clearTimeout(readyTimer);
                } else {
                    console.error(`AudioPlayer ${idRef.current}: Tipo de dados de áudio não suportado:`, typeof audioData);
                    setError("Formato de áudio inválido");
                }
            } catch (err) {
                console.error(`AudioPlayer ${idRef.current}: Erro ao configurar áudio:`, err);
                setError(`Erro ao configurar áudio: ${err.message}`);
            }
        } else {
            console.log(`AudioPlayer ${idRef.current}: Usando áudio já carregado (hash: ${audioRef.current.dataset.lastAudioHash})`);
            setIsReady(true);
        }
    }, [audioData, autoPlay, allowOverlap, loadingDelay]);

    // Function to toggle play/pause
    const togglePlay = () => {
        if (!isReady) {
            console.log(`AudioPlayer ${idRef.current}: Tentativa de reprodução antes de estar pronto`);
            return;
        }

        console.log(`AudioPlayer ${idRef.current}: Botão de play/pause clicado. Estado atual:`, isPlaying);

        if (!audioRef.current) {
            console.error(`AudioPlayer ${idRef.current}: Elemento de áudio não inicializado`);
            setError("Não foi possível inicializar o áudio");
            return;
        }

        if (isPlaying) {
            console.log(`AudioPlayer ${idRef.current}: Pausando áudio`);
            audioManager.stop(idRef.current);
        } else {
            console.log(`AudioPlayer ${idRef.current}: Iniciando reprodução`);

            audioManager.play(idRef.current, allowOverlap)
                .catch(err => {
                    console.error(`AudioPlayer ${idRef.current}: Erro ao iniciar reprodução:`, err);
                    setError(`Falha ao reproduzir: ${err.message}`);
                    tryAlternativePlayback();
                });
        }
    };

    // Function for alternative playback method
    const tryAlternativePlayback = () => {
        try {
            console.log(`AudioPlayer ${idRef.current}: 🛠️ Tentando método alternativo de reprodução`);

            if (!audioRef.current || !audioRef.current.src) {
                throw new Error("Elemento de áudio não inicializado ou sem fonte");
            }

            // Create a new Audio element with the same source
            const newAudio = new Audio(audioRef.current.src);
            audioRef.current = newAudio;

            // Re-register with audio manager
            audioManager.register(
                idRef.current,
                newAudio,
                (playing) => setIsPlaying(playing),
                onPlayComplete
            );

            // Try to play
            audioManager.play(idRef.current, allowOverlap)
                .catch(err => {
                    console.error(`AudioPlayer ${idRef.current}: Erro no método alternativo:`, err);
                    setError(`Todos os métodos de reprodução falharam`);
                });

        } catch (e) {
            console.error(`AudioPlayer ${idRef.current}: Falha no método alternativo:`, e);
            setError(`Todos os métodos de reprodução falharam: ${e.message}`);
        }
    };

    return (
        <div className={`audio-player ${playerId ? `audio-player-${playerId}` : ''}`} data-player-id={idRef.current}>
            <button
                className={`play-button ${isPlaying ? 'playing' : ''} ${error ? 'error' : ''}`}
                onClick={togglePlay}
                disabled={!audioData || !isReady}
                aria-label={isPlaying ? "Pausar áudio" : "Reproduzir áudio"}
            >
                <i className={`fas fa-${isPlaying ? 'pause' : 'play'}`}></i>
            </button>

            {error && (
                <div className="audio-error">
                    <span title={error}>Erro</span>
                    <button
                        className="retry-button"
                        onClick={tryAlternativePlayback}
                        aria-label="Tentar novamente"
                    >
                        <i className="fas fa-redo"></i>
                    </button>
                </div>
            )}

            {/* Debug button in development only */}
            {process.env.NODE_ENV === 'development' && (
                <button
                    className="debug-button"
                    onClick={() => {
                        console.log(`=== DEBUG AUDIO PLAYER ${idRef.current} ===`);
                        console.log("audioRef:", audioRef.current);
                        console.log("audioData:", typeof audioData === 'string' ?
                            `${audioData.substring(0, 50)}... (${audioData.length} chars)` :
                            audioData);
                        console.log("isPlaying:", isPlaying);
                        console.log("error:", error);
                        console.log("audioManager state:", audioManager.getDebugInfo());

                        if (audioRef.current) {
                            console.log("Audio element properties:");
                            console.log("- src:", audioRef.current.src);
                            console.log("- paused:", audioRef.current.paused);
                            console.log("- currentTime:", audioRef.current.currentTime);
                            console.log("- duration:", audioRef.current.duration);
                            console.log("- error:", audioRef.current.error);
                        }
                    }}
                >
                    Debug
                </button>
            )}
        </div>
    );
};

export { AudioPlayer, loadAudio };
export default AudioPlayer;