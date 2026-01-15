from core.llm_provider import llm_client
from core.config import Config
import asyncio
import re


class PatcherAgent:
    @staticmethod
    async def generate_fix(file_content, work_notes):
        """
        Fixes only safe patterns.
        Leaves indirect/dangerous ones for humans.
        """

        helper = (
            "const escapeRegExp = "
            "(s) => s.replace(/[.*+?^${}()|[\\\\\\]]/g, '\\\\$&');"
        )

        # ---- RULE 1: direct `$regex: var` → auto fix
        direct_pattern = r"\$regex\s*:\s*([A-Za-z0-9_.$]+)"
        if re.search(direct_pattern, file_content):
            print("Direct {$regex: var} patch")
            patched = re.sub(
                direct_pattern,
                r"$regex: new RegExp(escapeRegExp(\\1))",
                file_content
            )
            if "escapeRegExp" not in patched:
                patched = helper + "\n" + patched
            return patched

        # ---- RULE 2: simple new RegExp(var)
        new_re = r"new\s+RegExp\(([^)]+)\)"
        match = re.search(new_re, file_content)
        if match:
            print("new RegExp(...) patch")
            patched = re.sub(
                new_re,
                r"new RegExp(escapeRegExp(\1))",
                file_content
            )
            if "escapeRegExp" not in patched:
                patched = helper + "\n" + patched
            return patched

        # ---- RULE 3: .match(var) and .search(var)
        if ".match(" in file_content or ".search(" in file_content:
            print(".match()/.search() patch")
            patched = re.sub(
                r"\.match\(([^)]+)\)",
                r".match(new RegExp(escapeRegExp(\1)))",
                file_content
            )
            patched = re.sub(
                r"\.search\(([^)]+)\)",
                r".search(new RegExp(escapeRegExp(\1)))",
                patched
            )
            if "escapeRegExp" not in patched:
                patched = helper + "\n" + patched
            return patched

        # ---- RULE 4: refuse to guess
        print("No safe pattern to auto-fix — skipping")
        return file_content
