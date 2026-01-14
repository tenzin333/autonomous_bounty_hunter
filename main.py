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
    print(f"Found {len(vulnerabilities)} potential issues.")

    #inside your start_hunt loop
    for finding in vulnerabilities:
        severity = finding.get('extra', {}).get('severity', 'UNKNOWN')

        file_path = finding.get('path', 'Unkown File')
        line_number = finding.get('start' , {}).get('line', '??')
        message = finding.get('extra' , {}).get('message','No message')
        code_snippet = finding.get('extra', {}).get('lines', '')
        
        #skip triage if the finding is just a logging statement
        if "console.log" in code_snippet.lower():
            print(f"PRE-TRIAGE SKIP: Ignoring log-related finding at {file_path}:{line_number}")
            continue

        print(f"Triage checking finding at {file_path}:{line_number}...")
        # Run the async agent
        result = asyncio.run(attacker.validate(finding, code_snippet))
        # --- FIX STARTS HERE ---
        # Handle the dictionary response correctly
        if isinstance(result, dict):
            is_valid = result.get("valid", False)

            # 1. Grab all possible keys
            raw_reason = (result.get("explanation") or result.get("reason") or result.get("details") or "")

            # 2. If it's still empty, it might be a nested object or the LLM used a different key
            if not raw_reason.strip():
                # Fallback: find the first string value that isn't the 'valid' key
                reasons = [v for k, v in result.items() if isinstance(v, str) and k != 'valid' and v.strip()]
                reason = reasons[0] if reasons else "Confirmed by LLM (No specific reason provided)"
            else:
                reason = raw_reason
        else:
            # Fallback for tuple/list
            is_valid, reason, *extra = result
        """
        if is_valid:
            print("\n" + "="*60)
            print(f"CRITICAL CONFIRMED: {file_path}:{line_number}")
            print(f"TYPE: {message}") # This pulls the Semgrep rule name
            print("-" * 60)
            print(f"CODE CONTEXT:")
            print(f"{code_snippet}") # Shows the actual lines from the file
            print("-" * 60)
            print(f"ANALYSIS: {reason}")
    
            # If you added the payload to your agent:
            payload = result.get("payload", "N/A")    
            print(f"EXPLOIT PAYLOAD: {payload}")
            print("="*60 + "\n")
        else:
            print(f"Skipping: {str(reason)[:40]}...")        
            # Fallback if your agent returns a tuple (is_valid, reason)
            is_valid, reason, *extra = result
        """

        if isinstance(result, dict):
            is_valid = result.get("valid", False)
            reason = result.get("explanation", "No explanation provided")
    
            if is_valid:
                print(f"\n[VULNERABILITY CONFIRMED]")
                print("#"*60)
                print(f"Location: {file_path}:{line_number}")
                print(f"Impact:   {reason}")
                print("#"*60)
            else:
                # This will now show you WHY it's skipping (e.g., "The code is safe because...")
                print(f"TRIAGE NEGATIVE: {reason[:100]}...")
        else:
            print(f"ERROR: Model failed to return JSON. Raw: {str(result)[:50]}")


if __name__ == "__main__":
    target = "https://github.com/tenzin333/jobpilot2.0" # Example repo
    start_hunt(target)
