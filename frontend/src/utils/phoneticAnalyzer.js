/**
 * Utilitário para análise fonética avançada em português brasileiro
 */

// Tabela de equivalência fonética para sons similares em português
const PHONETIC_EQUIVALENTS = {
    // Vogais
    'a': ['a', 'á', 'à', 'ã', 'â'],
    'e': ['e', 'é', 'ê'],
    'i': ['i', 'í'],
    'o': ['o', 'ó', 'ô', 'õ'],
    'u': ['u', 'ú'],

    // Consoantes problemáticas em terapia de fala
    'r': ['r', 'rr'], // Diferentes formas do R em português
    'l': ['l', 'u'], // Substituição comum de L por U no final de palavras
    's': ['s', 'ss', 'ç', 'z', 'x', 'sc', 'xc'],
    't': ['t', 'd'], // Confusão entre T e D
    'p': ['p', 'b'], // Confusão entre P e B
    'k': ['c', 'k', 'q'], // Sons de K
    'g': ['g', 'j'], // Sons similares para alguns falantes
    'f': ['f', 'v'], // Confusão entre F e V
};

// Mapeamento de caracteres para representação fonética simplificada
const PHONETIC_MAP = {
    'ch': 'x', 'lh': 'ly', 'nh': 'ny',
    'rr': 'h', 'sc': 's', 'sç': 's',
    'xc': 's', 'ç': 's', 'ss': 's',
    'x': 'x', 'z': 'z',
};

// Substituições comuns para erros de pronúncia em terapia da fala
const COMMON_SPEECH_SUBSTITUTIONS = [
    { pattern: /^r/, replacement: 'l' }, // Rotacismo: substituição de R por L
    { pattern: /^l/, replacement: 'r' }, // Substituição de L por R
    { pattern: /^s/, replacement: 't' }, // Sigmatismo: problemas com S
    { pattern: /s$/, replacement: '' },  // Omissão de S final
    { pattern: /r$/, replacement: '' },  // Omissão de R final
    { pattern: /^pr/, replacement: 'p' }, // Simplificação de encontros consonantais
    { pattern: /^tr/, replacement: 't' },
    { pattern: /^br/, replacement: 'b' },
    { pattern: /^gr/, replacement: 'g' },
    { pattern: /^fr/, replacement: 'f' },
];

/**
 * Converte uma palavra para sua representação fonética simplificada
 * @param {string} word - A palavra a ser convertida
 * @returns {string} - Representação fonética da palavra
 */
const toPhoneticRepresentation = (word) => {
    if (!word) return '';

    // Converter para minúsculas e remover acentos
    let phonetic = word.toLowerCase()
        .normalize("NFD")
        .replace(/[\u0300-\u036f]/g, "");

    // Aplicar substituições de dígrafos
    Object.entries(PHONETIC_MAP).forEach(([pattern, replacement]) => {
        phonetic = phonetic.replace(new RegExp(pattern, 'g'), replacement);
    });

    // Para análise de terapia da fala, preservar certas características
    // como repetição de consoantes pode ser útil para avaliar a pronúncia
    return phonetic;
};

/**
 * Calcula a similaridade fonética entre duas palavras
 * @param {string} spoken - O que foi falado
 * @param {string} target - A palavra alvo
 * @returns {number} - Pontuação de similaridade (0-100)
 */
const calculatePhoneticSimilarity = (spoken, target) => {
    if (!spoken || !target) return 0;

    // Converter para representação fonética
    const phoneticSpoken = toPhoneticRepresentation(spoken);
    const phoneticTarget = toPhoneticRepresentation(target);

    // Uso de distância de Levenshtein para calcular similaridade
    const distance = levenshteinDistance(phoneticSpoken, phoneticTarget);
    const maxLength = Math.max(phoneticSpoken.length, phoneticTarget.length);

    // Converter distância em similaridade (0-100)
    const similarity = ((maxLength - distance) / maxLength) * 100;
    return Math.round(similarity);
};

/**
 * Calcula a distância de Levenshtein entre duas strings
 * @param {string} a - Primeira string
 * @param {string} b - Segunda string
 * @returns {number} - Distância de edição
 */
const levenshteinDistance = (a, b) => {
    if (a.length === 0) return b.length;
    if (b.length === 0) return a.length;

    const matrix = [];

    // Inicializar matriz
    for (let i = 0; i <= b.length; i++) {
        matrix[i] = [i];
    }
    for (let j = 0; j <= a.length; j++) {
        matrix[0][j] = j;
    }

    // Preencher matriz
    for (let i = 1; i <= b.length; i++) {
        for (let j = 1; j <= a.length; j++) {
            const cost = a[j - 1] === b[i - 1] ? 0 : 1;
            matrix[i][j] = Math.min(
                matrix[i - 1][j] + 1,        // deleção
                matrix[i][j - 1] + 1,        // inserção
                matrix[i - 1][j - 1] + cost  // substituição
            );

            // Considerar equivalências fonéticas (custo 0.5 em vez de 1)
            if (cost !== 0) {
                const aChar = a[j - 1];
                const bChar = b[i - 1];

                // Verificar se os caracteres são foneticamente equivalentes
                for (const [key, equivalents] of Object.entries(PHONETIC_EQUIVALENTS)) {
                    if (equivalents.includes(aChar) && equivalents.includes(bChar)) {
                        // Se forem equivalentes, reduzir o custo
                        matrix[i][j] = Math.min(matrix[i][j], matrix[i - 1][j - 1] + 0.5);
                        break;
                    }
                }
            }
        }
    }

    return matrix[b.length][a.length];
};

/**
 * Verifica se a palavra falada é foneticamente semelhante à palavra alvo
 * @param {string} spoken - O que foi falado
 * @param {string} target - A palavra alvo
 * @param {number} threshold - Limiar de aceitação (0-100)
 * @returns {object} - Resultado da análise
 */
const isPhoneticMatch = (spoken, target, threshold = 75) => {
    // Verificar correspondência exata
    if (spoken.includes(target)) {
        return {
            match: true,
            similarity: 100,
            phonetics: {
                original: target,
                spoken: spoken
            },
            exactMatch: true
        };
    }

    // Calcular similaridade fonética
    const similarity = calculatePhoneticSimilarity(spoken, target);

    // Verificar variações comuns de erros de pronúncia
    const possibleVariations = COMMON_SPEECH_SUBSTITUTIONS.map(({ pattern, replacement }) => {
        return target.replace(pattern, replacement);
    });

    // Verificar se a palavra falada contém alguma das variações
    const containsVariation = possibleVariations.some(variation => spoken.includes(variation));

    // Se contém uma variação ou tem alta similaridade, considerar match
    const isMatch = similarity >= threshold || containsVariation;

    return {
        match: isMatch,
        similarity,
        phonetics: {
            original: toPhoneticRepresentation(target),
            spoken: toPhoneticRepresentation(spoken)
        },
        possibleErrors: containsVariation ?
            COMMON_SPEECH_SUBSTITUTIONS.filter(({ pattern }) => pattern.test(target))
                .map(({ pattern, replacement }) => ({
                    type: pattern.toString(),
                    expected: target,
                    common: target.replace(pattern, replacement)
                })) :
            []
    };
};

/**
 * Extrai palavras relevantes de uma frase falada
 * @param {string} phrase - A frase completa
 * @returns {string[]} - Palavras extraídas
 */
const extractRelevantWords = (phrase) => {
    if (!phrase) return [];

    // Remover palavras irrelevantes (artigos, preposições, etc.)
    const stopWords = ['o', 'a', 'os', 'as', 'um', 'uma', 'uns', 'umas', 'de', 'da', 'do', 'das', 'dos', 'em', 'no', 'na', 'nos', 'nas', 'por', 'para', 'e', 'ou', 'que', 'se', 'eu', 'tu', 'ele', 'ela'];

    return phrase.toLowerCase()
        .split(/\s+/)
        .filter(word => word.length > 1 && !stopWords.includes(word));
};

/**
 * Analisa a pronúncia para exercícios de terapia da fala
 * @param {string} spoken - O que foi falado
 * @param {string} target - A palavra ou frase alvo
 * @param {Object} options - Opções de configuração
 * @returns {Object} - Resultado detalhado da análise
 */
const analyzePronunciation = (spoken, target, options = {}) => {
    const {
        threshold = 75,
        strictMode = false, // Se verdadeiro, requer pronúncia mais precisa
        focusOnSound = null, // Som específico para focar (ex: 'r', 'l', 's')
    } = options;

    // Tratamento especial para exercícios que focam em sons específicos
    const adjustedThreshold = focusOnSound ?
        // Ser mais rigoroso com o som específico sendo praticado
        threshold + 10 : threshold;

    // Para palavras únicas
    if (!target.includes(' ')) {
        return isPhoneticMatch(spoken, target, adjustedThreshold);
    }

    // Para frases
    const targetWords = extractRelevantWords(target);
    const spokenWords = extractRelevantWords(spoken);

    // Análise palavra por palavra
    const wordAnalysis = targetWords.map(targetWord => {
        // Encontrar a melhor correspondência entre as palavras faladas
        let bestMatch = { match: false, similarity: 0 };
        let matchedWord = '';

        for (const spokenWord of spokenWords) {
            const analysis = isPhoneticMatch(spokenWord, targetWord, adjustedThreshold);
            if (analysis.similarity > bestMatch.similarity) {
                bestMatch = analysis;
                matchedWord = spokenWord;
            }
        }

        return {
            targetWord,
            matchedWord,
            ...bestMatch
        };
    });

    // Calcular pontuação geral
    const matchedWords = wordAnalysis.filter(w => w.match).length;
    const totalScore = (matchedWords / targetWords.length) * 100;
    const averageSimilarity = wordAnalysis.reduce((sum, w) => sum + w.similarity, 0) / wordAnalysis.length;

    return {
        match: strictMode ? totalScore >= 90 : totalScore >= 70,
        overallScore: Math.round(totalScore),
        averageSimilarity: Math.round(averageSimilarity),
        wordByWord: wordAnalysis,
        missedWords: wordAnalysis.filter(w => !w.match).map(w => w.targetWord),
    };
};

export default {
    analyzePronunciation,
    isPhoneticMatch,
    calculatePhoneticSimilarity,
    toPhoneticRepresentation,
    extractRelevantWords
};