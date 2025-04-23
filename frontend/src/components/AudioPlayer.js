import React, { useState, useRef, useEffect } from 'react';
import './AudioPlayer.css';
import api from '../services/api';

// Modificar a função loadAudio
const loadAudio = async (text) => {
    console.log("🔊 loadAudio chamado para:", text);
    try {
        console.log("Solicitando síntese de fala para:", text);
        const response = await api.post('/api/synthesize-speech', {
            text,
            voice_settings: { language_code: 'pt-PT' }
        }, {
            // Adicionar headers específicos
            headers: {
                'Content-Type': 'application/json',
                'Accept': 'application/json'
            },
            // Aumentar timeout
            timeout: 10000
        });

        console.log("Resposta da API:", response.status);

        // Verificar se a resposta é válida
        if (!response.data) {
            throw new Error("Resposta vazia do servidor");
        }

        // Log detalhado da resposta
        console.log("📦 Resposta completa:", {
            status: response.status,
            success: response.data.success,
            hasAudio: !!response.data.audio_data,
            audioLength: response.data.audio_data ? response.data.audio_data.length : 0
        });

        if (response.data.success && response.data.audio_data) {
            // Validar string base64
            if (!/^[A-Za-z0-9+/=]+$/.test(response.data.audio_data)) {
                throw new Error("Dados de áudio inválidos");
            }

            const audioUrl = `data:audio/mp3;base64,${response.data.audio_data}`;
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

const AudioPlayer = ({ audioData, autoPlay = false, onPlayComplete = null }) => {
    const [isPlaying, setIsPlaying] = useState(false);
    const [audioSrc, setAudioSrc] = useState(null);
    const [error, setError] = useState(null);
    const [isLoading, setIsLoading] = useState(false);
    const [retryCount, setRetryCount] = useState(0);
    const [isRetrying, setIsRetrying] = useState(false);
    const audioRef = useRef(null);
    const audioCache = useRef({});

    // Adicione este método para melhorar a manipulação de erros
    const handleAudioError = (e) => {
        console.error("Erro no elemento de áudio:", e);

        // Verificar se temos dados de áudio válidos
        if (!audioData || typeof audioData !== 'string' || audioData.length < 100) {
            console.error("Dados de áudio inválidos ou muito pequenos", audioData);
            return;
        }

        try {
            // Criar uma URL de dados segura
            if (!audioData.startsWith('data:')) {
                console.log("Recriando URL de dados com prefixo");
                // Criar uma nova URL de dados com o prefixo correto
                const audioDataUrl = `data:audio/mp3;base64,${audioData}`;

                // Aplicar diretamente no elemento audio
                if (audioRef.current) {
                    console.log("Aplicando URL de dados diretamente ao elemento audio");
                    audioRef.current.src = audioDataUrl;
                    audioRef.current.load();

                    if (autoPlay) {
                        const playPromise = audioRef.current.play();
                        if (playPromise) {
                            playPromise.catch(playError => {
                                console.warn("Erro ao reproduzir após recriação:", playError);
                            });
                        }
                    }
                }
            }
        } catch (error) {
            console.error("Erro ao tentar recuperar playback:", error);
        }
    };

    // Modificar useEffect que processa audioData
    useEffect(() => {
        let isMounted = true;

        const processAudio = async () => {
            if (!audioData || isRetrying) return;

            try {
                setIsLoading(true);
                setError(null);

                if (typeof audioData === 'string' && audioData.trim().length > 0) {
                    const audioUrl = `data:audio/mp3;base64,${audioData}`;
                    if (isMounted) {
                        setAudioSrc(audioUrl);
                        setIsLoading(false);
                    }
                } else if (retryCount < 3) { // Limitar tentativas
                    console.warn("Tentando recuperar áudio novamente...");
                    setIsRetrying(true);
                    setRetryCount(prev => prev + 1);

                    // Aguardar antes de tentar novamente
                    await new Promise(resolve => setTimeout(resolve, 2000));

                    if (isMounted) {
                        setIsRetrying(false);
                    }
                } else {
                    throw new Error("Dados de áudio inválidos após várias tentativas");
                }
            } catch (err) {
                console.error("Erro ao processar audioData:", err);
                if (isMounted) {
                    setError(`Erro: ${err.message}`);
                    setIsLoading(false);
                }
            }
        };

        processAudio();

        return () => {
            isMounted = false;
        };
    }, [audioData, retryCount]);

    // Função para tocar áudio
    const playAudio = () => {
        if (!audioRef.current || !audioSrc) {
            console.warn("Tentando reproduzir áudio sem source definido");
            return;
        }

        console.log("Iniciando reprodução de áudio");

        const playPromise = audioRef.current.play();
        if (playPromise !== undefined) {
            playPromise
                .then(() => {
                    console.log("Reprodução iniciada com sucesso");
                    setIsPlaying(true);
                })
                .catch(err => {
                    console.error("Erro na reprodução:", err);
                    setError(`Erro de reprodução: ${err.message}`);
                    setIsPlaying(false);
                });
        }
    };

    // Alternar entre play/pause
    const togglePlay = () => {
        if (isPlaying) {
            audioRef.current.pause();
            setIsPlaying(false);
        } else {
            playAudio();
        }
    };

    // Efeitos para manipulação de eventos do áudio
    useEffect(() => {
        const audio = audioRef.current;
        if (!audio) return;

        const handleEnded = () => {
            setIsPlaying(false);
            if (onPlayComplete) onPlayComplete();
        };

        audio.addEventListener('ended', handleEnded);

        return () => {
            audio.removeEventListener('ended', handleEnded);
        };
    }, [onPlayComplete]);

    // Autoplay quando audioSrc muda
    useEffect(() => {
        if (autoPlay && audioSrc && audioRef.current) {
            const timeoutId = setTimeout(() => playAudio(), 100);
            return () => clearTimeout(timeoutId);
        }
    }, [audioSrc, autoPlay]);

    return (
        <div className="audio-player">
            <audio
                ref={audioRef}
                onError={handleAudioError} // Adicione o manipulador de erros
            >
                Your browser does not support the audio element.
            </audio>

            <button
                className="play-button"
                onClick={togglePlay}
                disabled={!audioSrc || isLoading}
            >
                <i className={`fas fa-${isPlaying ? 'pause' : 'play'}`}></i>
            </button>

            {isLoading && <div className="loading">Carregando áudio...</div>}
            {error && <div className="error">{error}</div>}

            {/* Botão de diagnóstico (apenas em desenvolvimento) */}
            {process.env.NODE_ENV !== 'production' && audioSrc && (
                <button
                    onClick={() => {
                        console.log("Diagnóstico:");
                        console.log("- AudioSrc:", audioSrc.substring(0, 50) + "...");
                        console.log("- Elemento:", audioRef.current);
                    }}
                    className="debug-button"
                >
                    Diagnosticar
                </button>
            )}
        </div>
    );
};

export { AudioPlayer, loadAudio };
export default AudioPlayer;