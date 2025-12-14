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

## Content Quality Guidelines

### Language & Length Constraints
- **Language:** English only (Latin characters)
- **Summary:** Max 200 characters
- **Description:** Max 1000 characters (task contexts)
- **Artifact content:** Max 4000 characters (~500-700 words)

### Generalizable Patterns (NOT Specific Details)
✅ **DO store:**
- Patterns and templates applicable to future work
- "Check import statements before running Python scripts"
- "Always validate user input for SQL injection vulnerabilities"
- "Use error handling pattern: try-except with specific exceptions"

❌ **DON'T store:**
- Iteration-specific details: "Fixed bug in iteration 3"
- Personal names or dates: "John updated this on 2024-03-15"
- One-off solutions: "Changed line 42 in user_service.py"
- Project-specific file paths: "Modified /home/user/project/file.py"

### Focus on WHAT & WHY, Not HOW (specifics)
- **Good:** "Always validate API responses before processing to prevent null reference errors"
- **Bad:** "Fixed the bug where response.data was null in the getUserProfile function"

### Keep Content Concise
- Use bullet points and clear structure
- Remove redundant explanations
- Focus on actionable information
- Break long content into multiple artifacts

## Common Mistakes

❌ "I'll check if needed" → Always check first
❌ "Add at end" → Capture immediately
❌ "Too simple for context" → All tasks use workflow
❌ "Just look, don't load" → Must load artifacts
❌ "I know better" → Artifacts contain validated learnings
❌ "Task finished" without reflection → Must call `reflect_and_update_artifacts()` first
❌ "Fixed mistakes" without updating artifacts → Create/update artifacts for each learning
❌ Storing iteration details → Store generalizable patterns only
❌ Non-English content → All content must be in English
❌ Exceeding length limits → Keep summaries <200, content <4000 chars

---