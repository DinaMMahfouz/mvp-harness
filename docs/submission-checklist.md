# HARNESS — Submission Checklist

- [ ] Clear problem statement (AI apps may look fine but fail under adversarial/edge conditions; builders don't know if they're ready to ship)
- [ ] Clear target user (AI/Applied AI/GenAI engineers, RAG/Agent/MCP developers)
- [ ] Clear solution (deterministic release-readiness decision, not just a vulnerability count)
- [ ] 3 core features connected end-to-end (registry, assurance+findings, harden/retest/release-decision)
- [ ] Small, intentional MVP scope (no feature bloat)
- [ ] Built with Claude Code using subagents (not single-shot)
- [ ] Iterative agent-team decisions documented (docs/agent-team-decision-log.md)
- [ ] Main flow works end to end (register → test → find → fix → retest → decision)
- [ ] Data persists (Supabase Postgres, no hardcoded demo numbers)
- [ ] Testing of main workflow documented
- [ ] At least one real defect found by QA, fixed, and retested (documented)
- [ ] Not a static landing page or fake dashboard
- [ ] Shareable, deployed MVP link (Vercel frontend + Render backend)
- [ ] V2 roadmap documented
- [ ] GitHub repo clean (https://github.com/DinaMMahfouz/mvp-harness.git, main)
- [ ] No secrets committed (secret scan clean)
- [ ] n8n automation works end to end (real webhook, real email, signed callback)
