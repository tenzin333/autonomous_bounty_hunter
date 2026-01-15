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
from core.github_client import GitHubClient

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

async def start_hunt(repo_full_name):
    # 1. GitHub Setup & Workspace
    gh = GitHubClient() #
    
    # Fork the repo and create a unique branch for this session
    # setup_workspace returns the repo object and the generated branch_name
    forked_repo, branch_name = gh.setup_workspace(repo_full_name) #
    repo_url = forked_repo.clone_url #
    
    repo_name = repo_full_name.split("/")[-1]
    workspace_path = os.path.abspath(f"./workspaces/{repo_name}")
    
    if os.path.exists(workspace_path):
        shutil.rmtree(workspace_path)
    os.makedirs("./workspaces", exist_ok=True)

    print(f"Cloning fork: {repo_url}...")
    # Clone the fork and immediately check out the fix branch
    subprocess.run(["git", "clone", "-b", branch_name, repo_url, workspace_path], check=True)

    scanner = Scanner(workspace_path)
    attacker = AttackerAgent()
    patcher = PatcherAgent()

    # 2. Initial Scan & 3. Triage Phase (Remains same as your version)
    semgrep_data = scanner.run_semgrep()
    vulnerabilities = semgrep_data.get("results", [])
    print(f"Found {len(vulnerabilities)} potential issues. Starting Triage...")
    confirmed_by_file = defaultdict(list)

    for finding in vulnerabilities:
        file_path = finding.get('path')
        if not file_path or not os.path.exists(file_path): continue
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

    # 4. Patching Phase
    unfixable_log = []
    patched_files = [] 

    for file_path, bugs in confirmed_by_file.items():
        print(f"\nProcessing {len(bugs)} fixes in: {os.path.basename(file_path)}")
        backup = file_path + ".bak"
        shutil.copy2(file_path, backup)

        try:
            with open(file_path, "r") as f:
                original_content = f.read()
            work_notes = "\n".join([f"Line {b['line']}: {b['reason']}" for b in bugs])

            print(f"Requesting AI patch for {os.path.basename(file_path)}...")
            raw_patched = await patcher.generate_fix(original_content, work_notes)
            patched_content = clean_output(raw_patched)
            
            if not patched_content or patched_content == original_content:
                shutil.move(backup, file_path)
                continue

            with open(file_path, "w") as f:
                f.write(patched_content)

            # 5. Verification Phase
            bug_ids = [b["id"] for b in bugs]
            remaining = verify_after_patch(file_path, bug_ids)

            if remaining:
                print(f"Verification failed. Rolling back.")
                shutil.move(backup, file_path)
            else:
                print(f"Successfully patched and verified {os.path.basename(file_path)}")
                patched_files.append(file_path)
                if os.path.exists(backup): os.remove(backup)

        except Exception as e:
            print(f"Error patching {file_path}: {e}")
            if os.path.exists(backup): shutil.move(backup, file_path)

    # 6. Push Fixes and Submit PR
    # Move this OUTSIDE the file loop so we submit one PR for all fixes
    if patched_files:
        print("\nPatches verified locally. Pushing to GitHub fork...")
        try:
            # Change directory to the git repo to run git commands
            original_cwd = os.getcwd()
            os.chdir(workspace_path)
            
            subprocess.run(["git", "add", "."], check=True)
            subprocess.run(["git", "commit", "-m", "Security: Fix ReDoS and Format String vulnerabilities"], check=True)
            subprocess.run(["git", "push", "origin", branch_name], check=True)
            
            # Go back to original directory before submitting PR via API
            os.chdir(original_cwd)
            
            print("Submitting Pull Request...")
            pr_url = gh.submit_pull_request(
                original_repo_full_name=repo_full_name,
                head_branch=branch_name,
                title="Automated Security Fixes",
                body="This PR fixes several confirmed security vulnerabilities identified by automated triage."
            ) #
            print(f"PR Created: {pr_url}") #
        except Exception as e:
            print(f"Failed to push or create PR: {e}")

    print("\nHunt completed.")

if __name__ == "__main__":
    # You can change this to any target repository
    target = "https://github.com/tenzin333/jobpilot2.0"
    asyncio.run(start_hunt(target))
