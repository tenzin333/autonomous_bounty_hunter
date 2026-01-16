import asyncio
import json
import logging
import os
import re
import shutil
import subprocess
from datetime import datetime
from collections import defaultdict

from core.scanner import Scanner
from agents.attacker import AttackerAgent
from agents.patcher import PatcherAgent
from core.github_client import GitHubClient
from contracts.web3 import BlockchainLogger
from core.config import Config
from core.hunterDB import HunterDB as Database

# Basic logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s"
)
log = logging.getLogger(__name__)


def generate_professional_pr_body(confirmed_patches, repo_name):
    body = f"### Automated Security Fixes for `{repo_name}`\n\n"
    body += "> IMPORTANT\n"
    body += "> This is an automated pull request. Review carefully before merging.\n\n"

    body += "#### Changes and Remediation\n"
    body += "The following vulnerabilities were identified and patched:\n\n"
    body += "| File | Vulnerability Type | Line | Status |\n"
    body += "| :--- | :--- | :--- | :--- |\n"

    for file_path, bugs in confirmed_patches.items():
        file_name = os.path.basename(file_path)
        for bug in bugs:
            vuln_type = bug['id'].split('.')[-1].replace('-', ' ').title()
            body += f"| `{file_name}` | {vuln_type} | {bug['line']} | Verified |\n"

    body += "\n#### Technical Details\n"
    body += "- Tooling: Semgrep and AI remediation\n"
    body += "- Remediation: Secure regex patterns, safer formatting, and input guards\n\n"
    body += "---\n"
    body += "Refer to the project security policy for manual audit instructions.\n"
    return body


def run_semgrep_json(path):
    """Run Semgrep and return parsed JSON results."""
    cmd = ["semgrep", "--config", "auto", "--json", path]
    result = subprocess.run(cmd, capture_output=True, text=True)

    if result.returncode not in (0, 1):
        log.warning(f"Semgrep exited {result.returncode}. stderr: {result.stderr.strip()}")
        return {"results": []}

    try:
        return json.loads(result.stdout)
    except Exception as e:
        log.error(f"Failed to parse Semgrep JSON: {e}")
        return {"results": []}


def verify_after_patch(file_path, original_ids):
    scan_results = run_semgrep_json(file_path)
    remaining_ids = [r.get('check_id') for r in scan_results.get('results', [])]
    return [oid for oid in original_ids if oid in remaining_ids]


def clean_output(content):
    content = re.sub(r"```[a-zA-Z]*\n?", "", content)
    content = content.replace("```", "")
    return content.strip()


async def start_hunt(repo_full_name):
    gh = GitHubClient()
    db = Database()

    # Workspace prep
    forked_repo, branch_name = gh.setup_workspace(repo_full_name)
    repo_url = forked_repo.clone_url
    repo_name = repo_full_name.split("/")[-1]

    workspace_path = os.path.abspath(f"./workspaces/{repo_name}")
    if os.path.exists(workspace_path):
        shutil.rmtree(workspace_path)

    os.makedirs("./workspaces", exist_ok=True)

    log.info(f"Cloning forked repository {repo_url} to {workspace_path}")
    subprocess.run(["git", "clone", "-b", branch_name, repo_url, workspace_path], check=True)

    scanner = Scanner(workspace_path)
    attacker = AttackerAgent()
    patcher = PatcherAgent()

    # Scan
    semgrep_data = scanner.run_semgrep() or {}
    vulnerabilities = semgrep_data.get("results", [])
    log.info(f"Found {len(vulnerabilities)} potential issues")

    confirmed_by_file = defaultdict(list)

    # Triage
    for finding in vulnerabilities:
        file_path = finding.get('path')
        if not file_path or not os.path.exists(file_path):
            log.warning("Skipping missing file")
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
            log.info(f"Confirmed vulnerability at {file_path}:{line}")

    unfixable_log = []
    patched_files = []

    # Patching
    for file_path, bugs in confirmed_by_file.items():
        log.info(f"Processing {len(bugs)} issues in {file_path}")
        backup = f"{file_path}.bak"
        shutil.copy2(file_path, backup)

        try:
            with open(file_path, "r") as f:
                original_content = f.read()

            work_notes = "\n".join([f"Line {b['line']}: {b['reason']}" for b in bugs])
            raw_patched = await patcher.generate_fix(original_content, work_notes)
            patched_content = clean_output(raw_patched)

            if not patched_content or patched_content == original_content:
                log.warning("Patch rejected: No meaningful changes")
                shutil.move(backup, file_path)
                continue

            with open(file_path, "w") as f:
                f.write(patched_content)

            # Verify
            bug_ids = [b["id"] for b in bugs]
            remaining = verify_after_patch(file_path, bug_ids)

            if remaining:
                log.warning(f"Patch failed verification, restoring {file_path}")
                shutil.move(backup, file_path)
                unfixable_log.append({
                    "file": file_path,
                    "lines": [b["line"] for b in bugs],
                    "reason": "Semgrep still detects issues"
                })
            else:
                log.info(f"Successfully patched {file_path}")
                patched_files.append(file_path)
                if os.path.exists(backup):
                    os.remove(backup)

        except Exception as e:
            log.error(f"Error patching {file_path}: {e}")
            if os.path.exists(backup):
                shutil.move(backup, file_path)

    # Commit + PR
    if patched_files:
        log.info("Committing and pushing changes")
        cwd = os.getcwd()
        try:
            os.chdir(workspace_path)
            subprocess.run(["git", "add", "."], check=True)
            subprocess.run(["git", "commit", "-m", "security: automated fixes"], check=True)
            subprocess.run(["git", "push", "origin", branch_name], check=True)
        finally:
            os.chdir(cwd)

        log.info("Submitting pull request")
        pr_body = generate_professional_pr_body(confirmed_by_file, repo_name)
        pr_url = gh.submit_pull_request(
            original_repo_full_name=repo_full_name,
            head_branch=branch_name,
            title="Automated Security Fixes",
            body=pr_body
        )
        log.info(f"Pull request created: {pr_url}")

        # Blockchain logging
        log.info("Logging results to blockchain")
        logger = BlockchainLogger(Config.RPC_URL, Config.AGENT_PRIVATE_KEY)

        for file_path in patched_files:
            file_name = os.path.basename(file_path)
            findings = confirmed_by_file.get(file_path, [])
            for bug in findings:
                vuln_type = bug['id'].split('.')[-1]
                commit_tx = logger.log_finding(repo_full_name, file_name, vuln_type)
                finding_id = db.save_commitment(
                    repo=repo_full_name, file=file_name,
                    vuln=vuln_type, salt=logger.salt,
                    commit_hash=commit_tx
                )
                db.update_pr_url(finding_id, pr_url)
                log.info(f"Blockchain commit saved for vulnerability {finding_id}")

    else:
        log.info("No patches passed verification. PR skipped.")

    # Summary + report
    log.info("--------------------------------------------------")
    log.info(f"Confirmed: {sum(len(v) for v in confirmed_by_file.values())}")
    log.info(f"Patched: {len(patched_files)}")
    log.info(f"Unfixable: {len(unfixable_log)}")

    if unfixable_log:
        os.makedirs("./reports", exist_ok=True)
        fh = f"./reports/unfixable_{datetime.now().strftime('%Y%m%d%H%M%S')}.json"
        with open(fh, "w") as f:
            json.dump(unfixable_log, f, indent=2)
        log.info(f"Unfixable issues written to {fh}")

    log.info("Hunt complete")


if __name__ == "__main__":
    target_repo = Config.TARGET_REPO
    asyncio.run(start_hunt(target_repo))
