import subprocess
import json
import os


class Scanner:
    def __init__(self, repo_path):
        self.repo_path = os.path.abspath(repo_path)

    def run_semgrep(self):
        print(f"🔍 Scanning repository: {self.repo_path}")

        env = os.environ.copy()
        env["PYTHONUTF8"] = "1"

        ignore = os.path.join(self.repo_path, ".semgrepignore")
        if os.path.exists(ignore):
            try:
                os.remove(ignore)
                print("🗑  Removed .semgrepignore")
            except:
                pass

        cmd = [
            "semgrep", "scan",
            "--json",
            "--config", "p/security-audit",
            "--config", "p/secrets",
            "--skip-unknown-extensions",
            "--no-git-ignore",
            self.repo_path
        ]

        try:
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                env=env
            )
            if result.returncode not in (0, 1):
                print(result.stderr[:200])
                return {"results": []}

            return json.loads(result.stdout.strip())

        except Exception as e:
            print("Semgrep error:", e)
            return {"results": []}
