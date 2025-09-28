# Development Task Implementation Rules

AI agent MUST follow ALL the next rules and processes when implementing ANY development task.

**CRITICAL VIOLATION CONSEQUENCES**: If any rule is violated, the agent MUST immediately stop, acknowledge the violation, and restart the process from the beginning following all rules strictly.

## ⚠️ VIOLATION PREVENTION SAFEGUARDS ⚠️

**BEFORE ANY ACTION, AI AGENT MUST:**
1. **ALWAYS START** every response with: "Reading mandatory rules..." and call `mcp_repomix_file_system_read_file` to read `docs/dev-task-rules.md`
2. **EXPLICITLY CONFIRM** which step number is being worked on by stating: "Currently working on Step X from the plan"
3. **REFUSE** to implement multiple steps if user asks - respond: "I can only implement ONE step at a time per the rules"
4. **NEVER CONTINUE** to next step without explicit user permission - always end with: "Step X complete. May I proceed to Step Y?"

## Preparation Process

1. Use `mcp_repomix_pack_codebase` tool to create a basic project analysis. Use `mcp_repomix_read_repomix_output`, `mcp_repomix_file_system_read_file` and `mcp_repomix_grep_repomix_output` to extract relevant information for task implementation.
2. Split the task implementation into a list of small finalized steps that can be individually tested and validated.
3. Save the list of steps in new md file `<TASK_NAME>-dev-plan.md` in `/docs/tasks/` directory with the following structure:
   ```
   # <TASK_NAME> Development Plan

   ## Overview
   Description of the task

   ## Steps

   ### Step 1
   Status: pending
   Description: [step 1 description]
   Result: TBD

   ### Step 2
   Status: pending
   Description: [step 2 description]
   Result: TBD
   ...
   ```

## Step Implementation Process

AI-agent MUST repeat this EXACT process for EVERY SINGLE step in `<TASK_NAME>-dev-plan.md` document. 

**CRITICAL: NO step can be marked as `completed` without passing tests!**

### For EACH step (one at a time):

**🚫 CRITICAL CHECKPOINT: AI MUST ANNOUNCE EACH MANDATORY ACTION**

1. **MANDATORY**: State "📖 Reading rules..." then read file `docs/dev-task-rules.md` with `mcp_repomix_file_system_read_file`.
2. **MANDATORY**: State "📋 Reading plan..." then read file `docs/tasks/<TASK_NAME>-dev-plan.md` with `mcp_repomix_file_system_read_file`.
3. **MANDATORY**: State "🔍 Creating fresh analysis..." then use `mcp_repomix_pack_codebase` tool to create fresh project analysis.
4. **MANDATORY**: State "🎯 Identifying pending step..." then find and identify the FIRST step with status `pending` and announce: "Working on Step X: [description]"
5. **MANDATORY**: State "⚙️ Implementing ONLY this step..." then implement ONLY that one step completely. **FORBIDDEN**: Starting any other step.
6. **MANDATORY**: State "🧪 Running tests for this step..." then create and run tests to validate the step implementation.
7. **MANDATORY**: State "🔬 Running complete test suite..." then run COMPLETE test suite: `uv run pytest tests/`
8. **MANDATORY**: State "🔧 Fixing any failures..." then fix implementation until ALL tests pass (100% success).
9. **MANDATORY**: State "✅ Updating step status..." then update step status to `completed` and add result.
10. **MANDATORY**: State "⏸️ STOPPING - requesting permission..." then STOP and ask: "Step X complete. May I proceed to Step Y?"

**🔒 ENFORCEMENT: Each numbered action MUST be announced before execution**

### 🚨 ENHANCED ENFORCEMENT RULES 🚨

- **NEVER skip testing**: Every code change MUST be validated with tests before marking step as completed
- **ZERO TOLERANCE for failing tests**: ANY failing test (new OR existing) = step NOT complete
- **ONE step at a time**: Never implement multiple steps simultaneously  
- **STOP after each step**: Always pause and ask user before proceeding to next step
- **FRESH analysis**: Always run new codebase analysis before each step
- **MANDATORY reads**: Always re-read rules and plan before each step
- **FIX OR REVERT**: If existing tests break, either fix the issue or revert changes entirely

**🔐 ADDITIONAL SAFEGUARDS AGAINST VIOLATIONS:**
- **FORBIDDEN PHRASES**: AI cannot say "Step X completed" without running tests first
- **REQUIRED CONFIRMATIONS**: AI must ask "All tests passing?" before marking step complete
- **MANDATORY STOPS**: AI must end each step with explicit permission request
- **PLAN UPDATES**: AI must update the `<TASK_NAME>-dev-plan.md` file for each completed step
- **NO SHORTCUTS**: AI cannot skip any of the 10 mandatory actions, even if "obvious"
- **USER OVERRIDE PROTECTION**: Even if user says "continue to next step", AI must still ask permission explicitly

## Quality Assurance Checklist

Before marking ANY step as `completed`, verify ALL of these:

### Code Quality:
- [ ] All lint errors are resolved (use `get_errors` tool)
- [ ] All type hints are correct
- [ ] Code follows project patterns and conventions
- [ ] All imports are properly organized

### Testing Requirements:
- [ ] **CRITICAL: ALL existing tests MUST pass 100% (0 failures allowed)**
- [ ] New functionality has test coverage
- [ ] Edge cases are tested  
- [ ] All test files execute without errors
- [ ] If ANY existing test fails, implementation MUST be fixed or reverted
- [ ] Run complete test suite: `uv run pytest tests/`

### Documentation:
- [ ] Code changes are properly documented
- [ ] Docstrings are updated if function signatures changed
- [ ] Step result includes specific details of what was implemented

### Integration:
- [ ] Changes don't break existing functionality
- [ ] All related interfaces/contracts are updated
- [ ] Dependencies are properly handled

**FAILURE TO MEET ANY CHECKLIST ITEM = STEP NOT COMPLETE**

## 🛡️ VIOLATION DETECTION & RECOVERY 🛡️

### Common Violations to Watch For:
1. **Skipping mandatory reads** - AI tries to implement without reading rules/plan
2. **Multiple step implementation** - AI implements several steps at once 
3. **Missing test validation** - AI marks step complete without running tests
4. **No permission requests** - AI continues to next step without asking
5. **Missing announcements** - AI performs actions without stating them

### Recovery Protocol:
1. **IMMEDIATE STOP** when violation is detected
2. **ACKNOWLEDGE** the specific violation  
3. **REVERT** any changes made during violated process
4. **RESTART** from Step 1 with proper process
5. **DOCUMENT** the violation in plan file under "Violations Log"

### Violation Prevention Triggers:
- **Before each action**: AI must announce what it's doing
- **Before marking complete**: AI must confirm "All tests passing - 100% success rate"  
- **Before next step**: AI must ask "May I proceed to next step?"
- **After each step**: AI must update plan file with results

**⚠️ ZERO TOLERANCE POLICY: ANY violation = FULL PROCESS RESTART ⚠️**
