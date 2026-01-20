# 🛡️ Autonomous Bounty Hunter

**Autonomous Bounty Hunter** is an AI-driven security automation system designed to scan GitHub repositories for vulnerabilities, validate findings using AI, apply verified patches, and submit professional pull requests with cryptographic, on-chain attestations for every confirmed fix.

---

## 🚀 Project Overview

The **Autonomous Bounty Hunter** automates the process of discovering, validating, and remediating vulnerabilities in GitHub repositories. Key features include:

1. **Clones a target GitHub repository** for scanning.
2. **Scans the codebase** using **Semgrep** for known security issues.
3. **Validates findings** using an **AI attacker agent** to confirm real vulnerabilities.
4. **Generates secure patches** to fix the identified vulnerabilities.
5. **Re-verifies fixes** by performing regression scanning to ensure no new issues are introduced.
6. **Pushes changes** and opens a professional **pull request** to the original repository.
7. **Logs verified findings on-chain** for a tamper-proof proof-of-work.
8. **Executes an on-chain bounty claim** to ensure that identified vulnerabilities are rewarded.

A lightweight **Flask server** is included to perform health checks and support containerized or local deployments.

---

## 💡 Why This Project Is Useful

- **AI-powered vulnerability validation** ensures high accuracy in identifying real issues.
- **Fully automated remediation workflow** reduces manual effort and error-prone tasks.
- **GitHub-native pull request automation** ensures seamless integration with existing workflows.
- **Post-patch verification** ensures patches do not introduce new issues.
- **Blockchain-backed audit trail** provides a tamper-proof record of all actions, from vulnerability discovery to bounty claims.
- **Automated bounty claiming** simplifies the process of earning rewards for identifying vulnerabilities.
- **Cloud-friendly architecture** supports long-running deployments and scalability.

---

## 🧰 Getting Started

### Prerequisites

Before you can run **Autonomous Bounty Hunter**, ensure you have the following prerequisites installed:

#### System & Tooling

- **Python 3.9+**
- **Git**
- **Semgrep**: Install via `pip install semgrep`
- **GitHub account** and **access token** for repo access

#### Blockchain Environment (Required)

This project requires an **Ethereum-compatible blockchain** to log findings and claim bounties.

For local development, we recommend using **Foundry** for blockchain deployment:

- **Foundry**
  - `anvil` — Local Ethereum node
  - `forge` — Smart contract deployment & interaction

To install Foundry:

```bash
curl -L https://foundry.paradigm.xyz | bash
foundryup
```

#### Configuration

Set up the following environment variables:

```bash
TARGET_REPO=owner/repo
GITHUB_TOKEN=ghp_xxx
RPC_URL=http://127.0.0.1:8545
PRIVATE_KEY=0x...
CONTRACT_ADDRESS=0x...
ABI_PATH=onchain/abi/Contract.json
TRIAGE_MODEL=llama-3.1-8b-instant
PATCHER_MODEL=meta-llama/llama-4-scout-17b-16e-instruct
OPENAI_API_KEY=0x...
GH_TOKEN=github_0x...
COMMITMENT_SALT=ax...
ABI_PATH=./out/BountyBoard.sol/BountyBoard.json
DATABASE_URL=postgres://username:password@bounty-hunter-service-bounty-hunter-c5ed.e.aivencloud.com:24036/defaultdb?sslmode=require
LLM_BASE_URL=https://api.groq.com/openai/v1
LLM_API_KEY=gsk_0x...
```

### Running the Hunter

We recommend using the **entrypoint script** for automatic setup and execution. It will:

- Start a local **Anvil** node on `127.0.0.1:8545`.
- Deploy the **BountyBoard** smart contract using **Forge**.
- Launch the **Autonomous Bounty Hunter agent** (`main.py`).
- Execute an on-chain **bounty claim** via `strike_bounty.py`.
- Keep the process running while the agent performs its tasks.

To run the entrypoint script, execute:

```bash
bash entrypoint.sh
```

> ⚠️ **Blockchain infrastructure is mandatory**. The hunter and bounty claim functionality will not work without a deployed contract.

---

## 🧱 Architecture Overview

The project is organized into the following key components:

- **core/**: Contains scanning logic, GitHub automation, configuration, and database management.
- **agents/**: Includes the attacker and patcher AI agents that identify vulnerabilities and generate patches.
- **onchain/**:
  - **contracts/**: Smart contracts used for logging findings and claiming bounties.
  - **script/**: Scripts for interacting with the blockchain (logging, claiming).
- **entrypoint.sh**: Bootstraps the blockchain environment, deploys the smart contract, and starts the bounty hunter agent.
- **main.py**: The orchestration entry point that manages the entire bounty hunting process.

---

## 🆘 Support

- **GitHub Issues**: For reporting bugs or requesting new features.
- **Review PRs carefully**: Always ensure automated pull requests are reviewed before merging into production.

---

## 👥 Contributing

We welcome contributions! Please see `docs/CONTRIBUTING.md` for guidelines on how to contribute to the project.

---

## 📌 Disclaimer

While the fixes are automated, **manual review** of the proposed pull requests is **required** before deploying to production. Ensure all changes are thoroughly vetted.
```

---