# Speech Therapy Game

An interactive application for speech therapy, developed to help children and adults improve their pronunciation skills through engaging games and exercises.

## Main Features

- **Interactive Speech Therapy Games**: Customized exercises for different sounds and difficulty levels
- **Speech Recognition**: Real-time pronunciation assessment with personalized feedback
- **Visual Feedback**: Audio visualization to show when the user is speaking
- **Adaptation for European Portuguese**: Interface and content adapted for users in Portugal
- **Progression System**: Tracking progress and adapting difficulty to the user's level
- **Tutor Voice**: Spoken instructions and feedback using natural-sounding text-to-speech


## MCP (Model Context Protocol) Agentic Architecture

This project implements an advanced MCP Agentic architecture that coordinates multiple specialized AI agents working together to deliver personalized speech therapy exercises.

### Key Components

#### 1. Model Integration
- Seamless integration with OpenAI and other LLM providers
- Models are abstracted behind agent interfaces for flexibility
- Support for various model types based on specific agent needs

#### 2. Context Management
- `ModelContext` provides structured state sharing between agents
- Persistent storage of results, user data, and session information
- Context-aware agents that build upon each other's outputs

#### 3. Protocol-Based Communication
- Standardized `Message` objects define inter-agent communication
- `Tool` definitions create contracts for agent capabilities
- MCPServer manages message routing and response handling

#### 4. Specialized Agents

- **GameDesignerAgent**: Creates customized games and exercises based on user needs
- **SpeechEvaluatorAgent**: Analyzes pronunciation accuracy using AI models
- **TutorAgent**: Provides pedagogical feedback with voice synthesis capabilities
- **ProgressionManagerAgent**: Adapts difficulty based on user performance
- **SearchAgent**: Retrieves relevant exercises and educational resources

### Advanced Features

- **Telemetry and Monitoring**: Comprehensive tracking of agent performance
- **Resilience Mechanisms**: Automatic retries with exponential backoff
- **Context-Aware Execution**: Methods that automatically integrate with shared context
- **Async-First Design**: Non-blocking operations for better performance

### Architecture Diagram

```
┌────────────┐         ┌────────────┐         ┌────────────┐
│   Client   │         │  API Layer │         │ MCP System │
│            │ ──────► │            │ ──────► │            │
└────────────┘         └────────────┘         └────────────┘
                                                    │
                                                    ▼
┌──────────────────────────────────────────────────────────────────────────┐
│                             ModelContext                                  │
└──────────────────────────────────────────────────────────────────────────┘
       ▲                 ▲                  ▲                  ▲
       │                 │                  │                  │
       ▼                 ▼                  ▼                  ▼
┌────────────┐   ┌────────────┐    ┌────────────┐    ┌────────────┐
│    Game    │   │   Speech   │    │    Tutor   │    │   Search   │
│  Designer  │   │ Evaluator  │    │    Agent   │    │    Agent   │
└────────────┘   └────────────┘    └────────────┘    └────────────┘
```

## Usage Example

```python
# Initialize the MCP system
mcp = MCPSystem(api_key="your-openai-key", db_connector=db)
await mcp.initialize_agents()

# Create a session using the MCP workflow
session = await mcp.create_interactive_session(user_id="user123")

# Process user input through multiple coordinated agents
result = await mcp.process_user_response(
    user_id="user123",
    response="User's spoken text",
    expected_text="Target pronunciation",
    session_id=session["session_id"]
)

# Access the combined results from multiple agents
print(f"Evaluation score: {result['evaluation']['score']}")
print(f"Feedback: {result['feedback']['text']}")
print(f"Next exercise: {result['next_exercise']['text']}")
```

### Benefits

This architecture provides significant advantages:
- **Scalability**: Agents operate independently and can scale separately
- **Flexibility**: New capabilities can be added without changing existing agents
- **Adaptability**: System dynamically adjusts to user needs and preferences
- **Observability**: Comprehensive telemetry across all operations
- **Resilience**: Built-in error handling and graceful degradation

This modular approach allows dynamic generation of educational content perfectly adapted to each user's specific needs while maintaining system reliability and performance.


## Technologies Used

- **Frontend**: React, JavaScript, CSS
- **Backend**: Python, Flask
- **Database**: MongoDB
- **AI**: OpenAI API (GPT-4, GPT-4o-mini)
- **Speech Processing**: Speech-to-Text, Text-to-Speech (Microsoft Azure, Amazon Polly or Google TTS)

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
   ```

2. Create and activate virtual environment:  
   ```bash
   python -m venv venv
   source venv/bin/activate  # Linux/Mac
   venv\Scripts\activate  # Windows
   ```

3. Install dependencies: 
   ```bash
   pip install -r requirements.txt
   ```

4. Install additional dependencies for audio processing:
   ```bash
   pip install SpeechRecognition pydub rapidfuzz
   ```

5. Set up environment variables:
   ```bash
   cp .env.example .env 
   # Edit .env with your settings
   ```

### Start application

1. Start the server BACKEND:
   ```bash
   python app.py
   ```

2. Start app FRONTEND:
   ```bash
   npm start
   ```