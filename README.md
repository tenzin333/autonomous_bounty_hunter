# 🏹 Autonomous Bounty Hunter

An autonomous, multi-agent security system that scans GitHub
repositories for vulnerabilities, generates verified patches, and
secures findings using a **Blockchain Commit-Reveal** scheme.

![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)
![Python: 3.10+](https://img.shields.io/badge/Python-3.10+-blue.svg)
![AI:
Multi-Agent](https://img.shields.io/badge/AI-Agentic_Workflows-purple.svg)
![Blockchain:
Web3/Solidity](https://img.shields.io/badge/Blockchain-Ethereum/Polygon-silver.svg)

------------------------------------------------------------------------

## 🚀 Overview

The **Autonomous Bounty Hunter** is a decentralized security
firm-in-a-box. It automates the end-to-end bug bounty pipeline---from
discovery to patch generation and verifiable credit assignment.

### 🧩 The Problem

Traditional bug bounty workflows suffer from: - Slow triage and delayed
payouts\
- **Bounty sniping** (someone rushes a public fix ahead of the original
finder) - Missing credit due to maintainers forgetting or refusing to
compensate

### 🎯 The Solution

This project solves these issues with: 1. **Autonomous Detection**\
Uses AST + static analysis + LLM triage to find real vulnerabilities. 2.
**Verified Patching**\
Generates minimal, safe, PR-ready fixes to vulnerable repositories. 3.
**Immutable Proof of Discovery**\
A blockchain commit-reveal pattern proves **who found the bug first**,
preventing theft and enabling trust.

------------------------------------------------------------------------

## 🧠 System Architecture

The system is composed of three major layers:

### 1. Multi-Agent Intelligence

-   **Agent A -- The Attacker**\
    Scans repositories using Semgrep & heuristics, sends candidates to
    an LLM for exploitability validation.
-   **Agent B -- The Patcher**\
    Contextualizes the vulnerability and generates a safe, minimal,
    non-breaking fix.

### 2. Trust & Blockchain Layer (Commit-Reveal)

Ensures credit is provable and timestamped. - **Commit:**\
Hash `(repo + file + vuln + salt) → keccak256`, store on-chain before
submitting PR. - **Reveal:**\
After merge, publish raw contents + salt to validate the earlier
commit. - Reputation becomes cryptographically verifiable.

### 3. Cloud Execution + Dashboard

-   **Workers:** Dockerized job runners (Render, Koyeb, Fargate, or
    local cron/systemd)
-   **Database:** PostgreSQL stores active hunts + salts + commits
-   **UI:** Streamlit dashboard for visibility into hunts, PRs, and
    on-chain verification

------------------------------------------------------------------------

## 🛠️ Tech Stack

**Core:**\
Python 3.10+, AsyncIO

**Security & Detection:**\
Semgrep, AST scanning

**AI Models:**\
- GPT-4o, GPT-4o mini (default) - Pluggable support for Gemini &
open-source LLMs

**Blockchain:**\
Web3.py, Solidity Smart Contract\
Tested on **Polygon Amoy Testnet**

**Database:**\
PostgreSQL (Aiven, Neon, Supabase)

**Frontend:**\
Streamlit UI dashboard

**Deployment:**\
Docker, GitHub Actions, crontab/Systemd/Task Scheduler

------------------------------------------------------------------------

## 📦 Installation & Setup

### 🔑 Prerequisites

You'll need: - Python **3.10+** - An LLM API key (OpenAI, Google,
etc.) - GitHub Personal Access Token (with `repo` scope) - Ethereum
private key with testnet funds - Access to a Polygon Amoy RPC

------------------------------------------------------------------------

### 1️⃣ Clone the Repository

``` bash
git clone https://github.com/tenzin333/autonomous_bounty_hunter.git
cd autonomous_bounty_hunter
```

### 2️⃣ Create & Activate a Virtual Environment

``` bash
python -m venv venv
source venv/bin/activate      # Windows: venv\Scripts\activate
```

### 3️⃣ Install Dependencies

``` bash
pip install -r requirements.txt
```

### 4️⃣ Create a `.env` File

``` env
OPENAI_API_KEY=your_openai_key
GH_TOKEN=your_github_token
AGENT_PRIVATE_KEY=your_wallet_private_key
RPC_URL=https://polygon-amoy.infura.io/v3/<project_id>
CONTRACT_ADDRESS=0xd22
BOUNTY_HUB_ABI=./abis/BountyHub.json
COMMITMENT_SALT=sfgsdfg
AGENT_PRIVATE_KEY=adsfdfsd

# Model Selection
TRIAGE_MODEL=llama-3.1-8b-instant
PATCHER_MODEL=meta-llama/llama-4-scout-17b-16e-instruct

# LLM 
LLM_BASE_URL=https://api.groq.com/openai/v1
LLM_API_KEY=gsk_your_key

# Runtime Mode
ENVIRONMENT=development/production

# PostgreSQL
DB_URL=postgres://user:pass@host:port/defaultdb?sslmode=require

# Target Repo
TARGET_REPO=tenzin333/jobpilot2.0

```

------------------------------------------------------------------------

## 📊 Dashboard & Monitoring

Launch dashboard locally:

``` bash
streamlit run dashboard.py
```

Monitor: - Live scanning - PR states (open/merged/closed) - Commit +
reveal status - Reputation growth

------------------------------------------------------------------------

## 🛡 Ethics & Responsible Use

This system is built for **white-hat security research** and authorized
bounty programs. - Operates only on public repositories - Ensures
discoverer receives provable credit - Prevents exploit hoarding and code
theft

Do **not** run on unauthorized or private systems.

------------------------------------------------------------------------

## 📄 License

Distributed under the MIT License.\
See `LICENSE` for more information.

------------------------------------------------------------------------

## 🙌 Contributing

Ideas & PRs welcome!\
Future work: - Distributed agent swarms - Automated CVE publication -
Tokenized on-chain reputation

------------------------------------------------------------------------

## ⭐ Support

Star the repo and fuel the next generation of autonomous hunters. 🔐
