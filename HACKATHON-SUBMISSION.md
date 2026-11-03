# Bee-Muse · Meta AI Developer Hackathon — submission evidence and final checklist

> **Status: DRAFT — NOT SUBMITTED.** Prepared 2026-11-02 from repository source, CI, `PLAN-HACKATON.md`, `HANDOFF.md` and `VALIDATION.md`. This file is a reversible addition; it does not certify a recorded video, public repository, physical Android demo or completed application.

## Submission snapshot

- Project: **iArtLabs · Bee-Muse**
- Repository: https://github.com/ART449/bee-muse (**private at the latest inspection; change visibility only after the complete source/history/security review**).
- Provisional application choices, to confirm in the existing form: **Indie Developer Track** and **Build for Your World**.
- Deadline recorded from the participant's official materials: **Wednesday 2026-11-04, 20:00 Aguascalientes, México**.
- Existing release: **0.5.0**. Windows x64, Linux x64, Mac Apple Silicon and a separate native Android debug APK are documented; **compilation success is not proof of physical interaction**.
- Primary handoff: `PLAN-HACKATON.md`, `HANDOFF.md`, `VALIDATION.md`.
- Do **not** reload the open submission tab until its draft answers are copied out; saved-draft persistence was not confirmed.

## Copy-ready English submission drafts

### Project summary / what are you building?

Bee-Muse is an AI-assisted local workspace for finding, inspecting and organizing files, and performing user-approved actions through reusable tools. It combines a local index and version-aware library, a conversation interface backed by Muse Code, a tool interface other agents can query, and desktop and Android clients. The goal is to give a person and their AI assistants one clear, permission-scoped path from a natural-language request to a verifiable result, while keeping personal library data out of the public repository.

### How does it use Meta technology?

Bee-Muse connects to Muse Code for Meta-backed language-model interactions, using the account's own authorized session. The service integration selects the `muse-wonder-1.0` model in `service/muse_bridge.py`. It also calls Muse's voice-transcription capability: a real synthetic WAV was transcribed through the compiled Windows backend. This is **speech-to-text**; spoken output in Bee-Muse uses the device/system voice, not Meta TTS. Local indexing, file tools and approval boundaries are Bee-Muse components; unverified future features are not presented as deployed Meta integrations.

### Why is Meta important to the project?

Meta-backed conversation helps turn a human request into a concrete, inspectable workflow, and Meta voice transcription provides an optional spoken-input path. Bee-Muse keeps the underlying local file tools reusable independently of the selected model, making it possible to inspect what an assistant requested and what the tool returned.

### Prior work versus hackathon work

**Recovered foundation:** Commit `f50750b` records a recovered Bee-Muse code baseline on 2026-11-02; that commit date **does not establish that the foundation was originally created during the event**. Do not claim the entire product was newly built for this hackathon.

**Changes versioned after the recovery:** `d85ecf1` (Muse conversations, workspace tools, MCP), `2b8daff` (native Android and HTTPS pairing gateway), `ac8c274` (native Android device features), `ab46c9b` (isolated desktop browser), `db5e46e` (Windows voice decoder fix), `5807c65` (portable release archives). These commits show repository changes; attribution to the exact event window must still be checked against event start and earlier material.

**Not yet verified end-to-end:** Facebook/Firebase OAuth; complete Muse → INBEEBOX → device action loop; actual Pixel assistant/gestures/notifications; device HTTPS pairing; physical microphone; visual SAM/OCR understanding; continuation across the entire large index; correct BeeCode/OpenCode integration. Mention these as roadmap, not finished deliverables.

### Team / creator

iArtLabs, led by Art, an independent developer in Mexico. **Confirm Felipe's exact role and whether to add him to the team before submission**. Do not manufacture names, employment, a project team size or a personal experience survey answer.

## Video: 180-second capture plan (not recorded)

Use **only synthetic test data** and the **Bee-Muse 0.5.0** executable. Close the identified old portable window before opening the new version; do not terminate unrelated Electron helpers. Do not display personal files, sessions, API keys, browser tokens or Windows account details.

| Time | What to show | Honest evidence standard |
| --- | --- | --- |
| 00:00–00:20 | Problem, project and scope | Introduce the goal, not unsupported outcomes |
| 00:20–00:50 | Local library and file search | Find a synthetic HTML or other indexed item |
| 00:50–01:25 | Muse requesting an authorized tool action | Show the actual result; if the workflow fails, do not use it as a completed demo |
| 01:25–01:55 | Meta model / speech-to-text integration | Record a real call if working; otherwise show appropriately labeled recorded evidence |
| 01:55–02:25 | Desktop, cross-platform artifacts and native Android | Distinguish built APK from physical-device testing |
| 02:25–03:00 | Changes built during event and conclusion | Show commit timeline with base vs subsequent work |

Expected capture destination on participant's machine: `I:\Bee-Muse\2026-11-02\hackathon-video\`. Confirm the recording plays, lasts no more than three minutes if required, contains legible text and has a publicly accessible URL before inserting it into the form.

## Go/no-go publication gate

- [ ] Run a full secret scan over **all Git objects/history**, not only the current tree. Inspect screenshots, documentation, commits, configuration, embedded asset metadata and binary artifacts for credentials, private files, tokens, internal addresses and licenses. `.gitignore` alone does not sanitize Git history.
- [ ] Confirm no credentials are embedded in Android assets, Electron bundles or release packages. Keep the Meta key in the protected Windows credential environment: do not print or copy it into logs, Git, forms, video or chat. OpenCode configuration references the environment; it must not contain a literal key.
- [ ] Validate repository history, release provenance, licenses and any third-party artwork/assets before publishing.
- [ ] Make repository public **only after passing** the gate; recheck from a logged-out browser.
- [ ] Capture and verify the three-minute video; publish an accessible link.
- [ ] Complete team details, video recording questions and personal experience questionnaire using the participant's real answers.
- [ ] Review the promotional-use consent and get the participant's explicit agreement before accepting it or pressing Submit.
- [ ] Submit before the deadline; retain the confirmation screen/email and final links.

## Other work is lower priority

Disk C recovery is separate from the hackathon. Existing moves to F: were checksum-verified but did not recover the requested 500 GB. BeeCode finished its prior run; it is not cleaning in the background. Resume only after the submission, using the existing inventory with scoped permissions, **free models only, no paid subagents**, and copy/hash verification before removing original files.

## Verification references

- `PLAN-HACKATON.md`, `HANDOFF.md`, `VALIDATION.md`, `META.md`.
- Desktop CI: https://github.com/ART449/bee-muse/actions/runs/41514484719
- Android CI: https://github.com/ART449/bee-muse/actions/runs/41512152076
- Event details: https://cerebralvalley.ai/e/meta-ai-developer-hackathon/details
- Submission: https://cerebralvalley.ai/e/meta-ai-developer-hackathon/hackathon/submit
