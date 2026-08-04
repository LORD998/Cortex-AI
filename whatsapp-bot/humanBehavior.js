// humanBehavior.js

/**
 * Calculates a realistic typing delay based on the length of the text.
 * @param {string} text 
 * @returns {number} delay in milliseconds
 */
function calculateTypingDelay(text) {
    const wpm = 60; // Words per minute (average human)
    const cps = (wpm * 5) / 60; // Characters per second (approx 5 chars per word)
    const msPerChar = 1000 / cps;
    
    // Add a base delay + time per character + some randomness (up to 500ms)
    const baseDelay = 1000;
    const typingTime = text.length * msPerChar;
    const randomFactor = Math.random() * 500;
    
    // Cap at a max of 8 seconds to not leave the user waiting forever
    return Math.min(baseDelay + typingTime + randomFactor, 8000); 
}

/**
 * Utility to pause execution
 * @param {number} ms 
 * @returns {Promise<void>}
 */
const sleep = (ms) => new Promise((resolve) => setTimeout(resolve, ms));

/**
 * Splits a long response into multiple shorter messages, mimicking human texting.
 * Splits by double newlines or sentences if it's too long.
 * @param {string} text 
 * @returns {string[]}
 */
function splitIntoHumanMessages(text) {
    // Split by double newline first (paragraphs)
    let chunks = text.split(/\n\s*\n/);
    
    // If a chunk is still too long (> 150 chars), split by sentences
    const finalChunks = [];
    for (let chunk of chunks) {
        if (chunk.length > 150) {
            const sentences = chunk.match(/[^.!?]+[.!?]+/g) || [chunk];
            let current = "";
            for (let sentence of sentences) {
                if ((current + sentence).length < 150) {
                    current += sentence;
                } else {
                    if (current) finalChunks.push(current.trim());
                    current = sentence;
                }
            }
            if (current) finalChunks.push(current.trim());
        } else {
            finalChunks.push(chunk.trim());
        }
    }
    
    return finalChunks.filter(c => c.length > 0);
}

module.exports = {
    calculateTypingDelay,
    sleep,
    splitIntoHumanMessages
}
