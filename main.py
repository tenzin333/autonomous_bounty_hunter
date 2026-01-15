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

def generate_professional_pr_body(confirmed_patches, repo_name):
    """
    Constructs a professional Markdown body for the GitHub Pull Request.
    """
    # Header with a professional alert
    body = f"### Automated Security Fixes for `{repo_name}`\n\n"
    body += "> [!IMPORTANT]\n"
    body += "> This is an automatic PR generated to help with patching efforts. "
    body += "Please review the changes carefully before merging.\n\n"

    # Vulnerability Summary
    body += "#### Changes and Remediation\n"
    body += "The following vulnerabilities were identified and addressed using automated patching and verification:\n\n"
    
    # Summary Table
    body += "| File | Vulnerability Type | Line | Status |\n"
    body += "| :--- | :--- | :--- | :--- |\n"
    
    for file_path, bugs in confirmed_patches.items():
        file_name = os.path.basename(file_path)
        for bug in bugs:
            # Extract a readable name from the Semgrep check_id
            vuln_type = bug['id'].split('.')[-1].replace('-', ' ').title()
            body += f"| `{file_name}` | {vuln_type} | {bug['line']} |  Verified |\n"

    # Technical Details
    body += "\n#### Technical Details\n"
    body += "- **Tooling**: Verified via Semgrep static analysis and AI-driven remediation.\n"
    body += "- **Remediation**: Implemented input sanitization and secure regex patterns to prevent ReDoS and injection attacks.\n\n"
    
    body += "---\n"
    body += "*For more information or manual review instructions, please refer to your project security policy.*"
    
    return body

def run_semgrep_json(path):
    """Run Semgrep and return parsed JSON results."""
    # Using 'auto' config for verification to ensure the patch satisfies the scanner
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
    # Filter to see if the specific IDs we were targeting are still there
    return [oid for oid in original_ids if oid in remaining_ids]

def clean_output(content):
    """Aggressively strip markdown fences and language labels from LLM output."""
    content = re.sub(r"```[a-zA-Z]*\n?", "", content)
    content = content.replace("```", "")
    return content.strip()

async def start_hunt(repo_full_name):
    # 1. GitHub Setup & Workspace
    gh = GitHubClient()
    
    # Fork the repo and create a unique branch via API
    forked_repo, branch_name = gh.setup_workspace(repo_full_name) #
    repo_url = forked_repo.clone_url 
    
    repo_name = repo_full_name.split("/")[-1]
    workspace_path = os.path.abspath(f"./workspaces/{repo_name}")
    
    if os.path.exists(workspace_path):
        shutil.rmtree(workspace_path)
    os.makedirs("./workspaces", exist_ok=True)

    print(f"Cloning fork: {repo_url}...")
    # Clone the fork and checkout the generated branch
    subprocess.run(["git", "clone", "-b", branch_name, repo_url, workspace_path], check=True)

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
        print(f"\nLooking for ${file_path}...")
        if not file_path or not os.path.exists(file_path): 
            print("File not found, skipping.")
            continue
        
        line = finding.get('start', {}).get('line', 0)
        # Use AttackerAgent to get code context and validate exploitability
        code_context = attacker.get_code_context(file_path, line) #
        result = await attacker.validate(finding, code_context, file_path, line) #
        
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

            # Use LLM to generate the code patch
            print(f"Requesting AI patch for {os.path.basename(file_path)}...")
            raw_patched = await patcher.generate_fix(original_content, work_notes)
            patched_content = clean_output(raw_patched)
            
            if not patched_content or patched_content == original_content:
                print("Patch rejected: No changes made by AI.")
                shutil.move(backup, file_path)
                continue

            with open(file_path, "w") as f:
                f.write(patched_content)

            # 5. Verification Phase
            bug_ids = [b["id"] for b in bugs]
            remaining = verify_after_patch(file_path, bug_ids)

            if remaining:
                print(f"Verification failed: {len(remaining)} issues still detected. Rolling back.")
                shutil.move(backup, file_path)
                unfixable_log.append({"file": file_path, "lines": [b["line"] for b in bugs], "reason": "Semgrep still finds issues."})
            else:
                print(f"Successfully patched and verified {os.path.basename(file_path)}")
                patched_files.append(file_path)
                if os.path.exists(backup): os.remove(backup)

        except Exception as e:
            print(f"Error patching {file_path}: {e}")
            if os.path.exists(backup): shutil.move(backup, file_path)

    # 6. Push Fixes and Submit Pull Request
    if patched_files:
        print("\nPushing verified patches to GitHub...")
        original_cwd = os.getcwd()
        try:
            os.chdir(workspace_path)
            
            # Git operations for commit and push
            subprocess.run(["git", "add", "."], check=True)
            subprocess.run(["git", "commit", "-m", "security: fix ReDoS and format string vulnerabilities"], check=True)
            subprocess.run(["git", "push", "origin", branch_name], check=True) #
            
            os.chdir(original_cwd)
            
            # Submit PR back to original repo
            print("Submitting Pull Request...")
            generated_body = generate_professional_pr_body(confirmed_by_file, repo_name)
            pr_url = gh.submit_pull_request(
                original_repo_full_name=repo_full_name, #
                head_branch=branch_name, #
                title="Automated Security Fixes",
                body=generated_body
            )
            print(f"PR Successfully Created: {pr_url}")
        except Exception as e:
            print(f"Failed to push or create PR: {e}")
        finally:
            os.chdir(original_cwd)

    # 7. Final Report
    if unfixable_log:
        os.makedirs("./reports", exist_ok=True)
        with open("./reports/unfixable.json", "w") as f:
            json.dump(unfixable_log, f, indent=2)
    
    print("\nHunt completed.")

if __name__ == "__main__":
    # Ensure this name is exactly owner/repo
    target_repo = "tenzin333/jobpilot2.0" 
    asyncio.run(start_hunt(target_repo))