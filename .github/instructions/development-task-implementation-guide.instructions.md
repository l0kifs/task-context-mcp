---
applyTo: '**'
---
# Development Task Implementation Guide

**MANDATORY COMPLIANCE:** AI agents MUST strictly follow each rule in this guide when performing any task related to creating or updating project functionality. VIOLATIONS WILL RESULT IN IMMEDIATE TERMINATION OF TASK EXECUTION AND REQUIRE USER APPROVAL FOR RESUMPTION.

When a new task is assigned to you, follow these steps to implement it effectively:
1. Analyze the project in detail using mcp repomix.
2. Split the task implementation into a list of small finalized steps.
3. Save the list of steps in new md file <TASK_NAME>-dev-plan.md in /docs/tasks/ directory.
4. Implement the steps one by one following the Steps Implementation Guide.

## Steps Implementation Guide

Every step includes next actions:
1. Read the document <TASK_NAME>-dev-plan.md and find the current step to implement.
2. **MANDATORY: Analyze current project state** - Use tools to check for any manual user edits, recent changes, or external modifications before proceeding. If changes are detected, integrate them into the plan and seek user confirmation.
3. Implement functionality described in the step.
4. Implement all required tests for the new functionality.
5. Test the existing and new functionality with all tests in the project.
6. Fix all the issues found during testing.
7. Repeat testing (step 5) and fixing (step 6) steps until all issues fixed.
8. **MANDATORY: Summarize the work done and mark current step as completed in <TASK_NAME>-dev-plan.md ONLY AFTER ALL ISSUES ARE FIXED AND TESTS PASS.**
9. **MANDATORY: Return control to user for review. DO NOT PROCEED TO NEXT STEP WITHOUT EXPLICIT USER APPROVAL.**

## Critical Enforcement Rules

**ABSOLUTE PROHIBITIONS:**
- AI agents are FORBIDDEN from marking any step as completed if tests fail or issues remain unresolved.
- AI agents are FORBIDDEN from proceeding to the next step without user review and approval.
- AI agents are FORBIDDEN from implementing functionality without first updating and validating tests.
- AI agents are FORBIDDEN from ignoring manual user edits or external changes.
- AI agents MUST ensure steps are sufficiently small to allow for complete validation before marking as done.

**ENFORCEMENT:** If any violation occurs, the agent MUST stop execution, report the violation to the user, and await instructions for correction.