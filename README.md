# 🤖 Autonomous Bounty Hunter (ABH)
**A Multi-Agent System for Autonomous Bug Detection, Patching, and Web3 Settlement.**

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![AWS Fargate](https://img.shields.io/badge/Infrastructure-AWS%20Fargate-orange)](https://aws.amazon.com/fargate/)
[![OpenAI](https://img.shields.io/badge/AI-GPT--4o-blue)](https://openai.com/)
[![Solidity](https://img.shields.io/badge/Blockchain-Solidity-black)](https://soliditylang.org/)

## 🌟 Overview
The **Autonomous Bounty Hunter** is a self-operating security firm. It automates the entire lifecycle of a bug bounty: from scanning public repositories for vulnerabilities to writing functional patches and receiving crypto-payments via smart contracts upon successful merge.

### 🏗 Architecture
The system utilizes a **Stateful Multi-Agent Workflow** orchestrated via Python, deploying specialized agents for "Red Team" (Attacker) and "Blue Team" (Patcher) responsibilities.



## 🧠 The Agentic Workflow
1.  **Agent A (The Attacker):** - Executes a full-repo scan using **Semgrep** and **TruffleHog**.
    - Triages results using **GPT-4o-mini** to eliminate false positives.
    - Prioritizes targets based on severity (Critical/High).
2.  **Agent B (The Patcher):** - Ingests the vulnerability context.
    - Generates a surgical fix using **GPT-4o**.
    - Automates a GitHub **Fork -> Branch -> Pull Request** flow.
3.  **The Judge (Smart Contract):** - Holds bounty funds in escrow on **Polygon/Base**.
    - Releases funds to the Hunter's wallet automatically when the PR is merged.

## 🛠 Tech Stack
- **AI/Orchestration:** LangGraph, OpenAI SDK, Semgrep.
- **Backend:** Python 3.11, PyGithub, FastAPI.
- **Infrastructure:** AWS Fargate (Spot Instances), SQS, Supabase.
- **Web3:** Solidity, Ethers.js, Alchemy (RPC Provider).
- **Frontend:** Next.js 14, TailwindCSS, Shadcn/UI.

## 🚀 Getting Started

### Prerequisites
- Python 3.10+
- Docker
- OpenAI API Key & GitHub PAT (Personal Access Token)

### Installation
1. **Clone the repo:**
   ```bash
   git clone [https://github.com/your-username/autonomous-bounty-hunter.git](https://github.com/your-username/autonomous-bounty-hunter.git)
   cd autonomous-bounty-hunter

2. **Configure Environment: Create a .env file (see .env.example):**
    TRIAGE_MODEL=gpt-4o-mini
    PATCHER_MODEL=gpt-4o
    GITHUB_TOKEN=your_token
    OPENAI_API_KEY=your_key

3.  **Deploy the Smart Contract:**
    cd contracts
    npx hardhat run scripts/deploy.js --network polygon_mumbai

4. **Run the Hunter:**
    python main.py --repo [https://github.com/target/repo](https://github.com/target/repo)

## 🛡️ Security & Safety
   - **Sandbox Execution:** Agent-generated patches are validated in ephemeral Docker containers to prevent regression or malicious code execution.
   - **Style-Aware Patching:** Patcher agent analyzes `.eslintrc` or `pyproject.toml` to ensure fixes pass CI/CD linting.
   - **Human-in-the-Loop:** Optional dashboard toggle to manually approve PRs before submission to maintain high-quality PR history.


**Created by Tenzin Thilay** [LinkedIn](https://linkedin.com/in/ytenthinlay1) | [Portfolio](tenzinthinlay.netlify.app) | [GitHub](https://github.com/tenzin333)