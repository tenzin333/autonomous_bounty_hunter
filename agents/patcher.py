from core.llm_provider import llm_client
from core.config import Config
import asyncio

class PatcherAgent:
    @staticmethod
    async def generate_fix(file_content, vulnerability_desc):
        """
        Generates a patched version of the full file content.
        
        Args:
            file_content (str): The entire content of the file to be fixed.
            vulnerability_desc (str): The explanation provided by the AttackerAgent.
            
        Returns:
            str: The full file content with the security fix applied.
        """
        system_prompt = (
    "You are a Senior Security Engineer. You ONLY output raw source code.\n\n"
    "CRITICAL RULE: To fix ReDoS, you must do TWO things:\n"
    "1. Define this helper at the top: const escapeRegExp = (s) => s.replace(/[.*+?^${}()|[\\\\\\]]/g, '\\\\$&');\n"
    "2. SEARCH the file for 'new RegExp(...)'. You MUST wrap the first argument in 'escapeRegExp()'.\n"
    "   Example: change 'new RegExp(searchTerm)' to 'new RegExp(escapeRegExp(searchTerm))'.\n\n"
    "REJECTION CRITERIA: If you add the helper but do not wrap the variables in the code, the patch will fail.\n"
    "Maintain all existing functionality and indentation. Return the FULL file."
        )    
        
        user_prompt = f"""
        [VULNERABILITY DETAILS]
        {vulnerability_desc}

        [TASK]
        1. Apply the fixes to the FULL FILE CONTENT provided below.
        2. Use the 'escapeRegExp' pattern mentioned above to resolve all ReDoS issues.
        3. Maintain the exact same coding style and indentation.
        4. Return the ENTIRE updated file content.

        [FULL FILE CONTENT]
        ---
        {file_content}
        ---
        """
        
        for attempt in range(3):
            try:
                response = await llm_client.chat.completions.create(
                    model=Config.PATCHER_MODEL,
                    messages=[
                        {"role": "system", "content": system_prompt},
                        {"role": "user", "content": user_prompt}
                    ],
                    temperature=0.2  # Lower temperature for stable code generation
                )

                patched_code = response.choices[0].message.content.strip()

                # Robust Cleanup: Remove markdown if the model ignored the instruction
                if patched_code.startswith("```"):
                    # Split by backticks and find the largest block of code
                    parts = patched_code.split("```")
                    for part in parts:
                        clean_part = part.strip()
                        # Skip empty parts and language identifiers
                        if clean_part and not clean_part.lower().startswith(("javascript", "js", "python", "typescript", "json")):
                            return clean_part
                        elif clean_part.lower().startswith(("javascript", "js", "python", "typescript")):
                            # Handle blocks that start with a language name
                            return "\n".join(clean_part.split("\n")[1:]).strip()
                
                return patched_code

            except Exception as e:
                if "429" in str(e):
                    wait_time = (attempt + 1) * 5
                    print(f"Patcher rate limited. Retrying in {wait_time}s...")
                    await asyncio.sleep(wait_time)
                    continue
                
                print(f"Patcher LLM Error: {e}")
                # Return original content if patching fails to avoid breaking main.py
                return file_content

        return file_content
