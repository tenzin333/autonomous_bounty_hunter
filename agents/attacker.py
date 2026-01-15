import os
import asyncio
import json
import re
from core.llm_provider import llm_client
from core.config import Config

class AttackerAgent:
    @staticmethod
    def get_code_context(file_path, line_number, window=25):
        """Reads lines around a target location for LLM analysis."""
        try:
            if not os.path.exists(file_path):
                return "File not found."
                
            with open(file_path, 'r') as f:
                lines = f.readlines()

            # Ensure we are within range
            idx = max(line_number - 1, 0)
            start = max(idx - window, 0)
            end = min(idx + window, len(lines))

            # Returning raw text without line numbers is often better for LLM tokenization
            return "".join(lines[start:end])

        except Exception as e:
            return f"Error reading file: {e}"

    @staticmethod
    async def validate(finding, context, file_path, line_number):
        """
        Analyze Semgrep finding and confirm if it fits a fixable pattern.
        """

        system_prompt = (
            "You are a security triage engine. You must output ONLY valid JSON.\n\n"
            "GOAL: Confirm if the provided code contains a real security vulnerability.\n"
            "DETERMINISTIC RULES:\n"
            "1. Valid ONLY if the code explicitly shows user-controlled data reaching a dangerous sink (e.g., RegExp, console.log).\n"
            "2. If the data is a hardcoded string literal, mark valid:false.\n"
            "3. If the context is missing the variable definition, but it looks like a standard request parameter (req.query, req.body), mark valid:true.\n"
            "4. Return valid:false if the finding is a false positive or if you are unsure.\n"
        )

        # Structure the query clearly
        query = {
            "vulnerability_type": finding.get("check_id"),
            "location": f"{file_path}:{line_number}",
            "reported_issue": finding.get("extra", {}).get("message"),
            "code_snippet": context
        }

        user_prompt = json.dumps(query)

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

                raw = response.choices[0].message.content.strip()
                
                # Sanitize response in case the model ignored response_format
                if "```json" in raw:
                    raw = raw.split("```json")[1].split("```")[0].strip()
                elif "```" in raw:
                    raw = raw.split("```")[1].split("```")[0].strip()

                data = json.loads(raw)
                
                # Ensure keys exist to prevent downstream KeyErrors
                return {
                    "valid": data.get("valid", False),
                    "explanation": data.get("explanation", "No explanation provided."),
                    "severity": data.get("severity", "UNKNOWN")
                }

            except Exception as e:
                if "429" in str(e):
                    wait = (attempt + 1) * 5
                    print(f"Triage rate-limited. Retrying in {wait}s...")
                    await asyncio.sleep(wait)
                    continue

                print(f"Triage error on {file_path}:{line_number}: {e}")
                return {"valid": False, "explanation": str(e), "severity": "UNKNOWN"}

        return {"valid": False, "explanation": "Max retries exceeded", "severity": "UNKNOWN"}