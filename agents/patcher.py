from core.llm_provider import llm_client
from core.config import Config
import asyncio
import re


class PatcherAgent:
    @staticmethod
    async def generate_fix(file_content, work_notes):
        """
        Generate a patched version of the full file.
        """
        system_prompt = (
            "You are a senior security refactoring engine. Output RAW source code ONLY.\n"
            "MANDATORY RULES:\n"
            "1. Insert helper if missing:\n"
            "   const escapeRegExp = (s) => s.replace(/[.*+?^${}()|[\\\\\\]]/g, '\\\\$&');\n"
            "2. Wrap dynamic RegExp terms:\n"
            "   new RegExp(foo) -> new RegExp(escapeRegExp(foo))\n"
            "3. DO NOT remove logic.\n"
            "4. FAIL if wrapping is incomplete.\n"
        )

        user_prompt = f"""
Fix these issues:
{work_notes}

FULL FILE:
<<<{file_content}>>>
        """

        for attempt in range(3):
            try:
                response = await llm_client.chat.completions.create(
                    model=Config.PATCHER_MODEL,
                    messages=[
                        {"role": "system", "content": system_prompt},
                        {"role": "user", "content": user_prompt}
                    ],
                    temperature=0.15
                )
                patch = response.choices[0].message.content.strip()

                # Remove accidental fences
                patch = re.sub(r"```.*?```", "", patch, flags=re.DOTALL).strip()

                # Validation: must include helper AND wrapping
                if "escapeRegExp" in patch and "new RegExp(" in patch and "escapeRegExp(" in patch:
                    return patch

                print("⚠️ Patch attempt incomplete, retrying...")

            except Exception as e:
                if "429" in str(e):
                    await asyncio.sleep((attempt + 1) * 5)
                    continue
                print("Patch LLM error:", e)
                return file_content

        return file_content
