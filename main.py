import os
import subprocess
import asyncio
import json
import shutil
from collections import defaultdict
from core.scanner import Scanner
from agents.attacker import AttackerAgent
from agents.patcher import PatcherAgent

def verify_patch(file_path, original_finding_id):
    """Re-scans a specific file to see if the vulnerability is gone."""
    print(f"Verifying patch for {file_path}...")
    cmd = ["semgrep", "scan", "--config", "auto", "--json", file_path]
    result = subprocess.run(cmd, capture_output=True, text=True)
    if result.returncode != 0:
        return False
    try:
        scan_data = json.loads(result.stdout)
        remaining_findings = [f['check_id'] for f in scan_data.get('results', [])]
        return original_finding_id not in remaining_findings
    except Exception:
        return False

def clean_output(content):
    """Maintains your existing logic for stripping markdown code fences."""
    if "```" in content:
        content = content.split("```")[1]
        if content.startswith(("javascript", "js", "python", "typescript")):
            content = "\n".join(content.split("\n")[1:])
    return content.strip()

async def start_hunt(repo_url):
    # 1. Setup Workspace
    repo_name = repo_url.split("/")[-1]
    workspace_path = os.path.abspath(f"./workspaces/{repo_name}")
    if os.path.exists(workspace_path):
        shutil.rmtree(workspace_path)
    os.makedirs("./workspaces", exist_ok=True)
    os.system(f"git clone {repo_url} {workspace_path}")

    scanner = Scanner(workspace_path)
    attacker = AttackerAgent()
    patcher = PatcherAgent()
    
    vulnerabilities = scanner.run_semgrep()
    print(f"Found {len(vulnerabilities)} potential issues. Starting Triage...")

    # 2. Group Validated Findings by File
    # This prevents 'job-schema.js' from being overwritten 4 times in a row
    confirmed_by_file = defaultdict(list)

    for finding in vulnerabilities:
        file_path = finding.get('path', 'Unknown File')
        line_number = finding.get('start', {}).get('line', '??')
        code_snippet = finding.get('extra', {}).get('lines', '')
        
        if "console.log" in code_snippet.lower():
            continue

        print(f"\n--- Triage: {file_path}:{line_number} ---")
        result = await attacker.validate(finding, code_snippet, file_path, line_number)

        if isinstance(result, dict) and result.get("valid"):
            reason = result.get("explanation", "Critical bug confirmed.")
            reason_with_hint = (
                        f"Original Issue: {reason}\n"
                            "RETRY INSTRUCTION: The previous fix failed the security scan. "
                                "You MUST implement the 'escapeRegExp' helper function and wrap the dynamic variables "
                                    "to ensure no special characters can trigger catastrophic backtracking."
                                    )
            print(f"[CONFIRMED] {reason[:100]}")
            confirmed_by_file[file_path].append({
                "id": finding.get('check_id'),
                "reason": reason_with_hint,
                "line": line_number
            })
        else:
            explanation = result.get("explanation", "Safe") if isinstance(result, dict) else "Not valid"
            print(f"Skipping: {explanation[:60]}...")

    # 3. Batch Patching Loop
    for file_path, bugs in confirmed_by_file.items():
        print(f"\nProcessing {len(bugs)} fixes for: {file_path}")
        backup_path = f"{file_path}.bak"
        shutil.copy2(file_path, backup_path)
        
        try:
            with open(file_path, 'r') as f:
                full_file_content = f.read()

            # Create a combined 'work order' for the AI
            work_order = "\n".join([f"- Line {b['line']}: {b['reason']}" for b in bugs])

            # --- ATTEMPT 1 ---
            print(f"🚀 Generating Batch Patch (Attempt 1)...")
            patched_content = await patcher.generate_fix(full_file_content, work_order)
            with open(file_path, 'w') as f:
                f.write(clean_output(patched_content))

            # Check which bugs are still there
            failed_bugs = [b for b in bugs if not verify_patch(file_path, b['id'])]

            # --- ATTEMPT 2 (RETRY) if Attempt 1 didn't fix everything ---
            if failed_bugs:
                print(f"Attempt 1 missed {len(failed_bugs)} bugs. Retrying with explicit security rules...")
                retry_order = work_order + "\n\nCRITICAL: Use a robust regex escaping helper (e.g. .replace(/[.*+?^${}()] /g, '\\$&')) for ReDoS fixes to satisfy Semgrep."
                
                patched_content_v2 = await patcher.generate_fix(full_file_content, retry_order)
                with open(file_path, 'w') as f:
                    f.write(clean_output(patched_content_v2))
                
                # Final Verification
                failed_bugs = [b for b in bugs if not verify_patch(file_path, b['id'])]

            if not failed_bugs:
                print(f"ALL issues in {file_path} fixed and verified!")
                if os.path.exists(backup_path): os.remove(backup_path)
            else:
                print(f"--- FAILED PATCH PREVIEW FOR {file_path} ---")
                print("\n".join(patched_content_v2.splitlines()[:15])) # See the first 15 lines (check for escapeRegExp)
                print("--- END PREVIEW ---")
                print(f"FAILED: {len(failed_bugs)} issues still remain. Rolling back file.")
                shutil.move(backup_path, file_path)

        except Exception as e:
            print(f"Patching Error in {file_path}: {e}")
            if os.path.exists(backup_path): shutil.move(backup_path, file_path)

if __name__ == "__main__":
    target = "https://github.com/tenzin333/jobpilot2.0"
    asyncio.run(start_hunt(target))
