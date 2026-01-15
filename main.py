import os
import subprocess
import asyncio
import json
import shutil
from collections import defaultdict
from core.scanner import Scanner
from agents.attacker import AttackerAgent
from agents.patcher import PatcherAgent


def run_semgrep_json(path):
    """Run Semgrep once and return parsed JSON."""
    cmd = ["semgrep", "scan", "--config", "auto", "--json", path]
    result = subprocess.run(cmd, capture_output=True, text=True)

    if result.returncode != 0:
        print("Semgrep scan failed.")
        return {"results": []}

    try:
        return json.loads(result.stdout)
    except Exception:
        return {"results": []}


def verify_patch_batch(scan_results, original_ids):
    """
    Validate after patching using ONE semgrep rescan.
    Returns list of ids that still exist.
    """
    remaining = [r['check_id'] for r in scan_results.get('results', [])]
    return [i for i in original_ids if i in remaining]


def clean_output(content):
    """Strips markdown fences from AI output."""
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
    subprocess.run(["git", "clone", repo_url, workspace_path], check=True)

    scanner = Scanner(workspace_path)
    attacker = AttackerAgent()
    patcher = PatcherAgent()

    # First full scan
    semgrep_results = run_semgrep_json(workspace_path)
    vulnerabilities = semgrep_results.get("results", [])
    print(f"Found {len(vulnerabilities)} potential issues. Starting Triage...")

    confirmed_by_file = defaultdict(list)

    # 2. TRIAGE
    for finding in vulnerabilities:
        file_path = finding.get('path')
        if not file_path:
            continue

        line_number = finding.get('start', {}).get('line', 0)
        check_id = finding.get('check_id', '')

        # refined skip logic — skip semgrep console log rule, not string hits
        if check_id.lower().startswith("console-log"):
            continue

        context = attacker.get_code_context(file_path, line_number)

        print(f"\n--- Triage: {os.path.basename(file_path)}:{line_number} ---")
        result = await attacker.validate(finding, context, file_path, line_number)

        if isinstance(result, dict) and result.get("valid"):
            reason = result.get("explanation", "Confirmed issue.")
            reason_with_hint = (
                f"Issue: {reason}\n"
                "INSTRUCTION: You MUST wrap dynamic RegExp input with escapeRegExp()."
            )
            print(f"[CONFIRMED] {reason[:80]}...")
            confirmed_by_file[file_path].append({
                "id": check_id,
                "reason": reason_with_hint,
                "line": line_number
            })
        else:
            print(f"Skipping: {result.get('explanation', 'Not validated')[:60]}...")

    # 3. PATCHING
    for file_path, bugs in confirmed_by_file.items():
        print(f"\nProcessing {len(bugs)} fixes for: {file_path}")

        backup_path = f"{file_path}.bak"
        shutil.copy2(file_path, backup_path)

        try:
            with open(file_path, 'r') as f:
                original = f.read()

            work_order = "\n".join([f"- Line {b['line']}: {b['reason']}" for b in bugs])

            # ATTEMPT 1
            print("Generating Patch (Attempt 1)...")
            patched1 = await patcher.generate_fix(original, work_order)
            patched1 = clean_output(patched1)
            with open(file_path, 'w') as f:
                f.write(patched1)

            # rescan ONCE
            after_scan = run_semgrep_json(file_path)
            failed = verify_patch_batch(after_scan, [b["id"] for b in bugs])

            # ATTEMPT 2
            if failed:
                print(f"Retrying missing {len(failed)} with strict rules...")
                retry_order = work_order + "\nForce escapeRegExp use on ALL RegExp construction."
                patched2 = await patcher.generate_fix(original, retry_order)
                patched2 = clean_output(patched2)
                with open(file_path, 'w') as f:
                    f.write(patched2)

                after_scan = run_semgrep_json(file_path)
                failed = verify_patch_batch(after_scan, [b["id"] for b in bugs])

            if not failed:
                print(f"ALL issues in {file_path} fixed!")
                os.remove(backup_path)
            else:
                print(f"FAILED to fully fix {file_path}. Restoring original.")
                shutil.move(backup_path, file_path)

        except Exception as e:
            print(f"Patching error: {e}")
            shutil.move(backup_path, file_path)

    print("\nDONE.")


if __name__ == "__main__":
    target = "https://github.com/tenzin333/jobpilot2.0"
    asyncio.run(start_hunt(target))
