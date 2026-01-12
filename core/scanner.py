import subprocess
import json
import os

class Scanner:
    def __init__(self, repo_path):
        self.repo_path = repo_path

    def run_semgrep(self):
        """Runs Semgrep on the full repo and returns prioritized results."""
        print(f"🚀 Starting full-repo scan: {self.repo_path}")
        
        # We use the 'auto' config to detect the language automatically
        cmd = [
            "semgrep", "scan", 
            "--json", 
            "--config", "auto", 
            self.repo_path
        ]
        
        result = subprocess.run(cmd, capture_output=True, text=True)
        
        if result.returncode not in [0, 1]: # Semgrep returns 1 if findings are found
            print(f"Error running Semgrep: {result.stderr}")
            return []

        return self.parse_results(json.loads(result.stdout))

    def parse_results(self, data):
        findings = data.get("results", [])
        
        # Mapping Semgrep levels to numeric priority
        severity_map = {"ERROR": 3, "WARNING": 2, "INFO": 1}
        
        # Sort by severity (Highest first)
        sorted_findings = sorted(
            findings, 
            key=lambda x: severity_map.get(x['extra']['severity'], 0), 
            reverse=True
        )
        
        return sorted_findings