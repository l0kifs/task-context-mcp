# Business Requirements Document
## AI Agent Task Management System with SQLite

**Version:** 1.5  
**Date:** December 7, 2025  
**Status:** Draft

---

## 1. Executive Summary

### 1.1 Project Overview
Development of an intelligent task management system that enables AI agents to autonomously manage and improve execution processes for repetitive tasks such as writing requirements, analyzing CVs, creating automated tests, and improving testing automation concepts.

### 1.2 Business Problem
Current workflow requires manual or semi-manual distribution and updating of:
- Best practices and rules
- Supporting prompts
- Task execution results
- Process improvement documentation

This creates inefficiency and prevents agents from working autonomously.

### 1.3 Proposed Solution
Implement SQLite-based storage system that enables:
- Automatic context retrieval based on minimal user queries
- Self-managed distribution of artifacts
- Autonomous process improvement with minimal user intervention
- Full-text search across historical results and best practices

---

## 2. Business Objectives

### 2.1 Primary Goals
1. **Reduce manual overhead** by 80% for artifact management
2. **Enable autonomous agent operation** with minimal user input
3. **Implement artifact lifecycle management** for all practices, rules, and prompts
4. **Enable efficient context retrieval** for similar past tasks

### 2.2 Success Metrics
- Time spent on manual artifact management: < 20% of current
- Agent autonomy level: Requires only key queries from user
- Artifact lifecycle coverage: 100% of artifacts
- Context retrieval accuracy: > 85% relevance

---

## 3. Scope

### 3.1 In Scope

#### Task Types
System is designed to be **task-agnostic** and extensible. Initial examples include:
- Development requirements writing
- Task time estimation analysis
- Python autotest creation
- CV-to-position analysis
- Test automation concept improvement

**Note:** Task types are dynamically configurable. Users can add new task types without code changes.

#### Core Features
- **Artifact Storage**: Best practices, rules, prompts, results
- **Lifecycle Management**: Active/archived status tracking with archival reasons
- **Full-Text Search**: FTS5-based search across artifacts
- **Context Loading**: Automatic retrieval based on task type
- **Process Improvement**: Agent-driven optimization of workflows

#### Technical Components
- SQLite embedded database integration
- Python SDK implementation (SQLAlchemy ORM)
- Full-text search (FTS5)
- Transaction-based operations

### 3.2 Out of Scope
- Distributed/cluster deployment (phase 2)
- Real-time collaboration between multiple agents
- External system integrations (initially)
- GUI/web interface (MCP server only)

---

## 4. Use Case Scenarios

### 4.1 Scenario 1: Working on New Task
**Trigger:** User asks agent to help with a task that doesn't exist in the system

**Flow:**
1. User asks agent to help with a task
2. Agent analyzes task context provided by user
3. Agent uses task-context-mcp to get list of existing active tasks
4. Agent analyzes the list and finds no matching task
5. Agent creates a new task in task-context-mcp
6. Agent adds relevant artifacts (practices, rules, prompts) to the new task if available
7. Agent implements the task using the artifacts and provides output to user
8. User reviews the output and provides feedback
9. Agent analyzes feedback and updates artifacts if necessary (create new or archive existing)
10. Agent refines task implementation based on updated artifacts
11. User reviews and provides feedback
12. Steps 9-11 repeat until user is satisfied

### 4.2 Scenario 2: Continuing Work on Existing Task
**Trigger:** User asks agent to help with a task that already exists in the system

**Flow:**
1. User asks agent to help with a task
2. Agent analyzes task context provided by user
3. Agent uses task-context-mcp to get list of existing active tasks
4. Agent analyzes the list and finds a matching task
5. Agent retrieves all relevant active artifacts for the existing task
6. Agent implements the task using the artifacts and provides output to user
7. User reviews the output and provides feedback
8. Agent analyzes feedback and updates artifacts if necessary (create new or archive existing)
9. Agent refines task implementation based on updated artifacts
10. User reviews and provides feedback
11. Steps 8-10 repeat until user is satisfied

---

## 5. Functional Requirements

### 5.1 Data Structure

#### FR-1: Task Catalog
**Priority:** Critical  
**Description:** System shall maintain a catalog of all tasks with associated metadata

| Field         | Type      | Description                                                          |
| ------------- | --------- | -------------------------------------------------------------------- |
| id            | STRING    | Unique identifier (UUID)                                             |
| summary       | STRING    | Summary of the task. Used by agent to identify the task              |
| description   | TEXT      | Detailed description of the task. Used by agent to identify the task |
| creation_date | TIMESTAMP | Timestamp when the task was created                                  |
| updated_date  | TIMESTAMP | Timestamp when the task was last updated                             |
| status        | ENUM      | 'active', 'archived'                                                 |

#### FR-2: Artifact Storage
**Priority:** Critical  
**Description:** System shall store all artifacts with status tracking

| Field              | Type      | Description                                       |
| ------------------ | --------- | ------------------------------------------------- |
| id                 | STRING    | Unique identifier (UUID)                          |
| summary            | TEXT      | Summary of the artifact. Used for quick reference |
| content            | TEXT      | Full content of the artifact                      |
| task_id            | STRING    | Foreign key to task catalog                       |
| artifact_type      | ENUM      | 'practice', 'rule', 'prompt', 'result'            |
| status             | ENUM      | 'active', 'archived'                              |
| archived_at        | TIMESTAMP | Timestamp when the artifact was archived          |
| archivation_reason | TEXT      | Reason for archiving the artifact                 |
| created_at         | TIMESTAMP | Timestamp when the artifact was created           |

### 5.2 Core Operations

#### FR-3: Task Matching and Context Retrieval
**Priority:** Critical  
**User Story:** As an agent, I need to find existing active tasks or create new ones, and automatically load relevant context

**Workflow:**
1. Agent receives user request and analyzes task context
2. Agent retrieves list of existing active tasks
3. Agent analyzes the list to find matching task:
   - **If match found:** Continue with existing task and load its artifacts
   - **If no match:** Create new task and add relevant artifacts
4. Agent retrieves all relevant active artifacts for the task
5. Agent implements task using artifacts and provides output

**Acceptance Criteria:**
- List all active tasks with metadata for agent analysis
- Query "write requirements" retrieves all relevant practices, rules, and prompts
- Full-text search (FTS5) finds similar past results (top 10)
- SQL filters by task_type and artifact_type
- Results ranked by relevance score
- Support task matching by keyword similarity to user query

#### FR-4: Autonomous Updates with Feedback Loop
**Priority:** High  
**User Story:** As an agent, I need to improve practices and rules based on execution results and user feedback

**Iterative Refinement Workflow:**
1. Agent implements task using loaded artifacts
2. Agent provides output to user
3. User reviews output and provides feedback
4. Agent analyzes feedback and updates artifacts:
   - Create new artifacts if needed
   - Update existing artifacts with improvements
   - Archive artifacts that are no longer relevant
5. Agent refines implementation based on updated artifacts
6. Agent provides revised output to user
7. Steps 3-6 repeat until user is satisfied

**Acceptance Criteria:**
- Agent analyzes execution success/failure
- Agent analyzes user feedback to identify artifact improvements
- Agent proposes practice/rule updates
- Agent can create new artifacts based on feedback
- Agent can archive artifacts based on feedback
- User receives summary of changes (optional approval)

**Self-Improvement Process:**

**Step 1: Data Collection**
- Track execution metrics for each task (success rate, time, quality scores)
- Store execution results with metadata (context used, artifacts applied)
- Log user feedback (explicit corrections, implicit through re-runs)
- Monitor pattern: same task type with different outcomes

**Step 2: Performance Analysis**
```
Query: "Find all CV analysis tasks from last 30 days"
↓
Aggregate metrics:
- Success rate: 85%
- Average time: 5 minutes
- User corrections: 15% of tasks
↓
Identify patterns:
- Tasks using Rule A: 95% success
- Tasks using Rule B: 60% success
- Common failure: missed technical skills section
```

**Step 3: Improvement Hypothesis**
```
Agent reasoning:
"Rule B has lower success rate than Rule A.
Failed tasks often miss technical skills section.
Rule B doesn't emphasize technical skills extraction.
Hypothesis: Update Rule B to include technical skills focus."
```

**Step 4: Proposal Generation**
- Agent generates improved artifact
- Compares with current artifact
- Estimates impact based on historical data
- Creates justification with evidence

**Step 5: Validation & Approval**
```
Proposal to user:
┌─────────────────────────────────────────┐
│ Improvement Proposal                     │
├─────────────────────────────────────────┤
│ Artifact: CV Analysis Rule #42          │
│ Current Success Rate: 60%               │
│ Estimated New Rate: 85%                 │
│                                         │
│ Changes:                                │
│ + Add: "Extract technical skills first"│
│ + Add: "Match skills to job req"       │
│ ~ Modify: Priority order of sections   │
│                                         │
│ Evidence: 12 failed tasks analysis     │
│                                         │
│ [Approve] [Test] [Reject]              │
└─────────────────────────────────────────┘
```

**Step 6: Implementation Strategy**

**Option A: Immediate Deployment (user approves)**
```sql
-- Mark old artifact as archived
UPDATE artifacts 
SET status='archived',
    archived_at=CURRENT_TIMESTAMP,
    archivation_reason='Replaced by new version with technical skills focus'
WHERE id='artifact-uuid-42';

-- Insert new artifact
INSERT INTO artifacts (id, task_id, artifact_type, summary, content, status)
VALUES ('new-uuid', 'task-uuid', 'rule', 'CV analysis with technical skills focus', 'NEW_CONTENT', 'active');
```

**Step 7: Continuous Monitoring**
- Track new artifact performance
- Compare against previous baseline
- Detect regression
- Suggest rollback to previous artifact if regression detected

**Step 8: Feedback Loop**
```
After 100 executions with new rule:
↓
Success rate: 92% (better than expected 85%)
↓
Agent learns:
"Technical skills focus was correct improvement.
Other similar rules should also prioritize technical skills."
↓
Proactively suggests:
"Apply similar pattern to other CV-related rules?"
```

#### FR-5: Minimal Query Processing
**Priority:** High  
**User Story:** As a user, I want to send minimal queries like "analyze CV" and have agent handle the rest

**Acceptance Criteria:**
- Query parser extracts task_type from natural language
- Agent loads all relevant context automatically
- Agent executes task with loaded context
- Agent stores results appropriately
- User receives only final output

#### FR-6: Artifact Lifecycle Management
**Priority:** High  
**User Story:** As an agent, I need to manage the full lifecycle of artifacts including creation, updates, and archival based on task execution and user feedback

**Lifecycle States:**
- **Active:** Artifact is included in context loading for relevant tasks
- **Archived:** Artifact is excluded from active context and hidden from queries

**Feedback-Driven Lifecycle:**
1. Agent creates new artifacts when needed during task execution
2. Agent updates artifacts based on user feedback and execution analysis
3. Agent archives artifacts that are no longer relevant or have been superseded
4. All lifecycle changes are tracked with timestamps and reasons

**Acceptance Criteria:**
- Agent can create new artifacts during task execution
- Agent can mark artifacts as 'archived' with reason and timestamp
- Archived artifacts excluded from active context loading
- Historical queries can still access archived artifacts if needed
- Archival triggers notification to user
- Agent can suggest replacement artifacts
- Bulk archival supported (e.g., all rules from old framework)

#### FR-7: Conflict Resolution
**Priority:** High  
**User Story:** As an agent, I need to handle conflicting rules or practices gracefully

**Acceptance Criteria:**
- System detects conflicting artifacts (contradictory rules)
- Agent ranks artifacts by creation date (most recent takes precedence)
- Conflicts logged for user review
- User can manually resolve conflicts by archiving one artifact
- Archival can resolve conflicts automatically

---

## 6. Non-Functional Requirements

### 6.1 Performance
- **NFR-1:** Context retrieval < 2 seconds for 10K artifacts
- **NFR-2:** Full-text search response < 500ms

### 6.2 Reliability
- **NFR-3:** ACID compliance for all transactions
- **NFR-4:** Data persistence with automatic backups
- **NFR-5:** Zero data loss during updates

### 6.3 Scalability
- **NFR-6:** Support up to 100K artifacts per task
- **NFR-7:** Support unlimited artifacts per task type
- **NFR-8:** Embedded mode sufficient for single-user workload

### 6.4 Maintainability
- **NFR-9:** Clear schema migration path
- **NFR-10:** Comprehensive logging for debugging
- **NFR-11:** Export capability for backup/migration

---

## 7. Technical Architecture

### 7.1 Technology Stack
- **Database:** SQLite 3.35+ (with FTS5 extension)
- **Language:** Python 3.12+
- **ORM:** SQLAlchemy 2.0+
- **Search:** SQLite FTS5 for full-text search
- **LLM Access:** GitHub Copilot via VSCode API
- **Interface:** MCP Server (Model Context Protocol via FastMCP)
- **Development Environment:** VSCode with GitHub Copilot

### 7.2 AI Integration Strategy (No External API Keys Required)

#### GitHub Copilot Integration (Primary)
**Prerequisites:**
- Active GitHub Copilot subscription ✅ (You have this)
- VSCode with Copilot extension installed
- Python extension for VSCode

**How it works:**
```python
# Agent interacts with Copilot via VSCode API
from github_copilot_vscode import CopilotChat

class CopilotAgent:
    def __init__(self):
        self.copilot = CopilotChat()
    
    def generate_improvement(self, context, current_rule, failures):
        prompt = f"""
        Analyze this rule and suggest improvements:
        
        Current Rule: {current_rule}
        Failure Patterns: {failures}
        Context: {context}
        
        Generate an improved version.
        """
        
        # Send to Copilot Chat
        response = self.copilot.send_message(prompt)
        return response.content
```

**Capabilities with Copilot:**
- Code generation and improvement
- Analysis of patterns and issues
- Documentation generation
- Test case creation
- Requirement writing assistance

**Limitations:**
- Requires active internet connection
- Rate limits apply (but generous for personal use)
- Context window limits (~8K tokens per request)

#### SQLite Full-Text Search (FTS5)
**Built-in search capability with SQLAlchemy:**
```python
from sqlalchemy import create_engine, text
from sqlalchemy.orm import Session

engine = create_engine("sqlite:///task_context.db")

# Create FTS5 virtual table for full-text search
with engine.connect() as conn:
    conn.execute(text("""
        CREATE VIRTUAL TABLE IF NOT EXISTS artifacts_fts USING fts5(
            content,
            content_rowid='artifact_id'
        );
    """))
    conn.commit()

# Search for relevant artifacts
with Session(engine) as session:
    results = session.execute(text("""
        SELECT a.*, bm25(artifacts_fts) as rank
        FROM artifacts a
        JOIN artifacts_fts fts ON a.artifact_id = fts.rowid
        WHERE artifacts_fts MATCH :query
        ORDER BY rank
        LIMIT 10;
    """), {"query": search_query}).fetchall()
```

**Advantages of SQLAlchemy + SQLite FTS5:**
- ORM support for cleaner, type-safe code
- Database-agnostic (easy migration to PostgreSQL if needed)
- Built-in connection pooling and session management
- Supports ranking with BM25
- Simple to maintain and backup

### 7.3 Integration Points
- **Input:** User natural language queries via MCP tools
- **Output:** Task execution results + updated artifacts via MCP responses
- **Storage:** Local SQLite file (`./data/task_context.db`)
- **Backup:** Git repository (optional) + SQLite backup API
- **AI Access:** GitHub Copilot API via VSCode extension
- **Search:** SQLite FTS5 for full-text search (no external dependencies)
- **Protocol:** Model Context Protocol (MCP) via FastMCP for AI agent integration

---

## 8. Implementation Phases

### Phase 1: Foundation (Weeks 1-2)
- SQLite setup and schema design
- FTS5 virtual tables for full-text search
- Basic CRUD operations
- Task and Artifact models with UUID-based identification
- Single task type example (e.g., requirements writing)

### Phase 2: Intelligence (Weeks 3-4)
- Full-text search optimization
- Context auto-loading
- Artifact lifecycle management (active/archived)
- Task matching by summary and description

### Phase 3: Autonomy (Weeks 5-6)
- Agent-driven updates
- Process improvement logic
- Minimal query processing

### Phase 4: Optimization (Weeks 7-8)
- Performance tuning
- Support for unlimited task types
- Monitoring and logging
- Task type management via MCP tools

---

## 9. Risks and Mitigation

| Risk                               | Impact | Probability | Mitigation                              |
| ---------------------------------- | ------ | ----------- | --------------------------------------- |
| SQLite concurrency limitations     | Low    | Low         | Single-user mode, WAL mode for reads    |
| Performance degradation with scale | Medium | Low         | Monitor metrics, optimize queries early |
| Complex artifact management logic  | Medium | Medium      | Start simple, iterate based on needs    |
| Agent hallucination in updates     | High   | Low         | User approval for critical changes      |

---

## 10. Dependencies

### External Dependencies
- SQLite (bundled with Python - no external install needed)
- SQLAlchemy 2.0+ (pip install)
- Python ecosystem compatibility

### Internal Dependencies
- Agent execution framework
- Query parsing capabilities
- User approval workflow (for critical updates)

---

## 11. Success Criteria

### MVP (Minimum Viable Product)
- ✅ Store and retrieve artifacts with status tracking
- ✅ Full-text search across historical results
- ✅ Auto-load context for tasks by summary/description
- ✅ Artifact archival with reason tracking

### Full Release
- ✅ Unlimited tasks supported with UUID-based identification
- ✅ Autonomous agent updates with approval
- ✅ Minimal query processing for all tasks
- ✅ 80% reduction in manual overhead achieved
- ✅ Task and artifact lifecycle management

---

**Document Control:**
- **Author:** AI Assistant
- **Change History:** 
  - v1.0 - Initial draft
  - v1.1 - Added Use Case Scenarios section; Updated FR-3 to include task matching workflow; Enhanced FR-5 with feedback loop workflow; Expanded FR-7 with feedback-driven lifecycle management
  - v1.2 - Replaced SeekDB with SQLite; Replaced vector/semantic search with FTS5 full-text search; Simplified technology stack
  - v1.3 - Replaced sqlite3 with SQLAlchemy ORM for cleaner, type-safe database access
  - v1.4 - Updated data structures to match final implementation: UUID-based identification, simplified status model (active/archived), updated field names to match models.py
  - v1.5 - Simplified project by removing artifact versioning concept entirely; artifacts are now simply created, updated, or archived