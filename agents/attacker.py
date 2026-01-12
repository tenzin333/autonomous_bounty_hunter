from openai import OpenAI
from core.config import Config

client = OpenAI(api_key=Config.OPENAI_API_KEY)

class AttackerAgent:
    @staticmethod
    def get_code_context(file_path, line_number, window=15):
        """Reads specific lines around the vulnerability to save tokens."""
        try:
            with open(file_path, 'r') as f:
                lines = f.readlines()
                start = max(0, line_number - window)
                end = min(len(lines), line_number + window)
                
                # Add line numbers for the AI to reference accurately
                context = "".join([f"{i+1}: {lines[i]}" for i in range(start, end)])
                return context
        except Exception as e:
            return f"Error reading file: {e}"

    @staticmethod
    def validate(finding):
        """Asks the Triage LLM if the finding is a true positive."""
        file_path = finding['path']
        line_no = finding['start']['line']
        code_snippet = AttackerAgent.get_code_context(file_path, line_no)
        
        prompt = f"""
        Analyze this code for a suspected {finding['extra']['message']}.
        
        CODE CONTEXT:
        {code_snippet}
        
        Is this a real, exploitable vulnerability? 
        Respond in JSON: {{"is_valid": bool, "reason": "string"}}
        """
        
        response = client.chat.completions.create(
            model=Config.TRIAGE_MODEL,
            messages=[{"role": "user", "content": prompt}],
            response_format={ "type": "json_object" }
        )
        return response.choices[0].message.content