import subprocess
import json
import os

class Scanner:
    def __init__(self, repo_path):
        self.repo_path = os.path.abspath(repo_path)

    def run_semgrep(self):
        print(f"Scanning repository: {self.repo_path}")

        env = os.environ.copy()
        env["PYTHONUTF8"] = "1"

        # Remove ignore files to ensure full visibility for the audit
        ignore = os.path.join(self.repo_path, ".semgrepignore")
        if os.path.exists(ignore):
            try:
                os.remove(ignore)
                print("Removed .semgrepignore for full audit visibility")
            except Exception as e:
                print(f"Warning: Could not remove .semgrepignore: {e}")

        # Core Security Configs:
        # p/security-audit: Deep dive into potential vulnerabilities
        # p/default: General security best practices
        # p/javascript: Language-specific rules for Node/JS (ReDoS, Taint)
        # p/secrets: Looking for hardcoded credentials
        cmd = [
            "semgrep", "scan",
            "--json",
            # 'p/security-audit' is a great catch-all for deep analysis
            "--config", "p/security-audit", 
            # 'p/secrets' for hardcoded keys (cross-language)
            "--config", "p/secrets",
            # 'p/default' automatically selects rules based on file extension
            "--config", "p/default",
            "--skip-unknown-extensions",
            "--no-git-ignore",
            self.repo_path
        ]

        try:
            # Setting a timeout to prevent hanging on massive repositories
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                env=env,
                timeout=300 
            )

            # Semgrep exit codes: 0 (no findings), 1 (findings found)
            # Anything else is usually a crash/error
            if result.returncode not in (0, 1):
                print(f"Semgrep Error Output: {result.stderr[:500]}")
                return {"results": []}

            output = result.stdout.strip()
            if not output:
                return {"results": []}

            return json.loads(output)

        except subprocess.TimeoutExpired:
            print("Error: Semgrep scan timed out.")
            return {"results": []}
        except json.JSONDecodeError:
            print("Error: Failed to parse Semgrep JSON output.")
            return {"results": []}
        except Exception as e:
            print(f"Unexpected Scanner Error: {e}")
            return {"results": []}