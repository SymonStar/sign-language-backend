import os
from groq import Groq

class Translator:
    def __init__(self):
        api_key = os.getenv('GROQ_API_KEY', '')
        if api_key:
            self.client = Groq(api_key=api_key)
            self.use_ai = True
        else:
            self.client = None
            self.use_ai = False
            print("⚠️  No GROQ_API_KEY found. Using simple translation.")
    
    def translate_to_english(self, words):
        """Translate ASL word sequence to proper English"""
        if not words:
            return "No signs detected"
        
        # If no AI, just join words
        if not self.use_ai:
            return self.simple_translate(words)
        
        # Use Groq AI for proper translation
        try:
            gloss = ' '.join(words)
            
            response = self.client.chat.completions.create(
                model="llama-3.3-70b-versatile",
                messages=[
                    {
                        "role": "system",
                        "content": "You are translating American Sign Language (ASL) glosses into natural English. ASL has different grammar than English. Convert the sign sequence into a proper English sentence. Keep it concise."
                    },
                    {
                        "role": "user",
                        "content": f"Translate this ASL gloss to English: {gloss}"
                    }
                ],
                temperature=0.3,
                max_tokens=100
            )
            
            return response.choices[0].message.content.strip()
        
        except Exception as e:
            print(f"AI translation error: {e}")
            return self.simple_translate(words)
    
    def simple_translate(self, words):
        """Simple translation without AI"""
        # Basic grammar rules for common patterns
        sentence = ' '.join(words).lower()
        
        # Capitalize first letter
        if sentence:
            sentence = sentence[0].upper() + sentence[1:]
        
        # Add period
        if sentence and not sentence.endswith('.'):
            sentence += '.'
        
        return sentence
