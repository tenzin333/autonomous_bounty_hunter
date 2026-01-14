from core.llm_provider import llm_client
from core.config import Config
import asyncio
import json

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
    async def validate(finding, code_snippet, file_path, line_number):
        """
        Analyzes a finding for exploitability.
        Returns a dictionary with valid, explanation, and severity.
        """
        
        system_prompt = (
            "You are a Security Research API. You ONLY output JSON.\n"
            "Your task is to analyze Semgrep findings for exploitability based SOLELY on the provided Code Context.\n\n"
            "STRICT RULES:\n"
            "1. Base your answer ONLY on the provided Code Context. If the pattern is not visible, return valid: false or inconclusive.\n"
            "2. Do NOT assume functionality or variables not explicitly shown.\n"
            "3. Do NOT infer user-controlled input unless explicitly shown.\n"
            "4. Do NOT hallucinate vulnerabilities.\n"
            "5. Mark as valid ONLY if the exact vulnerable pattern is present.\n\n"
            "OUTPUT RULES:\n"
            "6. Output a JSON object with keys: valid, explanation, severity.\n"
            "7. 'valid' must be true, false, or 'inconclusive'.\n"
            "8. 'severity' must be LOW, MEDIUM, HIGH, CRITICAL, or UNKNOWN.\n"
            "9. The explanation must be 1-3 sentences referencing ONLY the provided context.\n"
            "10. Output pure JSON with NO markdown or commentary."
        )

        user_prompt = f"""
        [TARGET DATA]
        File: {file_path}
        Line: {line_number}
        Finding: {finding['extra']['message']}

        [CODE CONTEXT]
        {code_snippet}

        [INSTRUCTION]
        Analyze if the Code Context contains the vulnerability described.
        Return a JSON object with 'valid', 'explanation', and 'severity'.
        """

        for attempt in range(3):
            try:
                response = await llm_client.chat.completions.create(
                    model=Config.TRIAGE_MODEL,
                    messages=[
                        {"role": "system", "content": system_prompt},
                        {"role": "user", "content": user_prompt}
                    ],
                    response_format={"type": "json_object"}
                )

                raw_content = response.choices[0].message.content
                clean_content = raw_content.strip()
                
                # Cleanup potential markdown wrapper if response_format was ignored
                if clean_content.startswith("```"):
                    clean_content = clean_content.split("```")[1]
                    if clean_content.startswith("json"):
                        clean_content = clean_content[4:].strip()

                return json.loads(clean_content)

            except Exception as e:
                if "429" in str(e):
                    wait_time = (attempt + 1) * 5
                    print(f"Rate limited. Retrying in {wait_time}s...")
                    await asyncio.sleep(wait_time)
                    continue
                
                print(f"LLM Error: {e}")
                return {"valid": False, "explanation": f"API Error: {str(e)}", "severity": "UNKNOWN"}

        return {"valid": False, "explanation": "Failed after 3 attempts.", "severity": "UNKNOWN"}
