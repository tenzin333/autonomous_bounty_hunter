from core.llm_provider import llm_client
from core.config import Config


class AttackerAgent:
    @staticmethod
    def get_code_context(file_path, line_number, window=15):
        """Reads specific lines around the vulnerability to save tokens."""
        try:
            with open(file_path, 'r') as f:
                lines = f.readlines()
                # Line numbers in Semgrep are 1-indexed
                idx = line_number - 1
                start = max(0, idx - window)
                end = min(len(lines), idx + window)
                
                context = "".join([f"{i+1}: {lines[i]}" for i in range(start, end)])
                return context
        except Exception as e:
            return f"Error reading file: {e}"

    @staticmethod
    async def validate(finding, code_snippet):
        """
        Generic validation call. 
        Works with any OpenAI-compatible API (Ollama, LocalAI, vLLM, OpenAI).
        """
        prompt = f"Analyze for {finding['extra']['message']}: {code_snippet}"
        
        try:
            response = await llm_client.chat.completions.create(
                model=Config.TRIAGE_MODEL,
                messages=[{"role": "user", "content": prompt}],
                # We use a standard JSON prompt to ensure generic compatibility
                response_format={ "type": "json_object" } 
            )
            return response.choices[0].message.content
        except Exception as e:
            return f"{{\"is_valid\": false, \"reason\": \"Error: {str(e)}\"}}"
