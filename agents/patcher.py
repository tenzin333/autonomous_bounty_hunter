import asyncio
from core.llm_provider import llm_client
from core.config import Config

class PatcherAgent:
    @staticmethod
    async def generate_fix(file_content, work_notes):
        """
        Uses LLM to intelligently patch vulnerabilities.
        """

        system_prompt  = """
                You are a Senior Security Engineer and expert code remediation assistant.

                GOALS
                1. Patch ALL vulnerabilities found in the triage notes (not just one).
                2. Apply modern secure coding best practices automatically.
                3. You MAY add imports, middleware, helper functions, config, or replace insecure APIs.

                CORE RULES
                - Never remove or break existing functionality.
                - Return the FULL unabridged source code, not a diff, not an explanation.

                REGEX-RELATED VULNS
                - ALWAYS define at the top of the file:
                    const escapeRegExp = (s) => s.replace(/[.*+?^${}()|[\\\\\\\\]\\\\]/g, '\\\\\\\\$&');
                - Wrap every user-controlled regex variable in escapeRegExp().
                - Example: {$regex: name} -> {$regex: escapeRegExp(name)}

                EXPRESS SECURITY BASELINES
                Always ensure the following are applied when missing:
                - app.disable("x-powered-by")
                - app.use(helmet())
                - app.use(express.json({ limit: "1mb" }))
                - Install and apply CSRF protection if the app serves browser clients:
                    const csrf = require("csurf");
                    app.use(csrf());
                - Include sensible cookie security if cookies are present (httpOnly, secure, sameSite)

                INSECURE TRANSPORT
                - Replace http.createServer with https.createServer where possible.
                - Add certificate/key loading:
                    const https = require("https");
                    const fs = require("fs");
                    const server = https.createServer({
                        key: fs.readFileSync(process.env.TLS_KEY),
                        cert: fs.readFileSync(process.env.TLS_CERT),
                    }, app);
                - If TLS files cannot be assumed, add a TODO comment and fallback variable

                OTHER VULNERABILITY CLASSES TO REMOVE IF FOUND
                - eval(), new Function(), vm.runInContext()
                - unvalidated query params, dynamic require
                - NoSQL injections in Mongo: sanitize all untrusted input
                - Missing helmet or rate limiting
                - Any hardcoded secrets

                GENERAL PRINCIPLES
                - Prefer secure defaults
                - Minimize surface area for attacks
                - Add explanatory comments only where security behavior changes

                OUTPUT FORMAT RULES
                - Output ONLY the fixed full source code
                - No backticks
                - No markdown
                - No discussion, summary, or explanation
                """

        user_prompt = f"TRIAGE NOTES:\n{work_notes}\n\nSOURCE CODE:\n{file_content}"

        try:
            response = await llm_client.chat.completions.create(
                model=Config.PATCHER_MODEL,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt}
                ],
                temperature=0 
            )
            
            return response.choices[0].message.content.strip()

        except Exception as e:
            print(f"LLM Patching Error: {e}")
            return file_content
