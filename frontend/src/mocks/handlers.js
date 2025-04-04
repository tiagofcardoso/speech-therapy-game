import { rest } from 'msw';

export const handlers = [
    // Mock the login endpoint
    rest.post('/api/auth/login', (req, res, ctx) => {
        const { username, password } = req.body;

        if (username === 'testuser' && password === 'password') {
            return res(
                ctx.status(200),
                ctx.json({
                    success: true,
                    user_id: 'test123',
                    token: 'fake-jwt-token',
                    name: 'Test User'
                })
            );
        }

        return res(
            ctx.status(401),
            ctx.json({
                success: false,
                message: 'Invalid username or password'
            })
        );
    }),

    // Mock the start game endpoint
    rest.post('/api/start_game', (req, res, ctx) => {
        return res(
            ctx.status(200),
            ctx.json({
                session_id: 'test-session',
                instructions: {
                    greeting: 'Hello!',
                    explanation: 'We will practice pronunciation',
                    encouragement: 'You can do it!'
                },
                current_exercise: {
                    word: 'cat',
                    prompt: 'This animal says meow',
                    hint: 'Start with a k sound',
                    visual_cue: 'A furry pet with whiskers',
                    index: 0,
                    total: 5
                }
            })
        );
    }),

    // Mock the speech recognition endpoint
    rest.post('/api/recognize', (req, res, ctx) => {
        return res(
            ctx.status(200),
            ctx.json({
                recognized_text: 'cat'
            })
        );
    })
];