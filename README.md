# Speech Therapy Game

An interactive application for speech therapy, developed to help children and adults improve their pronunciation skills through engaging games and exercises.

## Main Features

- **Interactive Speech Therapy Games**: Customized exercises for different sounds and difficulty levels
- **Speech Recognition**: Real-time pronunciation assessment with personalized feedback
- **Visual Feedback**: Audio visualization to show when the user is speaking
- **Adaptation for European Portuguese**: Interface and content adapted for users in Portugal
- **Progression System**: Tracking progress and adapting difficulty to the user's level

## MCP (Model Context Protocol) Agent Architecture

The project uses an advanced MCP architecture with various specialized agents working together:

- **MCPCoordinator**: Orchestrates communication between agents and manages game sessions
- **GameDesignerAgent**: Responsible for creating customized games and exercises
- **SpeechEvaluatorAgent**: Evaluates the user's pronunciation using AI models
- **TutorAgent**: Provides pedagogical feedback and personalized instructions
- **ProgressionManagerAgent**: Monitors user progress and adjusts difficulty

This modular architecture allows dynamic generation of educational content adapted to the specific needs of each user.

## Technologies Used

- **Frontend**: React, JavaScript, CSS
- **Backend**: Python, Flask
- **Database**: MongoDB
- **AI**: OpenAI API (GPT-4, GPT-4o-mini)
- **Speech Processing**: Speech-to-Text, Text-to-Speech

## Implementation Details

### 1. Speech Recognition and Evaluation

We implemented a comprehensive speech recognition and evaluation system:

1. **Audio Recording**:
   - Used MediaRecorder API for capturing audio input
   - Implemented WebAudio API for real-time volume analysis
   - Added visual feedback during recording

2. **Audio Processing**:
   - Convert WebM audio to WAV format using FFmpeg
   - Handle audio format compatibility issues
   - Implemented error handling for audio processing failures

3. **Speech-to-Text**:
   - Integration with speech recognition API
   - Fallback mechanisms when recognition fails
   - Error logging and debugging information

4. **Pronunciation Evaluation**:
   - AI-based evaluation using OpenAI models
   - Scoring system based on pronunciation accuracy
   - Detailed feedback on specific sounds that need improvement

### 2. European Portuguese Adaptation

We fully adapted the application for European Portuguese:

1. **System Prompts**:
   - Translated all AI agent prompts to European Portuguese
   - Adapted language style to match Portuguese from Portugal
   - Updated language-specific instructions

2. **Interface Language**:
   - Changed verb forms from third person to second person (tu vs. você)
   - Updated expressions and vocabulary to match European Portuguese
   - Ensured consistency across the entire application

3. **Feedback Messages**:
   - Replaced Brazilian Portuguese expressions with European equivalents
   - Adjusted tone and formality level
   - Updated all encouragement and instruction messages

### 3. Visual Feedback System

We implemented a comprehensive visual feedback system to enhance user experience:

1. **Audio Level Visualization**:
   - Added real-time audio level indicators
   - Created animated bars that respond to user's voice
   - Implemented threshold detection for speaking/not speaking states

2. **Recording Button Enhancements**:
   - Added microphone icon to recording button
   - Implemented vibration effect when speaking is detected
   - Color changes to indicate recording state (purple/red)

3. **Feedback Indicators**:
   - Clear visual distinction between correct and incorrect responses
   - Progress tracking visualization
   - Score display and celebration animations

### 4. Error Handling and Performance Improvements

We significantly improved the robustness of the application:

1. **Audio Format Compatibility**:
   - Addressed WebM to WAV conversion issues
   - Implemented format detection and fallback options
   - Added proper cleanup of temporary files

2. **Network Error Handling**:
   - Implemented token refresh mechanism
   - Added retry logic for failed API calls
   - Improved error messages for users

3. **Fallback Mechanisms**:
   - Text similarity comparison when speech recognition fails
   - Default responses when AI services are unavailable
   - Graceful degradation when features aren't available

4. **Performance Optimization**:
   - Reduced unnecessary re-renders
   - Optimized audio processing
   - Improved resource cleanup

### 5. AI Integration Improvements

We enhanced the AI integration for better speech evaluation:

1. **SpeechEvaluatorAgent**:
   - Fixed type import issues
   - Improved prompt design for better evaluation
   - Enhanced error handling and fallback responses

2. **GameDesignerAgent**:
   - Improved exercise generation
   - Added support for different difficulty levels
   - Enhanced exercise format for pronunciation practice

3. **TutorAgent**:
   - Improved feedback generation
   - Added more encouraging and specific feedback
   - Supported multiple languages and accents

4. **ProgressionManagerAgent**:
   - Added user history tracking
   - Implemented adaptive difficulty adjustment
   - Enhanced scoring and progression metrics

## Installation

### Prerequisites

- Node.js (v14 or higher)
- Python (v3.9 or higher)
- MongoDB
- FFmpeg (for audio processing)

### Backend

1. Clone the repository:
   ```bash
   git clone https://github.com/your-username/speech-therapy-game.git
   cd speech-therapy-game/backend

2. Create and activate virtual environment:  
  python -m venv venv
  source venv/bin/activate  # Linux/Mac
  venv\Scripts\activate  # Windows

3. Install dependencies: 
  pip install -r requirements.txt

4. Install additional dependencies for audio processing:
  pip install SpeechRecognition pydub rapidfuzz

5. cp .env.example .env 
# Edit .env with your settings

### Start application

1. Start the server BACKEND:
    python app.py

2. Start app FRONTEND:
    npm start