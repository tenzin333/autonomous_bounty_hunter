from core.llm_provider import llm_client
from core.config import Config
import asyncio
import re


class PatcherAgent:
    @staticmethod
    async def generate_fix(file_content, work_notes):
        """
        Generates a patched version of the full file content.

        Now supports:
        - new RegExp(user)
        - { $regex: user }
        - .match(user)
        - .search(user)

        And enforces adding escapeRegExp helper.
        """

        system_prompt = (
            "You are a Senior Security Engineer. Return RAW CODE ONLY.\n\n"
            "GOAL: Fix all ReDoS risks where user-controlled strings become regexes.\n"
            "Apply ALL rules below:\n\n"
            "RULES:\n"
            "1. Ensure this helper exists exactly once at the top-level:\n"
            "   const escapeRegExp = (s) => s.replace(/[.*+?^${}()|[\\\\\\]]/g, '\\\\$&');\n\n"
            "2. Fix EVERY occurrence of unescaped regex usage:\n"
            "   A) new RegExp(x) → new RegExp(escapeRegExp(x))\n"
            "   B) { $regex: x } → { $regex: new RegExp(escapeRegExp(x)) }\n"
            "   C) something.match(x) → something.match(new RegExp(escapeRegExp(x)))\n"
            "   D) something.search(x) → something.search(new RegExp(escapeRegExp(x)))\n\n"
            "3. Do NOT change program behavior or modify logic outside these patterns.\n"
            "4. Maintain original indentation, whitespace, and formatting.\n"
            "5. Wrap ALL matching cases — even if multiple per line.\n"
            "6. Output ONLY the full source code. No markdown. No explanations."
        )

        user_prompt = (
            f"Fix all ReDoS-prone regex usage in this file.\n"
            f"NOTES:\n{work_notes}\n\n"
            "FILE CONTENT START\n"
            f"{file_content}\n"
            "FILE CONTENT END"
        )

        # Try up to 3 times to get a patch with escapes applied
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

                # 1. Remove accidental markdown
                patch = re.sub(r"```.*?```", "", patch, flags=re.DOTALL).strip()

                # 2. Normalize for validation
                normalized = re.sub(r"\s+", "", patch.lower())

                # 3. Check: must include escapeRegExp and at least one wrapped usage
                has_helper = "constescaperegexp=" in normalized
                has_usage = "escaperegexp(" in normalized

                if has_helper and has_usage:
                    return patch

                print(f"⚠️ Patch attempt {attempt+1} did not fully apply wrapping, retrying...")

            except Exception as e:
                if "429" in str(e):
                    wait = (attempt + 1) * 4
                    print(f"Patcher rate-limited, retrying in {wait}s...")
                    await asyncio.sleep(wait)
                    continue

                print("Patch LLM error:", e)
                return file_content

        # If we fall through 3 failures → return original file to avoid corruption
        print("❌ Patcher never produced a valid wrapped file. Returning original.")
        return file_content
