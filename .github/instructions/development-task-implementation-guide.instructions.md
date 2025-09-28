---
applyTo: '**'
---
# Development Task Implementation Guide

**UPDATED: 2025-09-28 - ENHANCED ENFORCEMENT MEASURES ADDED TO PREVENT CONTINUOUS EXECUTION VIOLATIONS**
**MANDATORY COMPLIANCE:** AI agents MUST strictly follow each rule in this guide when performing any task related to creating or updating project functionality. These requirements apply to any tasks related to development and testing within the project. **VIOLATIONS WILL RESULT IN IMMEDIATE TERMINATION OF TASK EXECUTION AND REQUIRE USER APPROVAL FOR RESUMPTION.** **CRITICAL WARNING: FAILURE TO STOP AFTER EACH STEP AND WAIT FOR USER APPROVAL CONSTITUTES A SEVERE VIOLATION THAT WILL RESULT IN COMPLETE TASK ABORTION.** **CRITICAL WARNING: FAILURE TO STOP AFTER EACH STEP AND WAIT FOR USER APPROVAL CONSTITUTES A SEVERE VIOLATION THAT WILL RESULT IN COMPLETE TASK ABORTION.**

**CRITICAL PRE-CONDITION:** Before starting ANY development task, AI agents MUST perform a self-check:
- Have I been assigned a development task by the user?
- Is this task related to creating or updating project functionality?
- If YES to both: I MUST follow this guide completely. If NO: I may proceed normally.

## Task Execution Protocol

When a new task is assigned to you, follow these steps in STRICT ORDER:

1. **MANDATORY PROJECT ANALYSIS:** Use `mcp_repomix_pack_codebase` tool to create a complete project analysis. Do NOT read individual files or use any other tools before this step.
2. **MANDATORY PLANNING:** Split the task implementation into a list of small finalized steps that can be individually tested and validated.
3. **MANDATORY PLAN DOCUMENTATION:** Save the list of steps in new md file `<TASK_NAME>-dev-plan.md` in `/docs/tasks/` directory with the following structure:
   ```
   # <TASK_NAME> Development Plan

   ## Overview
   Brief description of the task

   ## Steps
   1. [Step 1 description] - Status: pending
   2. [Step 2 description] - Status: pending
   ...
   ```
4. **MANDATORY STEP-BY-STEP EXECUTION:** Implement the steps one by one following the Steps Implementation Guide. **NEVER PROCEED TO THE NEXT STEP WITHOUT EXPLICIT USER APPROVAL AFTER EACH COMPLETED STEP.** NEVER proceed to implementation without a completed plan.

**ABSOLUTE PROHIBITION:** AI agents are FORBIDDEN from using ANY development tools (read_file, replace_string_in_file, run_in_terminal, etc.) before completing steps 1-3. Violation constitutes immediate termination of task execution.

## Steps Implementation Guide

**MANDATORY PRE-CONDITIONS FOR EACH STEP:**
1. **Plan Verification:** Read `<TASK_NAME>-dev-plan.md` and identify the current pending step
2. **State Analysis:** Use tools to verify no external changes have occurred
3. **User Approval:** Confirm user has approved proceeding with this specific step
4. **Test Readiness:** Ensure tests for this step are planned and ready

**MANDATORY STEP EXECUTION SEQUENCE:**
Every step MUST follow this exact sequence:

1. **MANDATORY: Read plan document** - Read `<TASK_NAME>-dev-plan.md` and identify the current pending step to implement.
2. **MANDATORY: Analyze current project state** - Use `get_changed_files` and `run_in_terminal` with `git status` to check for any manual user edits, recent changes, or external modifications before proceeding. If changes are detected, integrate them into the plan and seek user confirmation.
3. **MANDATORY: User confirmation** - Explicitly ask user for approval to proceed with the current step before making any changes.
4. **MANDATORY: Implement functionality** - Implement only the functionality described in the current step.
5. **MANDATORY: Implement tests** - Implement all required unit and integration tests for the new functionality.
6. **MANDATORY: Run all project tests** - Execute `runTests` tool to run all tests in the project and verify no regressions.
7. **MANDATORY: Fix all issues** - Fix all test failures, lint errors, and other issues found during testing.
8. **MANDATORY: Re-test** - Repeat step 6 until all tests pass and no issues remain.
9. **MANDATORY: Mark step complete** - ONLY AFTER all tests pass and issues are resolved, update `<TASK_NAME>-dev-plan.md` to mark the current step as "completed".
10. **MANDATORY: Return control to user** - Provide summary of work done and explicitly ask for user approval to proceed to the next step. DO NOT PROCEED WITHOUT EXPLICIT USER APPROVAL.

**EXAMPLE OF CORRECT STEP EXECUTION:**
```
AI: Step 1 completed successfully. All tests pass. Summary: Implemented feature X with tests.
AI: **STEP COMPLETED: [Step 1 Description]. WAITING FOR USER APPROVAL TO PROCEED TO NEXT STEP.**
AI: Please confirm if I should proceed to Step 2 or if you have any feedback/changes.
[WAIT FOR USER RESPONSE - DO NOT PROCEED]
```

**STEP EXECUTION RULES:**
- Each step must be completed fully before starting the next
- All tests must pass before marking a step complete
- User approval is required between steps
- Any external changes require plan updates and re-approval
- **ABSOLUTE REQUIREMENT:** Never proceed to next step without explicit user confirmation after each completed step

## Critical Enforcement Rules

**ABSOLUTE PROHIBITIONS:**
- AI agents are FORBIDDEN from marking any step as completed if tests fail or issues remain unresolved.
- AI agents are FORBIDDEN from proceeding to the next step without user review and approval.
- AI agents are FORBIDDEN from implementing functionality without first updating and validating tests.
- AI agents are FORBIDDEN from ignoring manual user edits or external changes.
- AI agents MUST ensure steps are sufficiently small to allow for complete validation before marking as done.
- **CRITICAL:** AI agents are FORBIDDEN from reading ANY source code files before creating a complete project analysis using `mcp_repomix_pack_codebase`.
- **CRITICAL:** AI agents are FORBIDDEN from making ANY code changes before creating and documenting a detailed implementation plan in `<TASK_NAME>-dev-plan.md`.
- **CRITICAL:** AI agents are FORBIDDEN from using ANY development tools (grep_search, file_search, read_file, replace_string_in_file, run_in_terminal, etc.) before completing the mandatory project analysis and planning phases.

**MANDATORY SELF-CHECK PROTOCOL:**
**CRITICAL REQUIREMENT: PERFORM THIS CHECK BEFORE EVERY ACTION, INCLUDING TOOL USAGE AND CODE CHANGES.**
Before using ANY tool or making ANY change, AI agents MUST ask themselves and DISPLAY the answers:
1. Have I completed `mcp_repomix_pack_codebase` analysis? (MANDATORY - NO = STOP)
2. Have I created `<TASK_NAME>-dev-plan.md` with detailed steps? (MANDATORY - NO = STOP)
3. Am I currently executing a specific step from the approved plan? (MANDATORY - NO = STOP)
4. Have I received explicit user approval for the current step? (MANDATORY - NO = STOP)
5. Have I implemented and validated tests for this functionality? (MANDATORY - NO = STOP)
6. Have I provided a completion summary and asked for user approval to proceed? (MANDATORY - NO = STOP)
7. Am I about to proceed to the next step without user confirmation? (CRITICAL - YES = STOP IMMEDIATELY)

If ANY answer is NO (or YES for question 7): **STOP IMMEDIATELY**, report violation, and await user instructions.

**ENFORCEMENT:** If any violation occurs, the agent MUST:
1. Immediately stop all execution
2. Report the specific violation to the user
3. Provide the self-check results that failed
4. Await explicit user instructions for correction or resumption

## Common Violations and Prevention

**CRITICAL VIOLATION: CONTINUOUS EXECUTION WITHOUT USER APPROVAL**
- **Description:** AI agents executing multiple steps in sequence without stopping for user approval after each step.
- **Prevention Measures:**
  - **MANDATORY STEP TERMINATION MESSAGE:** After completing each step, AI agents MUST output: "**STEP COMPLETED: [Step Description]. WAITING FOR USER APPROVAL TO PROCEED TO NEXT STEP.**"
  - **MANDATORY USER CONFIRMATION REQUIREMENT:** AI agents MUST explicitly ask: "Please confirm if I should proceed to the next step or if you have any feedback/changes."
  - **ABSOLUTE PROHIBITION ON AUTO-PROGRESSION:** AI agents are FORBIDDEN from automatically proceeding to the next step. Each step transition requires explicit user permission.
- **Consequences:** Immediate task abortion and requirement for complete restart with user oversight.

**CRITICAL VIOLATION: SKIPPING PLANNING PHASES**
- **Description:** AI agents proceeding directly to implementation without proper project analysis and planning.
- **Prevention Measures:**
  - **MANDATORY PRE-EXECUTION CHECKLIST:** Before any tool usage, display: "CONFIRMING COMPLIANCE: 1. Project analysis completed? 2. Plan documented? 3. Current step approved?"
  - **MANDATORY PLAN VERIFICATION:** Re-read the plan document before each step and confirm current step status.
- **Consequences:** Complete task invalidation and requirement for full restart.

**CRITICAL VIOLATION: INADEQUATE TESTING**
- **Description:** AI agents marking steps complete without comprehensive testing.
- **Prevention Measures:**
  - **MANDATORY TEST EXECUTION LOG:** Display detailed test results after each test run.
  - **MANDATORY FAILURE ANALYSIS:** If any test fails, provide root cause analysis before attempting fixes.
  - **MANDATORY SUCCESS CONFIRMATION:** Only mark step complete after all tests pass and user reviews results.
- **Consequences:** Regression introduction and requirement for rollback.

## Project Analysis Requirements

**MANDATORY ANALYSIS PROCEDURE:**
1. Execute `mcp_repomix_pack_codebase` with the project root directory
2. Wait for complete analysis to finish
3. Review the generated output to understand:
   - Current architecture and layer separation
   - Existing functionality and interfaces
   - Test coverage and structure
   - Dependencies and configurations
4. ONLY after complete analysis: proceed to planning phase

**PROHIBITED ACTIONS DURING ANALYSIS:**
- Reading individual source files
- Searching for specific code patterns
- Running tests or builds
- Making any code changes

## Planning Requirements

**PLAN STRUCTURE MANDATORY ELEMENTS:**
- **Task Name:** Must be descriptive and match the user request
- **Overview:** 2-3 sentences explaining what will be implemented
- **Steps:** Each step must be:
  - Small enough to implement in < 30 minutes
  - Independently testable
  - Have clear success criteria
  - Include test implementation requirements

**PLAN VALIDATION:**
Before proceeding to implementation, the agent MUST:
- Ensure all steps are sufficiently small
- Verify each step has test requirements
- Confirm the plan addresses the complete user request
- Save the plan as `<TASK_NAME>-dev-plan.md` in `/docs/tasks/`