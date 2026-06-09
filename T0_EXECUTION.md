T0 execution document

Scope:
- Fix five T0 code/documentation issues requested by the user.
- Use external coding agent for all code/document changes.
- Verify with shell commands after the external agent finishes.

Execution sequence:
1. Create tasks.md with the complete 18 coding rules and exact T0 task list.
2. Run opencode against tasks.md.
3. Verify:
   - design.md port references and chapter 12 gap data.
   - duplicate underscore directories are removed.
   - cloud/app router modules are under cloud/app/routers and app_setup.py imports match.
   - all listed FastAPI main.py files define openapi_tags.
4. Report changed files, verification results, and any residual issues.

Telegram/MEDIA note:
- This local Codex environment does not expose a Telegram or MEDIA sending tool.
- The execution document and tasks.md are created in the workspace instead.
