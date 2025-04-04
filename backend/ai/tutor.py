from openai import OpenAI
import os

class Tutor:
    def __init__(self):
        # Initialize the OpenAI client for tutoring
        self.client = OpenAI(api_key=os.environ.get("OPENAI_API_KEY"))
        self.user_sessions = {}
    
    def provide_feedback(self, user_id, response):
        # Get user's current game state
        if user_id not in self.user_sessions:
            return {"error": "User session not found"}
        
        # Compare the response with the expected pronunciation
        expected = self.user_sessions[user_id]["expected_word"]
        
        # Use OpenAI to evaluate pronunciation quality
        evaluation = self._evaluate_pronunciation(response, expected)
        
        # Generate personalized feedback
        feedback = self._generate_feedback(evaluation, expected)
        
        # Update user progress
        self._update_user_progress(user_id, evaluation)
        
        return feedback
    
    def _evaluate_pronunciation(self, actual, expected):
        # Use OpenAI to evaluate how close the pronunciation is
        try:
            response = self.client.chat.completions.create(
                model="gpt-4",
                messages=[
                    {"role": "system", "content": "You are a speech therapy assistant. Evaluate how well the child's pronunciation matches the expected word."},
                    {"role": "user", "content": f"Expected word: '{expected}'. Child said: '{actual}'. Rate the pronunciation accuracy on a scale of 1-10 and explain why."}
                ]
            )
            return response.choices[0].message.content
        except Exception as e:
            print(f"Error evaluating pronunciation: {e}")
            return {"score": 5, "explanation": "Could not evaluate pronunciation."}
    
    def _generate_feedback(self, evaluation, expected):
        # Generate encouragement and tips based on evaluation
        try:
            response = self.client.chat.completions.create(
                model="gpt-4",
                messages=[
                    {"role": "system", "content": "You are a friendly speech therapist for children. Provide encouraging feedback."},
                    {"role": "user", "content": f"Give encouraging feedback for a child who attempted to say '{expected}'. Evaluation: {evaluation}"}
                ]
            )
            return response.choices[0].message.content
        except Exception as e:
            print(f"Error generating feedback: {e}")
            return {"message": "Great try! Let's practice again."}
    
    def _update_user_progress(self, user_id, evaluation):
        # Update the user's progress based on evaluation
        # This would involve more complex logic in a real application
        pass