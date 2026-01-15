from core.llm_provider import llm_client
from core.config import Config
import asyncio
import json
import re


class AttackerAgent:
    @staticmethod
    def get_code_context(file_path, line_number, window=25):
        """Reads lines around a target location."""
        try:
            with open(file_path, 'r') as f:
                lines = f.readlines()

            idx = max(line_number - 1, 0)
            start = max(idx - window, 0)
            end = min(idx + window, len(lines))

            # No line numbers displayed — cleaner for LLMs
            return "".join(lines[start:end])

        except Exception as e:
            return f"Error reading file: {e}"

    @staticmethod
    async def validate(finding, context, file_path, line_number):
        """
        Analyze Semgrep finding and confirm exploitability.
        """

        system_prompt = (
            "You are a static analysis triage engine. Output ONLY valid JSON.\n"
            "RULES:\n"
            "- Base your decision ONLY on the provided code.\n"
            "- No assumptions about external input or program behavior.\n"
            "- Mark valid only if the exact code pattern is present.\n"
            "- Do not hallucinate or infer missing context.\n"
            "- If unsure, return valid:false.\n"
        )

        user_prompt = json.dumps({
            "file": file_path,
            "line": line_number,
            "finding": finding.get("extra", {}).get("message"),
            "code_context": context
        })

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
                raw = re.sub(r"```.*?```", "", raw, flags=re.DOTALL).strip()

                return json.loads(raw)

            except Exception as e:
                if "429" in str(e):
                    wait = (attempt + 1) * 3
                    print(f"Triage rate-limited, retrying in {wait}s...")
                    await asyncio.sleep(wait)
                    continue

                print("Validator error:", e)
                return {"valid": False, "explanation": str(e), "severity": "UNKNOWN"}

        return {"valid": False, "explanation": "Timeout", "severity": "UNKNOWN"}
