/**
 * Indexy - The Friendly Spider Mascot
 * This script manages the interactive mascot character for the URL Indexing Checker application
 */

class IndexyMascot {
    constructor() {
        this.currentState = 'default';
        this.messageQueue = [];
        this.isMessageShowing = false;
        this.messageCategories = {
            'default': [
                "Hi there! I'm Indexy, your URL indexing assistant.",
                "Need help checking if your URLs are indexed? I'm here to help!",
                "Enter URLs to check their Google indexing status.",
                "Tip: You can upload a CSV file with lots of URLs to check in bulk.",
                "I crawl the web just like Google, but much friendlier!"
            ],
            'thinking': [
                "Hmm, let me think about that...",
                "Processing your request...",
                "Analyzing the situation...",
                "Connecting the web threads..."
            ],
            'working': [
                "Checking your URLs now...",
                "Crawling through the web for your results...",
                "I'm working on your request...",
                "Spinning up some results for you...",
                "Just a moment while I check the indexing status..."
            ],
            'happy': [
                "Great job! Your results are ready.",
                "Success! I've finished checking your URLs.",
                "All done! Take a look at your results.",
                "Mission accomplished! How else can I help?",
                "Your URL check is complete!"
            ],
            'tips': [
                "Tip: Keep your URLs organized for better tracking.",
                "Tip: Regular indexing checks help monitor your SEO progress.",
                "Tip: Check both new and old URLs to maintain visibility.",
                "Tip: Focus on improving content for non-indexed pages.",
                "Tip: Export your reports to track progress over time."
            ]
        };
    }

    /**
     * Initialize the mascot in the UI
     */
    initialize() {
        this.createMascotElements();
        this.detectPageAndSetBehavior();

        // Set up periodic random messages
        setInterval(() => {
            if (!this.isMessageShowing && Math.random() > 0.7) {
                this.showRandomMessage();
            }
        }, 30000); // Every 30 seconds with 30% chance
    }

    /**
     * Create the mascot elements in the DOM
     */
    createMascotElements() {
        const container = document.createElement('div');
        container.className = 'mascot-container';
        
        // Create the spider element
        const spider = document.createElement('div');
        spider.className = 'mascot-spider';
        
        // Create the legs
        const legs = document.createElement('div');
        legs.className = 'mascot-legs';
        
        for (let i = 1; i <= 8; i++) {
            const leg = document.createElement('div');
            leg.className = `mascot-leg mascot-leg-${i}`;
            legs.appendChild(leg);
        }
        
        // Create the body
        const body = document.createElement('div');
        body.className = 'mascot-body';
        
        // Create the eyes
        const eyes = document.createElement('div');
        eyes.className = 'mascot-eyes';
        
        // Left eye
        const leftEye = document.createElement('div');
        leftEye.className = 'mascot-eye';
        const leftPupil = document.createElement('div');
        leftPupil.className = 'mascot-pupil';
        leftEye.appendChild(leftPupil);
        
        // Right eye
        const rightEye = document.createElement('div');
        rightEye.className = 'mascot-eye';
        const rightPupil = document.createElement('div');
        rightPupil.className = 'mascot-pupil';
        rightEye.appendChild(rightPupil);
        
        eyes.appendChild(leftEye);
        eyes.appendChild(rightEye);
        body.appendChild(eyes);
        
        // Create speech bubble
        const speech = document.createElement('div');
        speech.className = 'mascot-speech';
        
        // Assemble the mascot
        spider.appendChild(legs);
        spider.appendChild(body);
        container.appendChild(spider);
        container.appendChild(speech);
        
        // Add to page
        document.body.appendChild(container);
        
        // Store references
        this.container = container;
        this.spider = spider;
        this.speech = speech;
        
        // Add click listener to show a message when clicked
        this.spider.addEventListener('click', () => {
            this.showRandomMessage();
        });
        
        // Track mouse movement to make eyes follow cursor
        document.addEventListener('mousemove', (e) => {
            const pupils = document.querySelectorAll('.mascot-pupil');
            const spiderRect = this.spider.getBoundingClientRect();
            const spiderCenterX = spiderRect.left + spiderRect.width / 2;
            const spiderCenterY = spiderRect.top + spiderRect.height / 2;
            
            const maxMove = 3;
            const angleX = (e.clientX - spiderCenterX) / window.innerWidth;
            const angleY = (e.clientY - spiderCenterY) / window.innerHeight;
            
            pupils.forEach(pupil => {
                pupil.style.transform = `translate(${angleX * maxMove}px, ${angleY * maxMove}px)`;
            });
        });
    }

    /**
     * Detect the current page and set appropriate behavior
     */
    detectPageAndSetBehavior() {
        // Check which page we're on based on URL
        const pathname = window.location.pathname;
        
        if (pathname === '/' || pathname === '/index') {
            // Home page
            this.addFormHelpers();
            this.setState('default');
            this.showMessage("Welcome! Enter URLs to check or upload a CSV file.", 5000);
        } else if (pathname.includes('/results')) {
            // Results page
            this.setState('happy');
            this.showMessage("Here are your results! Indexed URLs are shown in green.", 5000);
        } else if (pathname.includes('/processing')) {
            // Processing page
            this.setState('working');
            this.showMessage("I'm checking your URLs now. This might take a moment for large batches.", 5000);
            
            // Set up progress tracking animations
            const progressCheck = () => {
                const progressElement = document.getElementById('progress-bar');
                if (progressElement) {
                    const progress = parseInt(progressElement.style.width || '0');
                    if (progress < 30) {
                        this.showMessage("Starting to crawl through your URLs...", 3000);
                    } else if (progress < 70) {
                        this.showMessage("Making good progress! Keep waiting...", 3000);
                    } else if (progress < 100) {
                        this.showMessage("Almost done with your batch!", 3000);
                    } else {
                        this.setState('happy');
                        this.showMessage("All done! Your results will be displayed shortly.", 3000);
                    }
                }
            };
            
            setInterval(progressCheck, 5000);
        } else if (pathname.includes('/reports')) {
            // Reports page
            this.setState('happy');
            this.showMessage("Your reports are organized here. You can export them as CSV.", 5000);
        }
    }

    /**
     * Add helpful behavior for the input form
     */
    addFormHelpers() {
        // Find the URL input form
        const form = document.querySelector('form');
        const urlInput = document.querySelector('textarea[name="urls"]');
        const fileInput = document.querySelector('input[type="file"]');
        
        if (form && urlInput) {
            // Show tip when focusing on URL input
            urlInput.addEventListener('focus', () => {
                this.setState('thinking');
                this.showMessage("Enter one URL per line or paste a list of URLs.", 4000);
            });
            
            // Show encouragement when typing
            urlInput.addEventListener('input', () => {
                if (urlInput.value.length > 0 && urlInput.value.includes('\n')) {
                    this.showMessage("Multiple URLs detected! I'll check them all.", 3000);
                }
            });
            
            // React to form submission
            form.addEventListener('submit', () => {
                this.setState('working');
                this.showMessage("Starting the indexing check now. I'll crawl through your URLs!", 3000);
            });
        }
        
        if (fileInput) {
            // React to file selection
            fileInput.addEventListener('change', () => {
                if (fileInput.files.length > 0) {
                    this.setState('happy');
                    this.showMessage("File selected! Make sure it's a CSV with URLs.", 3000);
                }
            });
        }
    }

    /**
     * Change the mascot's state/appearance
     * @param {string} state - The state to change to ('default', 'happy', 'thinking', 'working')
     */
    setState(state) {
        // Remove previous state class
        this.spider.classList.remove(`mascot-state-${this.currentState}`);
        
        // Add new state class
        this.spider.classList.add(`mascot-state-${state}`);
        
        // Update current state
        this.currentState = state;
    }

    /**
     * Show a message in the mascot's speech bubble
     * @param {string} message - The message to display
     * @param {number} duration - How long to show the message (in ms)
     */
    showMessage(message, duration = 4000) {
        // If a message is already showing, queue this one
        if (this.isMessageShowing) {
            this.messageQueue.push({ message, duration });
            return;
        }
        
        this.isMessageShowing = true;
        this.speech.textContent = message;
        this.speech.classList.add('visible');
        
        setTimeout(() => {
            this.speech.classList.remove('visible');
            
            setTimeout(() => {
                this.isMessageShowing = false;
                
                // If there are queued messages, show the next one
                if (this.messageQueue.length > 0) {
                    const next = this.messageQueue.shift();
                    this.showMessage(next.message, next.duration);
                }
            }, 300); // Wait for fade out animation
        }, duration);
    }

    /**
     * Show a random message based on the current state
     */
    showRandomMessage() {
        // Decide which category to use - mostly use the current state's messages
        // but occasionally use tips or default messages
        let category = this.currentState;
        const rand = Math.random();
        
        if (rand > 0.7) {
            category = 'tips';
        } else if (rand > 0.5 && this.currentState !== 'default') {
            category = 'default';
        }
        
        const message = this.getRandomMessage(category);
        this.showMessage(message);
    }

    /**
     * Get a random message from the specified category
     * @param {string} category - The category of messages to choose from
     * @returns {string} A random message
     */
    getRandomMessage(category) {
        const messages = this.messageCategories[category];
        if (!messages || messages.length === 0) {
            return "Hello there!";
        }
        
        const randomIndex = Math.floor(Math.random() * messages.length);
        return messages[randomIndex];
    }
}

// Initialize the mascot when the DOM is fully loaded
document.addEventListener('DOMContentLoaded', () => {
    const indexy = new IndexyMascot();
    indexy.initialize();
    
    // Make it globally accessible for debugging
    window.indexy = indexy;
});