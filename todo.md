# Transplant Medication Adherence - TODO

**Project**: ADK Multi-Agent System on Cloud Run
**Status**: Shipped (Nov 2025 hackathon) — maintenance mode
**Last Updated**: 2026-04-18

## Current State

- All 5 ADK agents shipped: Coordinator, MedicationAdvisor, SymptomMonitor, DrugInteraction, RejectionRisk
- Live: https://missed-dose-service-64rz4skmdq-uc.a.run.app
- 156 tests, 94.8% coverage, SonarCloud gate passing
- 0 open GitHub issues
- Recent activity: dependency bumps (google-adk, pytest, ruff, pre-commit), CI minute optimization

## In Progress 🚧

None

## Pending 📋

### Post-hackathon bonus items (from README)
- [ ] Blog post: technical writeup (+0.4 hackathon bonus — may be moot post-deadline)
- [ ] Social media posts: #CloudRunHackathon (may be moot post-deadline)
- [ ] Demo video: 3-minute walkthrough

### Hardening
- [ ] Decide fate of deprecated `services/gemini_client.py` (legacy Gemini client — delete or document)
- [ ] Review whether `services/missed-dose/services/agents/` (nested copy under missed-dose service) is still needed or can be consolidated with top-level `services/agents/`

### Future enhancements (not scheduled)
- Web/mobile patient dashboard for history tracking
- FHIR EHR integration
- Multi-language support
- Voicebot integration
- ML personalization
- Cloud Run GPU for larger models
- Vertex AI fine-tuning

## Known Issues 🐛

None

## Notes 📝

- Project is in maintenance mode; new work should come from user direction or issues filed post-hackathon
- `services/missed-dose/services/` appears to be a build-time copy (deploy.sh copies agents into the service dir before Docker build) — verify before treating it as source of truth
- main branch is held by sibling worktree at `/home/adam/Code/transplant-gcp-pubsub`; sync via `git fetch` from this worktree rather than `git checkout main`
