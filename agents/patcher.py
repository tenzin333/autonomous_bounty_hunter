from core.llm_provider import llm_client
from core.config import Config


class PatcherAgent:
    @staticmethod
    def generate_fix(file_content, vulnerability_desc):
        """Generates a patched version of the file."""
        
        prompt = f"""
        You are a Senior Security Engineer. 
        VULNERABILITY: {vulnerability_desc}
        
        ORIGINAL FILE CONTENT:
        ---
        {file_content}
        ---
        
        TASK:
        1. Fix the vulnerability.
        2. Keep the exact same coding style, indentation, and variable naming.
        3. Only return the FULL updated file content. No conversation.
        """
        
        response = llm_client.chat.completions.create(
            model=Config.PATCHER_MODEL,
            messages=[
                {"role": "system", "content": "You only output code, no prose."},
                {"role": "user", "content": prompt}
            ],
            temperature=0.2 # Lower temperature for stable code generation
        )
        
        return response.choices[0].message.content