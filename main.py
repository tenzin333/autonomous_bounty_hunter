import os
import subprocess
import asyncio
import json
import shutil
import re
from collections import defaultdict
from core.scanner import Scanner
from agents.attacker import AttackerAgent
from agents.patcher import PatcherAgent

def run_semgrep_json(path):
    """Run Semgrep and return parsed JSON results."""
    # Use p/default and p/security-audit for verification to match initial scan
    cmd = ["semgrep", "scan", "--config", "auto", "--json", path]
    result = subprocess.run(cmd, capture_output=True, text=True)
    if result.returncode not in (0, 1):
        return {"results": []}
    try:
        return json.loads(result.stdout)
    except Exception:
        return {"results": []}

def verify_after_patch(file_path, original_ids):
    """Rescan the file and return list of original IDs that still exist."""
    scan_results = run_semgrep_json(file_path)
    remaining_ids = [r['check_id'] for r in scan_results.get('results', [])]
    # Return only the IDs we were specifically trying to fix
    return [oid for oid in original_ids if oid in remaining_ids]

def clean_output(content):
    """Aggressively strip markdown fences and language labels from LLM output."""
    # Remove ```javascript, ```js, etc.
    content = re.sub(r"```[a-zA-Z]*\n?", "", content)
    # Remove closing fences
    content = content.replace("```", "")
    return content.strip()

async def start_hunt(repo_url):
    # 1. Setup Workspace
    repo_name = repo_url.split("/")[-1]
    workspace_path = os.path.abspath(f"./workspaces/{repo_name}")
    if os.path.exists(workspace_path):
        shutil.rmtree(workspace_path)
    os.makedirs("./workspaces", exist_ok=True)

    print(f"Cloning {repo_url}...")
    subprocess.run(["git", "clone", repo_url, workspace_path], check=True)

    scanner = Scanner(workspace_path)
    attacker = AttackerAgent()
    patcher = PatcherAgent()

    # 2. Initial Scan
    semgrep_data = scanner.run_semgrep()
    vulnerabilities = semgrep_data.get("results", [])
    print(f"Found {len(vulnerabilities)} potential issues. Starting Triage...")

    confirmed_by_file = defaultdict(list)

    # 3. Triage Phase
    for finding in vulnerabilities:
        file_path = finding.get('path')
        if not file_path or not os.path.exists(file_path):
            continue

        line = finding.get('start', {}).get('line', 0)
        code_context = attacker.get_code_context(file_path, line)
        result = await attacker.validate(finding, code_context, file_path, line)

        if isinstance(result, dict) and result.get("valid"):
            confirmed_by_file[file_path].append({
                "id": finding.get("check_id"),
                "reason": result.get("explanation"),
                "line": line
            })
            print(f"[CONFIRMED] {os.path.basename(file_path)}:{line}")
        else:
            print(f"Skipping {os.path.basename(file_path)}:{line}")

    unfixable_log = []

    # 4. Patching Phase
    for file_path, bugs in confirmed_by_file.items():
        print(f"\nProcessing {len(bugs)} fixes in: {os.path.basename(file_path)}")

        backup = file_path + ".bak"
        shutil.copy2(file_path, backup)

        try:
            with open(file_path, "r") as f:
                original_content = f.read()

            work_notes = "\n".join([f"Line {b['line']}: {b['reason']}" for b in bugs])

            # LLM-Powered Patching
            print(f"Requesting AI patch for {os.path.basename(file_path)}...")
            raw_patched = await patcher.generate_fix(original_content, work_notes)
            patched_content = clean_output(raw_patched)
            
            # Check if LLM returned empty or unchanged content
            if not patched_content or patched_content == original_content:
                print("AI failed to provide a modified version. Skipping.")
                shutil.move(backup, file_path)
                unfixable_log.append({
                    "file": file_path,
                    "lines": [b["line"] for b in bugs],
                    "reason": "AI returned empty or unchanged content."
                })
                continue

            # Write the patch to file
            with open(file_path, "w") as f:
                f.write(patched_content)

            # 5. Verification Phase
            bug_ids = [b["id"] for b in bugs]
            remaining = verify_after_patch(file_path, bug_ids)

            if remaining:
                print(f"Verification failed: {len(remaining)} issues remain. Rolling back.")
                shutil.move(backup, file_path)
                unfixable_log.append({
                    "file": file_path,
                    "lines": [b["line"] for b in bugs],
                    "remaining_ids": remaining,
                    "reason": "AI patch did not satisfy Semgrep scanner."
                })
            else:
                print(f"Successfully patched and verified {os.path.basename(file_path)}")
                if os.path.exists(backup):
                    os.remove(backup)

        except Exception as e:
            print(f"Error patching {file_path}: {e}")
            if os.path.exists(backup):
                shutil.move(backup, file_path)
            unfixable_log.append({
                "file": file_path,
                "error": str(e)
            })

    # 6. Summary Report
    if unfixable_log:
        os.makedirs("./reports", exist_ok=True)
        report_path = "./reports/unfixable.json"
        with open(report_path, "w") as f:
            json.dump(unfixable_log, f, indent=2)

        print(f"\nREPORTS GENERATED: {report_path}")
        print("HUMAN REVIEW REQUIRED FOR:")
        for item in unfixable_log:
            f_name = os.path.basename(item.get('file', 'Unknown'))
            print(f" - {f_name} (Lines: {item.get('lines', 'N/A')})")

    print("\nHunt completed.")


if __name__ == "__main__":
    # You can change this to any target repository
    target = "https://github.com/tenzin333/jobpilot2.0"
    asyncio.run(start_hunt(target))
