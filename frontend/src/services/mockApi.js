// Mock API for testing lip sync functionality

export const generateMockLipsync = (word) => {
    // Generate more realistic mock lipsync data based on the word
    const lipsyncData = [];
    let currentTime = 0.2; // Start with a small delay

    // Vowels should be longer than consonants
    const vowels = 'aeiouáàâãéèêíìîóòôõúùû';
    const bilabials = 'bpm';
    const labiodentals = 'fv';
    const dentals = 'tdnszl';
    const velars = 'kg';

    // Generate viseme for each character
    for (let i = 0; i < word.length; i++) {
        const char = word[i].toLowerCase();

        // Map character to viseme and duration
        let viseme = 'X';
        let duration = 0.1; // Default duration

        if (vowels.includes(char)) {
            viseme = 'A';
            duration = 0.2; // Vowels are longer
        } else if (bilabials.includes(char)) {
            viseme = 'B';
            duration = 0.1;
        } else if (labiodentals.includes(char)) {
            viseme = 'F';
            duration = 0.1;
        } else if (dentals.includes(char)) {
            viseme = 'D';
            duration = 0.1;
        } else if (velars.includes(char)) {
            viseme = 'C';
            duration = 0.1;
        } else {
            // For other characters like spaces, use neutral viseme
            viseme = 'X';
            duration = 0.05;
            continue; // Skip to next character, don't add to lipsync data
        }

        // Add viseme with timing
        lipsyncData.push({
            start: currentTime,
            end: currentTime + duration,
            value: viseme
        });

        // Move to next position
        currentTime += duration + 0.02; // Add small gap between phonemes
    }

    // Add neutral viseme at the end
    lipsyncData.push({
        start: currentTime,
        end: currentTime + 0.2,
        value: 'X'
    });

    return lipsyncData;
};

export const getMockAudio = (word) => {
    // Since we don't have actual audio files yet, let's create a more realistic
    // mock by using the browser's speech synthesis capability

    // For browsers that support it, generate a data URL with speech audio
    // But for now, just return a silent audio that won't cause errors
    return 'data:audio/wav;base64,UklGRigAAABXQVZFZm10IBIAAAABAAEARKwAAIhYAQACABAAAABkYXRhAgAAAAEA';
};

export const getMockLipsyncForWord = (word) => {
    // Generate mock data for testing
    return {
        word,
        lipsyncData: generateMockLipsync(word).map(item => ({ ...item, word })),
        audioSrc: getMockAudio(word)
    };
};