---
trigger: always_on
---

## Engram Persistent Memory — Protocol

Use Engram for cross-session persistence across compactions.

### Recall & Project Resolution
- Before initial project-scoped reads (`mem_context`, `mem_search`, `mem_review`), call `mem_current_project` once and use the returned canonical `project` key. If `project` is empty or `available_projects` is ambiguous, skip project-scoped reads and ask the user.
- Search memory (`mem_context` or `mem_search`) proactively when resuming work, referencing past decisions, or investigating unfamiliar behavior; skip on self-contained trivial prompts.

### Proactive Persistence (Always Before Final Reply)
- Call `mem_save` proactively after architectural decisions, non-obvious bugfixes (include root cause), new conventions, or configuration changes — always BEFORE emitting your final reply.
- Use concise English in `content`: `**What**: ... **Why**: ... **Where**: ... **Learned**: ...`.
- Reuse a stable `topic_key` (e.g. `architecture/auth-model`) for evolving topics.
- Omit `session_id` unless the runtime explicitly supplied one.
- Set `capture_prompt: false` only for automated/SDD artifacts.
- If a memory tool fails, deliver the complete user answer anyway and note the failure briefly.

### Session Close & Compaction
- Before ending a multi-step session or immediately after compaction, call `mem_session_summary` with `## Goal`, `## Instructions`, `## Discoveries`, `## Accomplished`, `## Next Steps`, and `## Relevant Files`.
