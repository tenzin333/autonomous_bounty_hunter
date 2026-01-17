import asyncio
import json
import logging
import os
import re
import shutil
import subprocess
import time
from datetime import datetime
from collections import defaultdict

from core.scanner import Scanner
from agents.attacker import AttackerAgent
from agents.patcher import PatcherAgent
from core.github_client import GitHubClient
from onchain.script.web3 import BlockchainLogger
from core.config import Config
from core.hunterDB import HunterDB as Database

# Standard technical logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s"
)
log = logging.getLogger(__name__)

def generate_professional_pr_body(confirmed_patches, repo_name):
    """Generates a clean, markdown-based PR description."""
    body = f"### Automated Security Fixes for {repo_name}\n\n"
    body += "IMPORTANT: This is an automated pull request. Review carefully before merging.\n\n"
    body += "#### Changes and Remediation\n"
    body += "The following vulnerabilities were identified and patched:\n\n"
    body += "| File | Vulnerability Type | Line | Status |\n"
    body += "| :--- | :--- | :--- | :--- |\n"

    for file_path, bugs in confirmed_patches.items():
        file_name = os.path.basename(file_path)
        for bug in bugs:
            vuln_type = bug['id'].split('.')[-1].replace('-', ' ').title()
            body += f"| {file_name} | {vuln_type} | {bug['line']} | Verified |\n"

    body += "\n#### Technical Details\n"
    body += "- Static Analysis: Semgrep\n"
    body += "- Patching Engine: AI-driven remediation\n"
    body += "- Verification: Post-patch regression scan\n"
    return body

def run_semgrep_json(path):
    """Executes Semgrep scan and returns JSON result object."""
    cmd = ["semgrep", "--config", "auto", "--json", path]
    result = subprocess.run(cmd, capture_output=True, text=True)

    if result.returncode not in (0, 1):
        log.warning(f"Semgrep exit code {result.returncode}. Error: {result.stderr.strip()}")
        return {"results": []}

    try:
        return json.loads(result.stdout)
    except Exception as e:
        log.error(f"Failed to parse Semgrep JSON output: {e}")
        return {"results": []}

def verify_after_patch(file_path, original_ids):
    """Checks if previously identified vulnerabilities still exist after patching."""
    scan_results = run_semgrep_json(file_path)
    remaining_ids = [r.get('check_id') for r in scan_results.get('results', [])]
    return [oid for oid in original_ids if oid in remaining_ids]

def clean_output(content):
    """Removes markdown code blocks from LLM generated content."""
    content = re.sub(r"```[a-zA-Z]*\n?", "", content)
    content = content.replace("```", "")
    return content.strip()

async def start_hunt(repo_full_name):
    """Main execution loop for the Autonomous Bounty Hunter."""
    gh = GitHubClient()
    db = Database()
    
    # Initialize Local Blockchain Logger (Anvil)
    try:
        blockchain = BlockchainLogger(
            provider_url=Config.RPC_URL,
            private_key=Config.PRIVATE_KEY,
            contract_address=Config.CONTRACT_ADDRESS,
            contract_abi_path=Config.ABI_PATH
        )
        log.info(f"Blockchain Logger connected to {Config.RPC_URL}")
    except Exception as e:
        log.error(f"Blockchain initialization failed: {e}")
        return

    # Workspace Setup
    forked_repo, branch_name = gh.setup_workspace(repo_full_name)
    repo_url = forked_repo.clone_url
    repo_name = repo_full_name.split("/")[-1]
    workspace_path = os.path.abspath(f"./workspaces/{repo_name}")

    if os.path.exists(workspace_path):
        shutil.rmtree(workspace_path)
    os.makedirs("./workspaces", exist_ok=True)

    log.info(f"Cloning {repo_url} to {workspace_path}")
    subprocess.run(["git", "clone", "-b", branch_name, repo_url, workspace_path], check=True)

    scanner = Scanner(workspace_path)
    attacker = AttackerAgent()
    patcher = PatcherAgent()

    # Step 1: Scanning
    semgrep_data = scanner.run_semgrep() or {}
    vulnerabilities = semgrep_data.get("results", [])
    log.info(f"Scan complete: {len(vulnerabilities)} vulnerabilities identified.")

    confirmed_by_file = defaultdict(list)

    # Step 2: Triage and Validation
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
            log.info(f"Validated: {finding.get('check_id')} in {os.path.basename(file_path)}:{line}")

    # Step 3: Patching and Verification
    patched_files = []
    unfixable_log = []

    for file_path, bugs in confirmed_by_file.items():
        log.info(f"Applying patches to {file_path}")
        backup = f"{file_path}.bak"
        shutil.copy2(file_path, backup)

        try:
            with open(file_path, "r") as f:
                original_content = f.read()

            work_notes = "\n".join([f"Line {b['line']}: {b['reason']}" for b in bugs])
            raw_patched = await patcher.generate_fix(original_content, work_notes)
            patched_content = clean_output(raw_patched)

            if not patched_content or patched_content == original_content:
                log.warning(f"Patch failed for {file_path}: No content change.")
                shutil.move(backup, file_path)
                continue

            with open(file_path, "w") as f:
                f.write(patched_content)

            # Verification Scan
            bug_ids = [b["id"] for b in bugs]
            remaining = verify_after_patch(file_path, bug_ids)

            if remaining:
                log.warning(f"Patch rejected for {file_path}: Issues still persist.")
                shutil.move(backup, file_path)
                unfixable_log.append({"file": file_path, "reason": "Verification failed"})
            else:
                log.info(f"Patch verified for {file_path}")
                patched_files.append(file_path)
                if os.path.exists(backup):
                    os.remove(backup)

        except Exception as e:
            log.error(f"Error during patching: {e}")
            if os.path.exists(backup):
                shutil.move(backup, file_path)

    # Step 4: Deployment and On-Chain Logging
    if patched_files:
        log.info("Committing patches and pushing to origin.")
        current_dir = os.getcwd()
        try:
            os.chdir(workspace_path)
            subprocess.run(["git", "add", "."], check=True)
            subprocess.run(["git", "commit", "-m", "security: automated vulnerability remediation"], check=True)
            subprocess.run(["git", "push", "origin", branch_name], check=True)
        finally:
            os.chdir(current_dir)

        pr_body = generate_professional_pr_body(confirmed_by_file, repo_name)
        pr_url = gh.submit_pull_request(
            original_repo_full_name=repo_full_name,
            head_branch=branch_name,
            title="Security Remediation: Automated Fixes",
            body=pr_body
        )
        log.info(f"PR Submitted: {pr_url}")

        # Final Step: Blockchain Commitment
        for file_path in patched_files:
            file_name = os.path.basename(file_path)
            findings = confirmed_by_file.get(file_path, [])
            for bug in findings:
                vuln_name = bug['id'].split('.')[-1]
                
                # Log the strike to the Anvil node
                tx_hash = blockchain.log_finding(repo_full_name, file_name, vuln_name)
                
                db.save_commitment(
                    repo=repo_full_name, 
                    file=file_name,
                    vuln=vuln_name, 
                    salt=blockchain.salt,
                    commit_hash=tx_hash
                )
                log.info(f"On-chain commitment confirmed: {tx_hash}")

    log.info("--------------------------------------------------")
    log.info(f"Hunt Summary for {repo_full_name}")
    log.info(f"Confirmed Vulns: {sum(len(v) for v in confirmed_by_file.values())}")
    log.info(f"Applied Patches: {len(patched_files)}")
    log.info("--------------------------------------------------")

if __name__ == "__main__":
    asyncio.run(start_hunt(Config.TARGET_REPO))

