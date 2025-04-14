import React, { useState, useEffect, useRef } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import api from '../services/api';
import phoneticAnalyzer from '../utils/phoneticAnalyzer';
import PhoneticFeedback from '../components/PhoneticFeedback';
import AvatarRenderer from '../components/Avatar/AvatarRenderer';
import { getMockLipsyncForWord } from '../services/mockApi';
import AudioPlayer from '../components/AudioPlayer'; // Importar o AudioPlayer
import './Exercise.css';

const Exercise = () => {
    const { exerciseId } = useParams();
    const navigate = useNavigate();
    const [exercise, setExercise] = useState(null);
    const [currentWordIndex, setCurrentWordIndex] = useState(0);
    const [words, setWords] = useState([]);
    const [isListening, setIsListening] = useState(false);
    const [transcript, setTranscript] = useState('');
    const [feedback, setFeedback] = useState('');
    const [score, setScore] = useState(0);
    const [completed, setCompleted] = useState(false);
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState(null);
    const [usingFallbackData, setUsingFallbackData] = useState(false);
    const [phoneticAnalysis, setPhoneticAnalysis] = useState(null);
    const [avatarData, setAvatarData] = useState(null);
    const [playingAvatar, setPlayingAvatar] = useState(false);
    const [wordAudio, setWordAudio] = useState(null); // Estado para o áudio da palavra atual
    const [isLoadingAudio, setIsLoadingAudio] = useState(false); // Indicador de carregamento do áudio

    const recognitionRef = useRef(null);
    const wordsRef = useRef([]);
    const currentWordIndexRef = useRef(0);

    useEffect(() => {
        wordsRef.current = words;
    }, [words]);

    useEffect(() => {
        currentWordIndexRef.current = currentWordIndex;
    }, [currentWordIndex]);

    useEffect(() => {
        const loadExercise = async () => {
            try {
                setLoading(true);

                const fallbackExercises = {
                    "1": {
                        id: 1,
                        title: "Pronunciação de R",
                        difficulty: "beginner",
                        description: "Pratique a pronúncia do som 'R' no início das palavras.",
                        instructions: "Clique em 'Iniciar' e pronuncie a palavra mostrada claramente.",
                        words: [
                            { id: 1, text: "rato", hint: "Um animal pequeno que rói" },
                            { id: 2, text: "rosa", hint: "Uma flor bonita" },
                            { id: 3, text: "rio", hint: "Água que corre" },
                            { id: 4, text: "roda", hint: "Parte de um carro" },
                            { id: 5, text: "rua", hint: "Onde ficam as casas" }
                        ]
                    },
                    "2": {
                        id: 2,
                        title: "Sons de S e Z",
                        difficulty: "intermediate",
                        description: "Diferencie sons sibilantes em palavras comuns.",
                        instructions: "Pronuncie cuidadosamente cada palavra, focando nos sons de S e Z.",
                        words: [
                            { id: 1, text: "casa", hint: "Onde moramos" },
                            { id: 2, text: "zero", hint: "Número antes do um" },
                            { id: 3, text: "sapo", hint: "Animal que pula" },
                            { id: 4, text: "asa", hint: "Parte de um pássaro" },
                            { id: 5, text: "zona", hint: "Área ou região" }
                        ]
                    }
                };

                console.log("Usando dados de fallback para o exercício");
                const fallbackExercise = fallbackExercises[exerciseId] || fallbackExercises["1"];
                setExercise(fallbackExercise);
                setWords(fallbackExercise.words);
                wordsRef.current = fallbackExercise.words;
                setUsingFallbackData(true);
                console.log("Palavras carregadas (fallback):", fallbackExercise.words);
                setLoading(false);

                try {
                    const response = await api.get(`/api/exercises/${exerciseId}`);
                    if (response.data.success) {
                        console.log("Dados da API recebidos (em segundo plano)");
                    }
                } catch (apiError) {
                    console.warn("API indisponível:", apiError.message);
                }
            } catch (err) {
                console.error('Error loading exercise:', err);
                setError('Não foi possível carregar o exercício. Por favor, tente novamente.');
                setLoading(false);
            }
        };

        loadExercise();

        if ('webkitSpeechRecognition' in window) {
            const recognition = new window.webkitSpeechRecognition();
            recognition.continuous = false;
            recognition.lang = 'pt-BR';

            recognition.onresult = (event) => {
                const speechResult = event.results[0][0].transcript.toLowerCase();
                setTranscript(speechResult);

                const currentWords = wordsRef.current;
                const wordIndex = currentWordIndexRef.current;

                console.log("Valores das refs no callback de reconhecimento:", {
                    wordsFromRef: currentWords.length,
                    indexFromRef: wordIndex,
                    speechResult
                });

                if (currentWords && currentWords.length > 0 && wordIndex < currentWords.length) {
                    checkPronunciationWithRefs(speechResult, currentWords, wordIndex);
                } else {
                    setFeedback('Erro: Não foi possível verificar a pronúncia. Palavras não carregadas corretamente.');
                }
            };

            recognition.onerror = (event) => {
                console.error('Speech recognition error:', event.error);
                setFeedback('Erro no reconhecimento de fala. Por favor, tente novamente.');
                setIsListening(false);
            };

            recognition.onend = () => {
                setIsListening(false);
            };

            recognitionRef.current = recognition;
        } else {
            setError('Seu navegador não suporta reconhecimento de fala. Por favor, use Chrome ou Edge.');
        }

        return () => {
            if (recognitionRef.current) {
                recognitionRef.current.abort();
            }
        };
    }, [exerciseId]);

    const checkPronunciationWithRefs = (spoken, currentWords, wordIndex) => {
        const currentWord = currentWords[wordIndex].text.toLowerCase();

        const analysisOptions = {
            threshold: exercise?.difficulty === 'beginner' ? 70 :
                exercise?.difficulty === 'intermediate' ? 80 : 85,
            strictMode: exercise?.difficulty === 'advanced',
            focusOnSound: exercise?.focusSound
        };

        console.log("Verificando pronúncia com análise fonética:", {
            falado: spoken,
            esperado: currentWord,
            indice: wordIndex,
            totalPalavras: currentWords.length,
            opcoes: analysisOptions
        });

        const analysis = phoneticAnalyzer.isPhoneticMatch(spoken, currentWord, analysisOptions.threshold);
        setPhoneticAnalysis(analysis);

        console.log("Resultado da análise fonética:", analysis);

        console.log("Evento STT (local):", {
            exerciseId,
            word: currentWord,
            transcript: spoken,
            success: analysis.match,
            phonetics: analysis.phonetics,
            similarity: analysis.similarity
        });

        if (analysis.match) {
            let feedbackMessage = '';

            if (analysis.exactMatch || analysis.similarity > 95) {
                feedbackMessage = 'Excelente! Pronúncia perfeita!';
            } else if (analysis.similarity > 85) {
                feedbackMessage = 'Muito bem! Pronúncia correta.';
            } else {
                feedbackMessage = 'Bom trabalho! Pronúncia aceitável.';
            }

            setFeedback(feedbackMessage);
            setScore(prevScore => prevScore + 10);

            if (!analysis.exactMatch && analysis.similarity < 95) {
                setTimeout(() => {
                    setFeedback(prev => `${prev} (Similaridade: ${analysis.similarity}%)`);
                }, 500);
            }

            setTimeout(() => {
                if (wordIndex < currentWords.length - 1) {
                    setCurrentWordIndex(prevIndex => prevIndex + 1);
                    setTranscript('');
                    setFeedback('');
                    setPhoneticAnalysis(null);
                } else {
                    setCompleted(true);
                    console.log("Exercício completo:", {
                        exerciseId,
                        score: score + 10,
                        completedWords: currentWords.length
                    });
                }
            }, 1500);
        } else {
            let feedbackMessage = `Tente novamente. A palavra era "${currentWord}".`;

            if (analysis.possibleErrors && analysis.possibleErrors.length > 0) {
                const error = analysis.possibleErrors[0];
                feedbackMessage += ` Tente prestar atenção especial ao som "${error.type.replace(/[\/\^$]/g, '')}" no início da palavra.`;
            } else if (analysis.similarity > 50) {
                feedbackMessage += ` Você chegou perto! (Similaridade: ${analysis.similarity}%)`;
            }

            setFeedback(feedbackMessage);
        }
    };

    const checkPronunciation = (spoken) => {
        console.warn("Função antiga checkPronunciation chamada - deve usar checkPronunciationWithRefs");
    };

    const startListening = () => {
        console.log("startListening - Estado atual:", {
            wordsState: words.length,
            wordsRef: wordsRef.current.length,
            currentWordIndex,
            currentWordIndexRef: currentWordIndexRef.current
        });

        if (!wordsRef.current || wordsRef.current.length === 0) {
            setFeedback('Erro: Nenhuma palavra para praticar. Tente recarregar a página.');
            return;
        }

        setFeedback('');
        setTranscript('');
        setIsListening(true);
        recognitionRef.current.start();
    };

    const handleFinish = () => {
        navigate('/dashboard');
    };

    const fetchAvatarData = async (word) => {
        try {
            setAvatarData(null);

            const generateSpeech = () => {
                return new Promise((resolve) => {
                    if ('speechSynthesis' in window) {
                        const utterance = new SpeechSynthesisUtterance(word);
                        utterance.lang = 'pt-BR';

                        const estimatedDuration = word.length * 0.1;

                        const mockData = getMockLipsyncForWord(word);

                        resolve({
                            word,
                            lipsyncData: mockData.lipsyncData,
                            audioSrc: 'silent',
                            useWebSpeech: true
                        });
                    } else {
                        const mockData = getMockLipsyncForWord(word);
                        resolve({
                            word,
                            lipsyncData: mockData.lipsyncData,
                            audioSrc: mockData.audioSrc,
                            useWebSpeech: false
                        });
                    }
                });
            };

            const data = await generateSpeech();
            setAvatarData(data);
        } catch (error) {
            console.error('Failed to fetch avatar data:', error);
        }
    };

    const fetchWordAudio = async (word) => {
        if (!word) return;

        try {
            setIsLoadingAudio(true);
            const response = await api.post('/api/synthesize-speech', {
                text: word,
                voice_settings: {
                    language_code: 'pt-PT'
                }
            });

            if (response.data && response.data.audio_data) {
                setWordAudio(response.data.audio_data);
                console.log('Áudio recebido para a palavra:', word);
            } else {
                console.warn('Nenhum áudio recebido para a palavra:', word);
            }
        } catch (err) {
            console.error('Erro ao obter áudio da palavra:', err);
        } finally {
            setIsLoadingAudio(false);
        }
    };

    useEffect(() => {
        if (words && words.length > 0 && currentWordIndex < words.length) {
            fetchWordAudio(words[currentWordIndex].text);
            fetchAvatarData(words[currentWordIndex].text);
        }
    }, [currentWordIndex, words]);

    if (loading) return (
        <div className="exercise-loading">
            <div className="spinner"></div>
            <p>Carregando exercício...</p>
        </div>
    );

    if (error) return (
        <div className="exercise-error">
            <h2>Erro!</h2>
            <p>{error}</p>
            <button onClick={() => navigate('/dashboard')}>Voltar ao Dashboard</button>
        </div>
    );

    if (!exercise || !words || words.length === 0) {
        return (
            <div className="exercise-error">
                <h2>Dados Incompletos</h2>
                <p>Não foi possível carregar as palavras para este exercício.</p>
                <button onClick={() => navigate('/dashboard')}>Voltar ao Dashboard</button>
            </div>
        );
    }

    const currentWord = words[currentWordIndex];

    return (
        <div className="exercise-container">
            {usingFallbackData && (
                <div className="fallback-warning">
                    Modo offline ativado: usando dados locais
                </div>
            )}

            {!completed ? (
                <>
                    <header className="exercise-header">
                        <h1>{exercise.title}</h1>
                        <span className="progress-indicator">
                            Palavra {currentWordIndex + 1} de {words.length}
                        </span>
                    </header>

                    <div className="exercise-content">
                        <div className="exercise-instructions">
                            <p>{exercise.instructions}</p>
                        </div>

                        <div className="current-word-container">
                            <h2 className="current-word">{currentWord.text}</h2>
                            <p className="word-hint">Dica: {currentWord.hint}</p>

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

                            {isLoadingAudio && (
                                <div className="loading-audio">
                                    <p>Carregando áudio...</p>
                                </div>
                            )}
                        </div>

                        {avatarData && (
                            <div className="avatar-demonstration">
                                <h3>Demonstração: "{avatarData.word}"</h3>
                                <AvatarRenderer
                                    audioSrc={avatarData.audioSrc}
                                    lipsyncData={avatarData.lipsyncData}
                                    onPlayComplete={() => setPlayingAvatar(false)}
                                />
                                <button
                                    className="replay-button"
                                    onClick={() => {
                                        setPlayingAvatar(true);
                                        const currentData = { ...avatarData };
                                        setAvatarData(null);
                                        setTimeout(() => setAvatarData(currentData), 10);
                                    }}
                                    disabled={playingAvatar}
                                >
                                    ↺ Repetir Demonstração
                                </button>
                            </div>
                        )}

                        <div className="speech-controls">
                            <button
                                className={`listen-button ${isListening ? 'listening' : ''}`}
                                onClick={startListening}
                                disabled={isListening}
                            >
                                {isListening ? 'Ouvindo...' : 'Iniciar'}
                            </button>

                            {transcript && (
                                <div className="transcript-container">
                                    <p>Você disse: <strong>{transcript}</strong></p>
                                </div>
                            )}

                            {feedback && (
                                <div className={`feedback ${feedback.includes('Muito bem') || feedback.includes('Excelente') || feedback.includes('Bom trabalho') ? 'positive' : 'negative'}`}>
                                    {feedback}
                                </div>
                            )}

                            {phoneticAnalysis && (
                                <PhoneticFeedback
                                    analysis={phoneticAnalysis}
                                    word={words[currentWordIndex].text}
                                />
                            )}
                        </div>
                    </div>
                </>
            ) : (
                <div className="exercise-completed">
                    <h2>Exercício Concluído!</h2>
                    <div className="completion-details">
                        <p>Sua pontuação: <strong>{score}</strong></p>
                        <p>Palavras praticadas: <strong>{words.length}</strong></p>
                    </div>
                    <button onClick={handleFinish} className="finish-button">
                        Voltar ao Dashboard
                    </button>
                </div>
            )}
        </div>
    );
};

export default Exercise;