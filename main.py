import os
import asyncio
import json
import shutil
from core.scanner import  Scanner
from agents.attacker import AttackerAgent

def start_hunt(repo_url):
    # 1. Setup Workspace
    repo_name = repo_url.split("/")[-1]
    workspace_path = os.path.abspath(f"./workspaces/{repo_name}")

    if os.path.exists(workspace_path):
        shutil.rmtree(workspace_path)
    
    os.makedirs("./workspaces", exist_ok=True)
    os.system(f"git clone {repo_url} {workspace_path}")

    # 2. Initialize Scanner & Agents
    scanner = Scanner(workspace_path)
    attacker = AttackerAgent()
    
    vulnerabilities = scanner.run_semgrep()
    print(f"🔍 Found {len(vulnerabilities)} potential issues.")

    # 3. Process Findings
    for finding in vulnerabilities:
        # Get severity from Semgrep data
        severity = finding.get('extra', {}).get('severity', 'INFO')
        
        # Call Attacker Agent to validate
        print(f"🕵️ Triage checking finding...")
        code_snippet = finding.get('extra', {}).get('lines', '')
        is_valid, reason, *extra = asyncio.run(attacker.validate(finding,code_snippet))

        if severity == "ERROR" and is_valid:
            print(f"✅ Confirmed Critical: {reason}")
            # Insert Patcher Logic Here
        else:
            print(f"⏭️ Skipping: Valid={is_valid}, Severity={severity}")

if __name__ == "__main__":
    target = "https://github.com/tenzin333/jobpilot2.0" # Example repo
    start_hunt(target)
