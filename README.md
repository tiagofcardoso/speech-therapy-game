# Speech Therapy Game

This project is an interactive speech therapy game designed to assist children in improving their speech pronunciation through engaging gameplay. The game utilizes artificial intelligence to provide feedback and adapt the difficulty level based on the user's progress.

## Project Structure

The project is divided into two main parts: the backend and the frontend.

### Backend

The backend is built using Python and includes the following components:

- **app.py**: The main entry point for the backend application, initializing the web server and setting up routes.
- **ai/tutor.py**: Contains the `Tutor` class for providing feedback and guidance during therapy sessions.
- **ai/game_generator.py**: Exports the `GameGenerator` class that creates game instances with varying difficulty levels.
- **models/**: Contains the data models for users and games.
  - **user.py**: Defines the `User` class for user management.
  - **game.py**: Defines the `Game` class for game management.
- **speech/**: Contains functions for speech recognition and synthesis.
  - **recognition.py**: Functions for processing and evaluating user speech input.
  - **synthesis.py**: Functions for generating spoken prompts.
- **database/db_connector.py**: Handles database connections and queries.
- **requirements.txt**: Lists the dependencies required for the backend.
- **tests/test_speech.py**: Contains unit tests for speech functionalities.

### Frontend

The frontend is built using React and includes the following components:

- **public/index.html**: The main HTML file for the web application.
- **src/components/**: Contains reusable components for the application.
  - **GameArea.js**: Manages the game interface and user interactions.
  - **ProgressTracker.js**: Displays the user's progress through the game levels.
  - **SpeechControls.js**: Provides controls for speech recognition.
- **src/pages/**: Contains the main pages of the application.
  - **Dashboard.js**: The main navigation page.
  - **GameScreen.js**: Displays the active game.
  - **Reports.js**: Shows performance and progress reports.
- **src/assets/styles/main.css**: Contains the main styles for the frontend.
- **src/App.js**: The main application component that sets up routing.
- **src/index.js**: The entry point for the React application.
- **package.json**: Configuration file for npm, listing dependencies and scripts.

## Setup Instructions

1. **Clone the repository**:
   ```
   git clone https://github.com/yourusername/speech-therapy-game.git
   cd speech-therapy-game
   ```

2. **Backend Setup**:
   - Navigate to the `backend` directory.
   - Install the required dependencies:
     ```
     pip install -r requirements.txt
     ```
   - Run the backend server:
     ```
     python app.py
     ```

3. **Frontend Setup**:
   - Navigate to the `frontend` directory.
   - Install the required dependencies:
     ```
     npm install
     ```
   - Start the frontend application:
     ```
     npm start
     ```

## Usage

Once both the backend and frontend are running, you can access the application in your web browser at `http://localhost:3000`. The game will guide users through various levels of speech therapy exercises, adapting to their progress and providing feedback.

## Contributing

Contributions are welcome! Please open an issue or submit a pull request for any enhancements or bug fixes.

## License

This project is licensed under the MIT License. See the LICENSE file for more details.# Speech-therapy-app
# speech-therapy-game
