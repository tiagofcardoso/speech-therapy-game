import React, { useEffect, useRef } from 'react';
import './SimpleConfetti.css';

const SimpleConfetti = ({ active = true, duration = 5000, particleCount = 100 }) => {
    const canvasRef = useRef(null);
    const particles = useRef([]);
    const animationFrameId = useRef(null);
    const startTimeRef = useRef(null);

    // Create particles with random properties
    const createParticles = (canvas) => {
        const ctx = canvas.getContext('2d');
        const width = canvas.width;
        const height = canvas.height;

        particles.current = [];

        for (let i = 0; i < particleCount; i++) {
            const size = Math.random() * 10 + 5;
            particles.current.push({
                x: Math.random() * width,
                y: Math.random() * height - height,
                size,
                color: getRandomColor(),
                speed: Math.random() * 3 + 2,
                angle: Math.random() * 6.28, // 0 to 2π
                rotation: Math.random() * 0.2 - 0.1,
                rotationSpeed: Math.random() * 0.01,
            });
        }
    };

    // Get a random color for confetti
    const getRandomColor = () => {
        const colors = [
            '#FF5252', // red
            '#FFEB3B', // yellow
            '#2196F3', // blue
            '#4CAF50', // green
            '#E040FB', // purple
            '#FF9800', // orange
        ];
        return colors[Math.floor(Math.random() * colors.length)];
    };

    // Animation loop
    const animate = (timestamp) => {
        if (!startTimeRef.current) startTimeRef.current = timestamp;
        const elapsedTime = timestamp - startTimeRef.current;

        if (elapsedTime > duration) {
            cancelAnimationFrame(animationFrameId.current);
            return;
        }

        const canvas = canvasRef.current;
        const ctx = canvas.getContext('2d');
        const width = canvas.width;
        const height = canvas.height;

        ctx.clearRect(0, 0, width, height);

        particles.current.forEach(particle => {
            // Update position
            particle.y += particle.speed;
            particle.x += Math.sin(particle.angle) * 0.5;

            // Update rotation
            particle.rotation += particle.rotationSpeed;

            // Draw particle
            ctx.save();
            ctx.translate(particle.x, particle.y);
            ctx.rotate(particle.rotation);
            ctx.fillStyle = particle.color;
            ctx.fillRect(-particle.size / 2, -particle.size / 2, particle.size, particle.size);
            ctx.restore();

            // Reset if particle goes below the screen
            if (particle.y > height) {
                particle.y = -particle.size;
                particle.x = Math.random() * width;
            }
        });

        animationFrameId.current = requestAnimationFrame(animate);
    };

    useEffect(() => {
        if (!active) return;

        const canvas = canvasRef.current;
        const resizeCanvas = () => {
            canvas.width = window.innerWidth;
            canvas.height = window.innerHeight;
        };

        resizeCanvas();
        window.addEventListener('resize', resizeCanvas);

        createParticles(canvas);
        startTimeRef.current = null;
        animationFrameId.current = requestAnimationFrame(animate);

        return () => {
            cancelAnimationFrame(animationFrameId.current);
            window.removeEventListener('resize', resizeCanvas);
        };
    }, [active, particleCount, duration]);

    if (!active) return null;

    return (
        <canvas
            ref={canvasRef}
            className="simple-confetti"
        />
    );
};

export default SimpleConfetti;