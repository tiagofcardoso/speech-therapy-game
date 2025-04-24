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

The MCP (Model Context Protocol) architecture coordinates multiple specialized AI agents to provide a personalized speech therapy experience. Below are examples of how to implement and use this system in different scenarios:

### Basic Setup and Configuration

```python
# Required imports
from ai.server.mcp_coordinator import MCPSystem
from ai.server.mcp_server import Message, ModelContext
from database.db_connector import DatabaseConnector

# Configure database connection
db = DatabaseConnector()

# Initialize the MCP system
mcp = MCPSystem(api_key="your-openai-key", db_connector=db)

# Initialize all agents asynchronously
await mcp.initialize_agents()
```

### Creating a New Game Session

```python
# Create context for a new session
user_id = "user123"  # User ID in the system
context = ModelContext()  # Shared context between agents

# Create an interactive session for the user
session = await mcp.create_interactive_session(user_id=user_id)

# Information about the created session
session_id = session["session_id"]
print(f"New session created: {session_id}")
print(f"Determined difficulty: {session['difficulty']}")
print(f"Game type: {session['game_data']['game_type']}")
```

### Agent Communication with Messages

```python
# Create a message for the Game Designer Agent
game_message = Message(
    from_agent="api",             # Source agent
    to_agent="game_designer",     # Destination agent
    tool="create_game",           # Tool to be used
    params={                      # Parameters for the tool
        "user_id": user_id,
        "difficulty": "beginner",
        "game_type": "pronunciation exercises"
    }
)

# Process the message and get the result
game_data = await mcp.server.process_message(game_message, context)

# Data from the created game
print(f"Game created: {game_data['title']}")
print(f"Exercises: {len(game_data['exercises'])}")
```

### MCP Coordinator Orchestrating Multiple Agents

```python
# Example of the MCP Coordinator orchestrating multiple agents
async def orchestrate_agents_workflow(user_prompt, user_id):
    # Create a shared context for this workflow
    context = ModelContext()
    context.set("user_id", user_id)
    context.set("user_prompt", user_prompt)
    
    # 1. First, get difficulty recommendation from Progression Manager
    difficulty_msg = Message(
        from_agent="coordinator",
        to_agent="progression_manager", 
        tool="determine_difficulty",
        params={"user_id": user_id}
    )
    difficulty = await mcp.server.process_message(difficulty_msg, context)
    context.set("difficulty", difficulty)
    
    # 2. Then have Game Designer create appropriate content
    game_msg = Message(
        from_agent="coordinator",
        to_agent="game_designer",
        tool="create_game",
        params={
            "user_id": user_id,
            "difficulty": difficulty,
            "game_type": "pronunciation exercises"
        }
    )
    game_data = await mcp.server.process_message(game_msg, context)
    context.set("game_data", game_data)
    
    # 3. Have Tutor prepare instructions and guidance
    tutor_msg = Message(
        from_agent="coordinator",
        to_agent="tutor",
        tool="create_instructions",
        params={
            "game_data": game_data,
            "difficulty": difficulty,
            "user_id": user_id
        }
    )
    instructions = await mcp.server.process_message(tutor_msg, context)
    
    # 4. Return the complete package with contributions from all agents
    return {
        "game": game_data,
        "instructions": instructions,
        "difficulty": difficulty,
        "session_id": str(uuid.uuid4())
    }
```

### Pronunciation Evaluation

```python
# Evaluate user pronunciation
evaluation_result = await mcp.evaluate_pronunciation(
    audio_file=open("audio_sample.webm", "rb"),  # Audio file
    expected_word="casa",                        # Expected word
    user_id=user_id,                             # User ID
    session_id=session_id                        # Session ID
)

# Process evaluation results
is_correct = evaluation_result["isCorrect"]
score = evaluation_result["score"]
feedback = evaluation_result["feedback"]

print(f"Pronunciation correct: {is_correct}")
print(f"Score: {score}/10")
print(f"Feedback: {feedback}")
```

### Complete Exercise Flow

```python
# Example of a complete flow from game generation to evaluation

async def complete_exercise_workflow(user_id):
    # 1. Create session and get game
    session = await mcp.create_interactive_session(user_id=user_id)
    session_id = session["session_id"]
    
    # 2. Get the current exercise
    current_exercise = session["game_data"]["exercises"][0]
    word_to_pronounce = current_exercise["word"]
    
    # 3. Synthesize audio for the user to hear
    from speech.synthesis import synthesize_speech
    audio_data = synthesize_speech(
        text=word_to_pronounce,
        voice_settings={"language_code": "pt-PT"}
    )
    
    # 4. Simulation of user audio recording
    # (In the real application, audio would come from the frontend)
    user_audio = get_user_audio_recording()
    
    # 5. Evaluate pronunciation
    result = await mcp.evaluate_pronunciation(
        audio_file=user_audio,
        expected_word=word_to_pronounce,
        user_id=user_id,
        session_id=session_id
    )
    
    # 6. Update progress and provide feedback
    if result["isCorrect"]:
        await mcp.server.process_message(
            Message(
                from_agent="api",
                to_agent="tutor",
                tool="generate_positive_feedback",
                params={"result": result, "user_id": user_id}
            ),
            ModelContext()
        )
    
    return result
```

### Implementation Tips

- **Shared Context**: Use `ModelContext` to share data between different agents.
- **Asynchronous Handling**: Leverage `async/await` methods for non-blocking operations.
- **Error Handling**: Add exception handling to deal with service failures.
- **Extensibility**: Create new agents by implementing the `BaseAgent` interface.

For more examples and advanced use cases, see the test files in the `tests/` folder.

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