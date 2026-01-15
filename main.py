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
    print(f"🔍 Verifying findings for {os.path.basename(file_path)}...")
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
    """Strips markdown code fences from AI output."""
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
    
    print(f"Cloning {repo_url}...")
    os.system(f"git clone {repo_url} {workspace_path}")

    scanner = Scanner(workspace_path)
    attacker = AttackerAgent()
    patcher = PatcherAgent()
    
    vulnerabilities = scanner.run_semgrep()
    print(f"Found {len(vulnerabilities)} potential issues. Starting Triage...")

    # 2. Group Validated Findings by File
    confirmed_by_file = defaultdict(list)

    for finding in vulnerabilities:
        file_path = finding.get('path', 'Unknown File')
        line_number = finding.get('start', {}).get('line', '??')
        code_snippet = finding.get('extra', {}).get('lines', '')
        
        if "console.log" in code_snippet.lower():
            continue

        print(f"\n--- Triage: {os.path.basename(file_path)}:{line_number} ---")
        result = await attacker.validate(finding, code_snippet, file_path, line_number)

        if isinstance(result, dict) and result.get("valid"):
            reason = result.get("explanation", "Critical bug confirmed.")
            # Embed the ReDoS fix instructions directly in the triage reason
            reason_with_hint = (
                f"Issue: {reason}\n"
                "INSTRUCTION: You MUST use an 'escapeRegExp' helper function and wrap dynamic variables "
                "in new RegExp() calls to prevent catastrophic backtracking."
            )
            print(f"[CONFIRMED] {reason[:80]}...")
            confirmed_by_file[file_path].append({
                "id": finding.get('check_id'),
                "reason": reason_with_hint,
                "line": line_number
            })
        else:
            print(f"Skipping: {result.get('explanation', 'Not validated')[:60]}...")

    # 3. Batch Patching Loop
    for file_path, bugs in confirmed_by_file.items():
        print(f"\nProcessing {len(bugs)} fixes for: {file_path}")
        backup_path = f"{file_path}.bak"
        shutil.copy2(file_path, backup_path)
        
        try:
            with open(file_path, 'r') as f:
                original_content = f.read()

            work_order = "\n".join([f"- Line {b['line']}: {b['reason']}" for b in bugs])

            # --- ATTEMPT 1 ---
            print(f"Generating Batch Patch (Attempt 1)...")
            patched_content = await patcher.generate_fix(original_content, work_order)
            with open(file_path, 'w') as f:
                f.write(clean_output(patched_content))

            # Initial check
            failed_bugs = [b for b in bugs if not verify_patch(file_path, b['id'])]

            # --- ATTEMPT 2 (RETRY) if bugs remain ---
            if failed_bugs:
                print(f"Attempt 1 missed {len(failed_bugs)} bugs. Retrying with strict rules...")
                retry_order = work_order + "\n\nCRITICAL: Use .replace(/[.*+?^${}()|[\\\\\\]]/g, '\\\\$&') for escaping."
                
                # We retry using the ORIGINAL content as base to avoid double-patching errors
                patched_content_v2 = await patcher.generate_fix(original_content, retry_order)
                with open(file_path, 'w') as f:
                    f.write(clean_output(patched_content_v2))
                
                # Re-verify
                failed_bugs = [b for b in bugs if not verify_patch(file_path, b['id'])]

            # --- CONSOLIDATED SUCCESS/FAILURE LOGIC ---
            initial_count = len(bugs)
            remaining_count = len(failed_bugs)
            
            if remaining_count < initial_count:
                # We made at least SOME progress
                if remaining_count == 0:
                    print(f"ALL {initial_count} issues in {file_path} fixed and verified!")
                else:
                    print(f"Partial Progress! Fixed {initial_count - remaining_count} bugs, but {remaining_count} still remain.")
                    print(f"Keeping partial fix for {file_path}.")
                
                if os.path.exists(backup_path):
                    os.remove(backup_path)
            else:
                # No progress at all
                print(f"FAILED: No progress made on {os.path.basename(file_path)}.")
                # Show a preview for debugging
                preview = patched_content if 'patched_content_v2' not in locals() else patched_content_v2
                print("--- DEBUG PREVIEW (First 10 lines) ---")
                print("\n".join(clean_output(preview).splitlines()[:10]))
                print("---------------------------------------")
                if "escapeRegExp(" not in patched_content:
                    print("Warning: AI added the helper but didn't actually wrap any variables!")
                # You could force a retry here or just let it proceed to verification
                if os.path.exists(backup_path):
                    shutil.move(backup_path, file_path)
                    print(f"Rolled back {os.path.basename(file_path)} to original state.")

        except Exception as e:
            print(f"Patching Error in {file_path}: {e}")
            if os.path.exists(backup_path):
                shutil.move(backup_path, file_path)

if __name__ == "__main__":
    target = "https://github.com/tenzin333/jobpilot2.0"
    asyncio.run(start_hunt(target))
