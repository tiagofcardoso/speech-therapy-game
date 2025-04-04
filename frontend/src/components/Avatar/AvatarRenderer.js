import React, { useEffect, useRef, useState } from 'react';
import * as THREE from 'three';
import { GLTFLoader } from 'three/examples/jsm/loaders/GLTFLoader';
import { KTX2Loader } from 'three/examples/jsm/loaders/KTX2Loader';
import { DRACOLoader } from 'three/examples/jsm/loaders/DRACOLoader';
import './AvatarRenderer.css';

const AvatarRenderer = ({ audioSrc, lipsyncData, modelUrl, onPlayComplete }) => {
    const containerRef = useRef(null);
    const sceneRef = useRef(null);
    const rendererRef = useRef(null);
    const cameraRef = useRef(null);
    const avatarRef = useRef(null);
    const mouthRef = useRef(null);
    const mixerRef = useRef(null);
    const audioRef = useRef(null);
    const animationFrameRef = useRef(null);
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState(null);

    // Initialize Three.js scene
    useEffect(() => {
        if (!containerRef.current) return;

        try {
            console.log("Initializing 3D scene...");

            // Setup scene
            const scene = new THREE.Scene();
            sceneRef.current = scene;
            scene.background = new THREE.Color(0xf0f0f0);

            // Setup camera
            const camera = new THREE.PerspectiveCamera(
                50,
                containerRef.current.clientWidth / containerRef.current.clientHeight,
                0.1,
                1000
            );
            cameraRef.current = camera;
            camera.position.z = 1;
            camera.position.y = 0.1;

            // Setup renderer
            const renderer = new THREE.WebGLRenderer({ antialias: true });
            rendererRef.current = renderer;
            renderer.setSize(containerRef.current.clientWidth, containerRef.current.clientHeight);
            renderer.setClearColor(0xf0f0f0);
            renderer.setPixelRatio(window.devicePixelRatio);
            containerRef.current.appendChild(renderer.domElement);

            // Add lights
            const ambientLight = new THREE.AmbientLight(0xffffff, 0.5);
            scene.add(ambientLight);

            const directionalLight = new THREE.DirectionalLight(0xffffff, 0.8);
            directionalLight.position.set(0, 1, 1);
            scene.add(directionalLight);

            // Set up enhanced sphere model with animated mouth
            createEnhancedFallbackModel();

            // Animation loop
            const animate = () => {
                animationFrameRef.current = requestAnimationFrame(animate);

                // Update any animations
                if (mixerRef.current) {
                    mixerRef.current.update(0.016);
                }

                renderer.render(scene, camera);
            };

            animate();

            // Handle window resize
            const handleResize = () => {
                if (!containerRef.current) return;

                camera.aspect = containerRef.current.clientWidth / containerRef.current.clientHeight;
                camera.updateProjectionMatrix();
                renderer.setSize(containerRef.current.clientWidth, containerRef.current.clientHeight);
            };

            window.addEventListener('resize', handleResize);

            // Cleanup
            return () => {
                window.removeEventListener('resize', handleResize);
                if (containerRef.current && renderer.domElement) {
                    containerRef.current.removeChild(renderer.domElement);
                }
                if (renderer) renderer.dispose();
                cancelAnimationFrame(animationFrameRef.current);
            };
        } catch (err) {
            console.error('Error initializing 3D scene:', err);
            setError(`Failed to initialize 3D scene: ${err.message}`);
            setLoading(false);
        }
    }, []);

    // Create an enhanced fallback model with animated mouth
    const createEnhancedFallbackModel = () => {
        if (!sceneRef.current) return;

        console.log("Creating enhanced fallback model with animated mouth");

        const scene = sceneRef.current;

        // Create head
        const headGeometry = new THREE.SphereGeometry(0.5, 32, 32);
        const headMaterial = new THREE.MeshStandardMaterial({
            color: 0xf5d2c1,
            roughness: 0.7
        });
        const head = new THREE.Mesh(headGeometry, headMaterial);
        scene.add(head);
        avatarRef.current = head;

        // Add eyes
        const eyeGeometry = new THREE.SphereGeometry(0.08, 32, 16);
        const eyeMaterial = new THREE.MeshBasicMaterial({ color: 0x444444 });

        const leftEye = new THREE.Mesh(eyeGeometry, eyeMaterial);
        leftEye.position.set(-0.15, 0.1, 0.45);
        head.add(leftEye);

        const rightEye = new THREE.Mesh(eyeGeometry, eyeMaterial);
        rightEye.position.set(0.15, 0.1, 0.45);
        head.add(rightEye);

        // Create mouth as a separate entity that we can animate
        const mouthGeometry = new THREE.RingGeometry(0.1, 0.15, 32, 1, 0, Math.PI);
        const mouthMaterial = new THREE.MeshBasicMaterial({
            color: 0x333333,
            side: THREE.DoubleSide
        });
        const mouth = new THREE.Mesh(mouthGeometry, mouthMaterial);
        mouth.position.set(0, -0.15, 0.45);
        mouth.rotation.set(0, 0, 0);
        head.add(mouth);
        mouthRef.current = mouth;

        // Add rotation for a more dynamic appearance
        head.rotation.y = -0.3;

        setLoading(false);
    };

    // Handle lipsync animation with audio
    useEffect(() => {
        if (loading || !lipsyncData || !avatarRef.current) return;

        let timers = [];
        let utterance = null;

        try {
            console.log("Setting up lipsync...", lipsyncData);

            // Simplified animation system that works with our fallback model
            const animateMouth = (viseme, intensity) => {
                if (!mouthRef.current) return;

                console.log(`Applying viseme: ${viseme} with intensity: ${intensity}`);

                // Simple mouth shapes based on viseme
                switch (viseme) {
                    case 'A': // Open mouth for vowels
                        mouthRef.current.scale.set(1, 2.5 * intensity, 1);
                        break;
                    case 'B': // Closed mouth for 'b', 'p', 'm'
                        mouthRef.current.scale.set(1, 0.5 * intensity, 1);
                        break;
                    case 'F': // Mouth for 'f', 'v'
                        mouthRef.current.scale.set(0.8, 1.2 * intensity, 1);
                        break;
                    case 'D': // Mouth for 'd', 't', 'n'
                        mouthRef.current.scale.set(1, 1.5 * intensity, 1);
                        break;
                    case 'C': // Mouth for 'k', 'g'
                        mouthRef.current.scale.set(0.7, 1.8 * intensity, 1);
                        break;
                    case 'X': // Neutral mouth
                    default:
                        mouthRef.current.scale.set(1, 1, 1);
                        break;
                }
            };

            const startAnimation = () => {
                console.log("Starting animation");

                // Reset mouth to neutral
                animateMouth('X', 0);

                // Schedule viseme changes
                lipsyncData.forEach(({ start, end, value }) => {
                    const startTimer = setTimeout(() => {
                        animateMouth(value, 1.0);
                    }, start * 1000);

                    const endTimer = setTimeout(() => {
                        animateMouth('X', 0);
                    }, end * 1000);

                    timers.push(startTimer, endTimer);
                });

                // Calculate total duration
                const lastViseme = lipsyncData[lipsyncData.length - 1];
                const totalDuration = lastViseme ? lastViseme.end + 0.5 : 1;

                // Set a timer to call onPlayComplete
                const completeTimer = setTimeout(() => {
                    console.log("Animation complete");
                    animateMouth('X', 0);

                    if (onPlayComplete) {
                        onPlayComplete();
                    }
                }, totalDuration * 1000);

                timers.push(completeTimer);
            };

            // Check if we're using audioSrc or web speech
            if (audioSrc === 'silent') {
                // Use Web Speech API
                if ('speechSynthesis' in window) {
                    utterance = new SpeechSynthesisUtterance(lipsyncData[0]?.word || "");
                    utterance.lang = 'pt-BR';

                    // Start animation first, then speak
                    startAnimation();
                    window.speechSynthesis.speak(utterance);
                } else {
                    // Just start animation if speech not available
                    startAnimation();
                }
            } else if (audioSrc) {
                // Use provided audio source
                console.log("Playing audio:", audioSrc);
                const audio = new Audio(audioSrc);
                audioRef.current = audio;

                // Setup lipsync timing with audio events
                audio.addEventListener('play', startAnimation);

                // Handle playback completion
                audio.addEventListener('ended', () => {
                    console.log("Audio playback completed");
                    animateMouth('X', 0);

                    if (onPlayComplete) {
                        onPlayComplete();
                    }
                });

                // Play the audio
                audio.play().catch(err => {
                    console.error('Error playing audio:', err);
                    setError('Failed to play audio: ' + err.message);

                    // If audio fails, still run the animation
                    startAnimation();
                });
            } else {
                // No audio, just run the animation
                startAnimation();
            }
        } catch (err) {
            console.error('Error setting up lipsync:', err);
            setError('Failed to setup lipsync: ' + err.message);
        }

        // Cleanup function
        return () => {
            if (audioRef.current) {
                audioRef.current.pause();
                audioRef.current = null;
            }

            if (utterance && window.speechSynthesis) {
                window.speechSynthesis.cancel();
            }

            timers.forEach(timer => clearTimeout(timer));
        };
    }, [audioSrc, lipsyncData, loading, onPlayComplete]);

    return (
        <div className="avatar-container" ref={containerRef}>
            {loading && (
                <div className="avatar-loading">Carregando avatar...</div>
            )}
            {error && (
                <div className="avatar-error">{error}</div>
            )}
        </div>
    );
};

export default AvatarRenderer;