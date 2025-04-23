/**
 * Global audio playback manager that enforces sequential playback
 * and prevents audio conflicts
 */

class AudioManager {
    constructor() {
        this.players = new Map(); // Map of audio players by ID
        this.playQueue = []; // Queue of audio players waiting to play
        this.currentlyPlaying = null; // Currently playing player ID
        this.isProcessingQueue = false; // Flag to prevent queue processing race conditions
    }

    /**
     * Register an audio player with the manager
     * @param {string} id - Unique ID for the player
     * @param {Audio} audioElement - HTML Audio element
     * @param {Function} onPlayStateChange - Function to call when play state changes
     * @param {Function} onPlayComplete - Function to call when playback completes
     * @returns {Function} - Unregister function
     */
    register(id, audioElement, onPlayStateChange, onPlayComplete = null) {
        console.log(`🎧 AudioManager: Registering player ${id}`);

        // Check if player already exists with same ID
        if (this.players.has(id)) {
            const existingPlayer = this.players.get(id);
            const sameElement = existingPlayer.element === audioElement;

            if (sameElement) {
                console.log(`🎧 AudioManager: Player ${id} already registered with same element, skipping`);
                // Just update callbacks if they changed
                existingPlayer.onPlayStateChange = onPlayStateChange;
                existingPlayer.onPlayComplete = onPlayComplete;
                return () => this.unregister(id);
            } else {
                console.log(`🎧 AudioManager: Updating existing player ${id} with new audio element`);

                // Clean up old event listeners
                this._cleanupEventListeners(existingPlayer);

                // Update properties
                existingPlayer.element = audioElement;
                existingPlayer.onPlayStateChange = onPlayStateChange;
                existingPlayer.onPlayComplete = onPlayComplete;
            }
        } else {
            // Create new player entry
            this.players.set(id, {
                id,
                element: audioElement,
                onPlayStateChange,
                onPlayComplete,
                isPlaying: false,
                priority: id.includes('feedback') ? 1 : 0, // Feedback audio gets higher priority
                eventListeners: {} // Store references to event handlers for cleanup
            });
        }

        // Get the player (either existing or newly created)
        const player = this.players.get(id);

        // Setup event listeners with stored references for later cleanup
        player.eventListeners = {
            play: () => {
                console.log(`🎧 AudioManager: ${id} started playing`);
                player.isPlaying = true;
                this.currentlyPlaying = id;
                if (player.onPlayStateChange) player.onPlayStateChange(true);
            },
            pause: () => {
                console.log(`🎧 AudioManager: ${id} paused`);
                player.isPlaying = false;
                if (this.currentlyPlaying === id) this.currentlyPlaying = null;
                if (player.onPlayStateChange) player.onPlayStateChange(false);
            },
            ended: () => {
                console.log(`🎧 AudioManager: ${id} finished playing`);
                player.isPlaying = false;
                if (this.currentlyPlaying === id) this.currentlyPlaying = null;
                if (player.onPlayStateChange) player.onPlayStateChange(false);
                if (player.onPlayComplete) player.onPlayComplete();

                // Process next item in queue
                setTimeout(() => this.processQueue(), 50);
            }
        };

        // Attach the event listeners
        audioElement.addEventListener('play', player.eventListeners.play);
        audioElement.addEventListener('pause', player.eventListeners.pause);
        audioElement.addEventListener('ended', player.eventListeners.ended);

        // Return unregister function
        return () => this.unregister(id);
    }

    /**
     * Helper method for event listener cleanup
     * @param {Object} player - Player object
     */
    _cleanupEventListeners(player) {
        if (!player || !player.element || !player.eventListeners) return;

        const { element, eventListeners } = player;

        if (eventListeners.play) {
            element.removeEventListener('play', eventListeners.play);
        }
        if (eventListeners.pause) {
            element.removeEventListener('pause', eventListeners.pause);
        }
        if (eventListeners.ended) {
            element.removeEventListener('ended', eventListeners.ended);
        }
    }

    /**
     * Unregister an audio player
     * @param {string} id - Unique ID for the player
     */
    unregister(id) {
        console.log(`🎧 AudioManager: Unregistering player ${id}`);

        const player = this.players.get(id);
        if (!player) return;

        // Clean up event listeners
        this._cleanupEventListeners(player);

        // Stop if playing
        this.stop(id);

        // Remove from queue
        this.playQueue = this.playQueue.filter(queueId => queueId !== id);

        // Remove from players map
        this.players.delete(id);

        // Reset currently playing if needed
        if (this.currentlyPlaying === id) {
            this.currentlyPlaying = null;
        }
    }

    /**
     * Play audio with the given ID
     * @param {string} id - Player ID to play
     * @param {boolean} immediate - Whether to play immediately, stopping others
     * @returns {Promise} - Resolves when playback starts or rejects on error
     */
    play(id, immediate = false) {
        return new Promise((resolve, reject) => {
            console.log(`🎧 AudioManager: Request to play ${id} (immediate: ${immediate})`);

            if (!this.players.has(id)) {
                console.error(`🎧 AudioManager: Player ${id} not found`);
                return reject(new Error(`Player ${id} not registered`));
            }

            // Get player
            const player = this.players.get(id);

            // If already playing, do nothing
            if (player.isPlaying) {
                console.log(`🎧 AudioManager: ${id} is already playing`);
                return resolve();
            }

            // If immediate or no current playback, play now
            if (immediate || !this.currentlyPlaying) {
                // Stop any current playback
                if (this.currentlyPlaying) {
                    console.log(`🎧 AudioManager: Stopping ${this.currentlyPlaying} for immediate playback of ${id}`);
                    this.stop(this.currentlyPlaying);
                }

                // Clear other queued items of the same type (word or feedback)
                if (id.includes('word')) {
                    this.playQueue = this.playQueue.filter(qId => !qId.includes('word'));
                } else if (id.includes('feedback')) {
                    this.playQueue = this.playQueue.filter(qId => !qId.includes('feedback'));
                }

                // Start playback
                console.log(`🎧 AudioManager: Starting playback of ${id}`);
                try {
                    const playPromise = player.element.play();
                    if (playPromise !== undefined) {
                        playPromise
                            .then(() => {
                                console.log(`🎧 AudioManager: Playback started successfully for ${id}`);
                                resolve();
                            })
                            .catch(err => {
                                console.error(`🎧 AudioManager: Error playing ${id}:`, err);

                                // If player was interrupted, don't count as error
                                if (err.name === 'AbortError') {
                                    console.log(`🎧 AudioManager: ${id} playback aborted`);
                                    resolve();
                                } else {
                                    player.isPlaying = false;
                                    reject(err);
                                }
                            });
                    } else {
                        // For browsers where play() doesn't return a promise
                        console.log(`🎧 AudioManager: ${id} play() did not return a promise`);
                        player.isPlaying = true;
                        this.currentlyPlaying = id;
                        resolve();
                    }
                } catch (err) {
                    console.error(`🎧 AudioManager: Error playing ${id}:`, err);
                    reject(err);
                }
            } else {
                // Otherwise, add to queue if not already queued
                if (!this.playQueue.includes(id)) {
                    console.log(`🎧 AudioManager: Adding ${id} to play queue`);

                    // Add to queue based on priority
                    if (player.priority > 0) {
                        // Insert at the beginning for high priority
                        this.playQueue.unshift(id);
                    } else {
                        // Add to end for normal priority
                        this.playQueue.push(id);
                    }

                    // Process queue (will only do something if not already processing)
                    this.processQueue();
                } else {
                    console.log(`🎧 AudioManager: ${id} already in play queue`);
                }

                // Resolve immediately since we're queuing
                resolve();
            }
        });
    }

    /**
     * Process the play queue
     */
    processQueue() {
        // Prevent concurrent queue processing
        if (this.isProcessingQueue) return;

        // If nothing is playing and queue has items, play next item
        if (!this.currentlyPlaying && this.playQueue.length > 0) {
            this.isProcessingQueue = true;

            // Get next item
            const nextId = this.playQueue.shift();
            console.log(`🎧 AudioManager: Processing queue, next player: ${nextId}`);

            // Start playback
            this.play(nextId, true)
                .catch(err => {
                    console.error(`🎧 AudioManager: Error playing queued item ${nextId}:`, err);
                })
                .finally(() => {
                    this.isProcessingQueue = false;

                    // If more items in queue, process next
                    if (this.playQueue.length > 0) {
                        setTimeout(() => this.processQueue(), 50);
                    }
                });
        } else {
            this.isProcessingQueue = false;
        }
    }

    /**
     * Stop playback of a specific player
     * @param {string} id - Player ID to stop
     */
    stop(id) {
        if (!this.players.has(id)) return;

        const player = this.players.get(id);
        if (player.element && !player.element.paused) {
            console.log(`🎧 AudioManager: Stopping playback of ${id}`);
            player.element.pause();
            if (player.element.currentTime) {
                player.element.currentTime = 0;
            }
            player.isPlaying = false;
            if (this.currentlyPlaying === id) {
                this.currentlyPlaying = null;
            }
        }
    }

    /**
     * Stop all playback
     */
    stopAll() {
        console.log('🎧 AudioManager: Stopping all playback');
        this.players.forEach((player) => {
            this.stop(player.id);
        });
        this.playQueue = [];
        this.currentlyPlaying = null;
    }

    /**
     * Get debug info about manager state
     */
    getDebugInfo() {
        return {
            registeredPlayers: Array.from(this.players.keys()),
            currentlyPlaying: this.currentlyPlaying,
            queueLength: this.playQueue.length,
            queue: [...this.playQueue],
            isProcessingQueue: this.isProcessingQueue
        };
    }
}

// Create singleton instance
const audioManager = new AudioManager();
export default audioManager;
