from github import Github
from core.config import Config
import time

class GitHubClient:
    def __init__(self):
        self.gh = Github(Config.GH_TOKEN)
        self.user = self.gh.get_user()

    def setup_workspace(self, repo_full_name):
        """
        Forks the repo and creates a unique branch for the fix.
        repo_full_name example: 'OWASP/NodeGoat'
        """
        original_repo = self.gh.get_repo(repo_full_name)
        
        # 1. Fork the repo to the Agent's account
        print(f"🍴 Forking {repo_full_name}...")
        forked_repo = self.user.create_fork(original_repo)
        
        # Wait for GitHub to finish the fork background process
        time.sleep(2) 
        
        # 2. Create a unique branch name
        branch_name = f"security-fix-{int(time.time())}"
        
        # 3. Get the SHA of the main branch to start the new branch
        main_branch = forked_repo.get_branch(forked_repo.default_branch)
        forked_repo.create_git_ref(ref=f"refs/heads/{branch_name}", sha=main_branch.commit.sha)
        
        return forked_repo, branch_name

    def submit_pull_request(self, original_repo_full_name, head_branch, title, body):
        """Opens a PR from the fork back to the original repo."""
        original_repo = self.gh.get_repo(original_repo_full_name)
        pr = original_repo.create_pull(
            title=title,
            body=body,
            base=original_repo.default_branch,
            head=f"{self.user.login}:{head_branch}"
        )
        return pr.html_url