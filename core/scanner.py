import subprocess
import json
import os
from core.config import Config

class Scanner:
    def __init__(self, repo_path):
        self.repo_path = os.path.abspath(repo_path)

    def run_semgrep(self):
        print(f"🚀 Starting full-repo scan: {self.repo_path}")

        # Force UTF-8 environment
        env = os.environ.copy()
        env["PYTHONUTF8"] = "1"
        env["PYTHONIOENCODING"] = "utf-8"

        # Remove .semgrepignore to prevent hidden skips
        ignore_file = os.path.join(self.repo_path, ".semgrepignore")
        if os.path.exists(ignore_file):
            try:
                os.remove(ignore_file)
                print("🗑️ Removed .semgrepignore")
            except:
                pass

        # Optimized command with --no-git-ignore to fix your current error
        cmd = [
            "semgrep", "scan",
            "--json",
            # This is the "God Mode" config - it includes rules for almost every language
            "--config", "p/default", 
            "--config", "p/security-audit",
            "--config", "p/secrets",
            "--no-git-ignore",
            # Tells Semgrep to ignore files it can't parse (like images/binaries)
            "--skip-unknown-extensions", 
            self.repo_path
         ]
  
        try:
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                shell=(os.name == 'nt'),
                encoding='utf-8',
                env=env
            )

            if result.returncode not in [0, 1]:
                print(f"❌ Semgrep failed: {result.stderr[:200]}")
                return []

            output = result.stdout.strip()
            if not output:
                return []

            data = json.loads(output)
            return self.parse_results(data)
        except Exception as e:
            print(f"❌ Error: {e}")
            return []

    def parse_results(self, data):
        findings = data.get("results", [])
        severity_map = {"ERROR": 3, "WARNING": 2, "INFO": 1}
        return sorted(
            findings, 
            key=lambda x: severity_map.get(x['extra']['severity'], 0), 
            reverse=True
        )
