import re

class PatcherAgent:
    @staticmethod
    async def generate_fix(file_content, work_notes):
        """
        Deterministic fix for ReDoS patterns.
        If no safe pattern is found, returns original content.
        """
        
        # Exact sanitization helper required by Semgrep
        helper = "const escapeRegExp = (s) => s.replace(/[.*+?^${}()|[\\\\\\]]/g, '\\\\$&');"
        
        # Track if we actually made a change
        original_content = file_content
        patched = file_content

        # Rule 1: MongoDB $regex patterns
        # Example: { name: { $regex: searchVar } }
        direct_pattern = r"\$regex\s*:\s*([A-Za-z0-9_.$]+)"
        if re.search(direct_pattern, patched):
            patched = re.sub(
                direct_pattern,
                r"$regex: new RegExp(escapeRegExp(\1))",
                patched
            )

        # Rule 2: Constructor new RegExp(var)
        # Avoid double-wrapping if already patched
        new_re = r"new\s+RegExp\((?![^)]*escapeRegExp)([^,)]+)(,[^)]+)?\)"
        if re.search(new_re, patched):
            patched = re.sub(
                new_re,
                r"new RegExp(escapeRegExp(\1)\2)",
                patched
            )

        # Rule 3: String.match(var) or String.search(var)
        # Convert to match(new RegExp(escapeRegExp(var)))
        match_pattern = r"\.(match|search)\((?![^)]*new\s+RegExp)([^)]+)\)"
        if re.search(match_pattern, patched):
            patched = re.sub(
                match_pattern,
                r".\1(new RegExp(escapeRegExp(\2)))",
                patched
            )

        # Rule 4: Unsafe console.log (Format String)
        # Convert console.log(var) to console.log("%s", var)
        log_pattern = r"console\.log\((?!\s*['\"`%])([^)]+)\)"
        if re.search(log_pattern, patched):
            patched = re.sub(log_pattern, r'console.log("%s", \1)', patched)

        # Finalize: Add helper if changes were made and it's missing
        if patched != original_content:
            if "const escapeRegExp" not in patched:
                # Insert helper after 'import' or 'require' or at top
                if "import " in patched or "require(" in patched:
                    lines = patched.splitlines()
                    insert_idx = 0
                    for i, line in enumerate(lines):
                        if "import " in line or "require(" in line:
                            insert_idx = i + 1
                    lines.insert(insert_idx, f"\n{helper}")
                    patched = "\n".join(lines)
                else:
                    patched = helper + "\n\n" + patched
            return patched

        return original_content