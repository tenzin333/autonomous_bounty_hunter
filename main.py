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
        return {"results": []}
    try:
        return json.loads(result.stdout)
    except Exception:
        return {"results": []}


def verify_after_patch(file_path, original_ids):
    """Rescan and return remaining IDs."""
    scan_results = run_semgrep_json(file_path)
    remaining = [r['check_id'] for r in scan_results.get('results', [])]
    return [i for i in original_ids if i in remaining]


def clean_output(content):
    """Strip accidental fences."""
    if "```" in content:
        content = content.split("```")[1]
    return content.strip()


async def start_hunt(repo_url):
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

    semgrep_data = scanner.run_semgrep()
    vulnerabilities = semgrep_data.get("results", [])
    print(f"Found {len(vulnerabilities)} potential issues. Starting Triage...")

    confirmed_by_file = defaultdict(list)

    # ---- TRIAGE ----
    for finding in vulnerabilities:
        file_path = finding.get('path')
        if not file_path:
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

    # ---- PATCH ----
    for file_path, bugs in confirmed_by_file.items():
        print(f"\nProcessing {len(bugs)} fixes in: {file_path}")

        backup = file_path + ".bak"
        shutil.copy2(file_path, backup)

        try:
            original = open(file_path).read()

            work_notes = "\n".join([
                f"{b['line']}: {b['reason']}" for b in bugs
            ])

            patched = await patcher.generate_fix(original, work_notes)
            patched = clean_output(patched)

            open(file_path, "w").write(patched)

            # Verify once
            remaining = verify_after_patch(file_path, [b["id"] for b in bugs])

            if remaining:
                print(f"Could not fix {len(remaining)} issues — rolling back")
                shutil.move(backup, file_path)
                unfixable_log.append({
                    "file": file_path,
                    "lines": [b["line"] for b in bugs],
                    "explanations": [b["reason"] for b in bugs]
                })
            else:
                print(f"All issues fixed in {file_path}")
                os.remove(backup)

        except Exception as e:
            print(f"Patch error: {e}")
            shutil.move(backup, file_path)
            unfixable_log.append({
                "file": file_path,
                "lines": [b["line"] for b in bugs],
                "error": str(e)
            })

    # ---- SUMMARY REPORT ----
    if unfixable_log:
        os.makedirs("./reports", exist_ok=True)
        with open("./reports/unfixable.json", "w") as f:
            json.dump(unfixable_log, f, indent=2)

        print("\nHUMAN REVIEW REQUIRED:")
        for item in unfixable_log:
            print(f" - {item['file']} lines {item['lines']}")

    print("\nDONE.")


if __name__ == "__main__":
    target = "https://github.com/tenzin333/jobpilot2.0"
    asyncio.run(start_hunt(target))
