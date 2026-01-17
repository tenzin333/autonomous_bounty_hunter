from core.hunterDB import HunterDB

try:
    db = HunterDB()
    print("Connecting...")
    db.save_commitment(
        repo="test/repo",
        file="test.js",
        vuln="test-vuln",
        salt="123",
        commit_hash="0xTEST",
        pr_url="http://test.com"
    )
    print("✅ Save call finished. Check your cloud dashboard now!")
except Exception as e:
    print(f"❌ Connection failed: {e}")
