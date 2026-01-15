import asyncio
from core.llm_provider import llm_client
from core.config import Config

class PatcherAgent:
    @staticmethod
    async def generate_fix(file_content, work_notes):
        """
        Uses LLM to intelligently patch vulnerabilities.
        """

        system_prompt = (
                    "You are a Senior Security Engineer. Patch the provided code.\n"
                        "CRITICAL INSTRUCTIONS:\n"
                            "1. You MUST define 'const escapeRegExp = (s) => s.replace(/[.*+?^${}()|[\\\\\\]]/g, '\\\\$&');' at the top of the file.\n"
                                "2. You MUST locate every variable mentioned in the Triage Notes and wrap it in the escapeRegExp() function.\n"
                                    "3. Example: change '{ $regex: name }' to '{ $regex: escapeRegExp(name) }'.\n"
                                        "4. Do not omit any part of the original file. Return the FULL source code only."
                                        )

        user_prompt = f"TRIAGE NOTES:\n{work_notes}\n\nSOURCE CODE:\n{file_content}"

        try:
            response = await llm_client.chat.completions.create(
                model=Config.PATCHER_MODEL,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt}
                ],
                temperature=0 
            )
            
            return response.choices[0].message.content.strip()

        except Exception as e:
            print(f"LLM Patching Error: {e}")
            return file_content
