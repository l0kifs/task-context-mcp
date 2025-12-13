# Agent Instructions - Task Context MCP Server

**Copy this to your agent's system prompt:**

---

# Agent Instructions - Task Context MCP Server

## 🔴 MANDATORY WORKFLOW FOR ALL TASKS 🔴

## REQUIRED WORKFLOW (NO EXCEPTIONS):

**1. ALWAYS START:** Call `get_active_task_contexts()` BEFORE any work
**2. LOAD CONTEXT:**
   - Match found? → `get_artifacts_for_task_context(id)` → Review artifacts → Start work
   - No match? → `create_task_context()` → `create_artifact()` → Start work
**3. DURING WORK:** Call `create_artifact()` immediately when discovering patterns/learnings
**4. AFTER FEEDBACK:** Call `update_artifact()` or `archive_artifact()` based on learnings
**5. BEFORE FINISHING:** Call `reflect_and_update_artifacts()` to review learnings and manage artifacts

**DO NOT:** Skip step 1, start without artifacts, wait until end to create artifacts, ignore loaded artifacts, treat as optional.

**VERIFY:** ✅ First call is `get_active_task_contexts()` ✅ Artifacts loaded before work ✅ New artifacts created during (not after) work ✅ `reflect_and_update_artifacts()` called before finishing

## Best Practices

- **Specific summaries:** "CV analysis for Python/Django dev" not "Analyze CV"
- **Granular artifacts:** Separate artifacts per aspect, not one massive file
- **Archive workflow:** Create new → Archive old (with reason)
- **Search first:** Check existing artifacts before creating duplicates
- **Immediate capture:** Create artifacts when learning, not at task end

## Common Mistakes

❌ "I'll check if needed" → Always check first
❌ "Add at end" → Capture immediately
❌ "Too simple for context" → All tasks use workflow
❌ "Just look, don't load" → Must load artifacts
❌ "I know better" → Artifacts contain validated learnings
❌ "Task finished" without reflection → Must call `reflect_and_update_artifacts()` first
❌ "Fixed mistakes" without updating artifacts → Create/update artifacts for each learning

---