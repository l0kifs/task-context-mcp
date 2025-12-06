# Task Context MCP Server - Workflow Documentation

> **Version:** 1.0  
> **Date:** December 6, 2025

This document describes the complete operational workflows of the Task Context MCP Server, detailing how AI agents interact with the system to manage tasks, artifacts, and autonomous improvements.

---

## Table of Contents

- [Task Context MCP Server - Workflow Documentation](#task-context-mcp-server---workflow-documentation)
  - [Table of Contents](#table-of-contents)
  - [1. System Overview](#1-system-overview)
    - [Key Components](#key-components)
  - [2. Core Workflows](#2-core-workflows)
    - [2.1 Task Type Registration](#21-task-type-registration)
    - [2.2 Artifact Management](#22-artifact-management)
      - [2.2.1 Create Artifact](#221-create-artifact)
      - [2.2.2 Update Artifact (Creates New Version)](#222-update-artifact-creates-new-version)
      - [2.2.3 Deprecate Artifact](#223-deprecate-artifact)
    - [2.3 Context Retrieval](#23-context-retrieval)
      - [Load Context for Task Type](#load-context-for-task-type)
    - [2.4 Task Execution](#24-task-execution)
  - [3. Search Workflows](#3-search-workflows)
    - [3.1 Semantic Search](#31-semantic-search)
    - [3.2 Hybrid Search](#32-hybrid-search)
    - [3.3 Context Auto-Loading](#33-context-auto-loading)
  - [4. Version Management Workflows](#4-version-management-workflows)
    - [4.1 Version Creation](#41-version-creation)
    - [4.2 Version History \& Comparison](#42-version-history--comparison)
    - [4.3 Rollback](#43-rollback)
  - [5. Autonomous Improvement Workflows](#5-autonomous-improvement-workflows)
    - [5.1 Metrics Collection](#51-metrics-collection)
    - [5.2 Performance Analysis](#52-performance-analysis)
    - [5.3 Proposal Generation](#53-proposal-generation)
    - [5.4 Approval Workflow](#54-approval-workflow)
    - [5.5 A/B Testing](#55-ab-testing)
  - [6. End-to-End Scenarios](#6-end-to-end-scenarios)
    - [6.1 New Task Type Setup](#61-new-task-type-setup)
    - [6.2 Minimal Query Processing](#62-minimal-query-processing)
    - [6.3 Self-Improving Agent Loop](#63-self-improving-agent-loop)
  - [7. Data Flow Diagrams](#7-data-flow-diagrams)
    - [Complete System Data Flow](#complete-system-data-flow)
  - [8. Error Handling](#8-error-handling)
    - [Error Categories \& Recovery](#error-categories--recovery)
    - [Error Response Format](#error-response-format)
  - [Summary](#summary)

---

## 1. System Overview

```
┌─────────────────────────────────────────────────────────────────────────┐
│                           AI Agent (Client)                              │
│                    (GitHub Copilot / Other LLM)                          │
└─────────────────────────────────────────────────────────────────────────┘
                                    │
                                    │ MCP Protocol (FastMCP)
                                    ▼
┌─────────────────────────────────────────────────────────────────────────┐
│                      Task Context MCP Server                             │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐    │
│  │   Tools     │  │  Resources  │  │  Services   │  │ Repositories│    │
│  │ (Actions)   │  │ (Read-only) │  │  (Logic)    │  │   (Data)    │    │
│  └─────────────┘  └─────────────┘  └─────────────┘  └─────────────┘    │
└─────────────────────────────────────────────────────────────────────────┘
                                    │
                                    │ pyseekdb
                                    ▼
┌─────────────────────────────────────────────────────────────────────────┐
│                     SeekDB (Embedded Mode)                               │
│  ┌─────────────────────────┐  ┌─────────────────────────┐              │
│  │   task_catalog          │  │      artifacts          │              │
│  │   (Task Types)          │  │  (Versioned Content)    │              │
│  └─────────────────────────┘  └─────────────────────────┘              │
└─────────────────────────────────────────────────────────────────────────┘
```

### Key Components

| Component         | Purpose                                               |
| ----------------- | ----------------------------------------------------- |
| **MCP Tools**     | Actions the agent can perform (CRUD, search, approve) |
| **MCP Resources** | Read-only data endpoints (config, schemas)            |
| **Services**      | Business logic (search, versioning, analysis)         |
| **Repositories**  | Data access layer (artifacts, task catalog)           |
| **SeekDB**        | Embedded vector database with hybrid search           |

---

## 2. Core Workflows

### 2.1 Task Type Registration

Register a new category of tasks before storing related artifacts.

```
┌──────────────┐     ┌─────────────────┐     ┌─────────────────┐     ┌─────────┐
│   AI Agent   │────▶│ register_task   │────▶│  Task Catalog   │────▶│ SeekDB  │
│              │     │ _type tool      │     │  Repository     │     │         │
└──────────────┘     └─────────────────┘     └─────────────────┘     └─────────┘
```

**Flow:**
1. Agent calls `register_task_type(task_type="cv_analysis", description="Analyze CVs...")`
2. Server validates task_type doesn't exist
3. Creates entry in `task_catalog` collection
4. Returns confirmation with created_at timestamp

**Example:**
```
Agent Input:
  tool: register_task_type
  params:
    task_type: "requirements_writing"
    description: "Writing software development requirements from user stories"

Server Response:
  status: "success"
  task_type: "requirements_writing"
  created_at: "2025-12-06T10:30:00Z"
```

---

### 2.2 Artifact Management

#### 2.2.1 Create Artifact

```
┌──────────────┐     ┌─────────────────┐     ┌─────────────────┐     ┌─────────────────┐
│   AI Agent   │────▶│  add_artifact   │────▶│   Embedding     │────▶│   Artifact      │
│              │     │     tool        │     │   Service       │     │   Repository    │
└──────────────┘     └─────────────────┘     └─────────────────┘     └─────────────────┘
                                                     │                        │
                                                     │ Generate 384-dim       │
                                                     │ embedding              │
                                                     ▼                        ▼
                                              ┌─────────────────────────────────────┐
                                              │            SeekDB                   │
                                              │   artifacts collection              │
                                              │   (content + embedding + metadata)  │
                                              └─────────────────────────────────────┘
```

**Flow:**
1. Agent calls `add_artifact(task_type, artifact_type, content, metadata)`
2. Server validates task_type exists
3. Embedding service generates vector from content
4. Repository creates artifact with version=1, status='active'
5. Returns artifact_id and version

**Artifact Types:**
- `practice` - Best practices for task execution
- `rule` - Specific rules to follow
- `prompt` - Reusable prompt templates
- `result` - Execution results for learning

---

#### 2.2.2 Update Artifact (Creates New Version)

```
┌──────────────┐     ┌─────────────────┐     ┌─────────────────┐
│   AI Agent   │────▶│ update_artifact │────▶│   Repository    │
│              │     │      tool       │     │                 │
└──────────────┘     └─────────────────┘     └─────────────────┘
                                                     │
                                                     │ 1. Keep old version
                                                     │ 2. Create new version
                                                     ▼
                                              ┌─────────────────┐
                                              │    SeekDB       │
                                              │  v1 (archived)  │
                                              │  v2 (active)    │
                                              └─────────────────┘
```

**Flow:**
1. Agent calls `update_artifact(artifact_id, content, metadata)`
2. Server retrieves current version
3. Archives current version (status='archived')
4. Creates new version with incremented version number
5. Generates new embedding for updated content
6. Returns new artifact_id and version

---

#### 2.2.3 Deprecate Artifact

```
┌──────────────┐     ┌───────────────────┐     ┌─────────────────┐
│   AI Agent   │────▶│ deprecate_artifact│────▶│   Repository    │
│              │     │       tool        │     │                 │
└──────────────┘     └───────────────────┘     └─────────────────┘
                                                       │
                                                       ▼
                                              ┌─────────────────────────┐
                                              │        SeekDB           │
                                              │  status: 'deprecated'   │
                                              │  deprecated_at: now()   │
                                              │  deprecated_reason: ... │
                                              │  replacement_id: ...    │
                                              └─────────────────────────┘
```

**Flow:**
1. Agent calls `deprecate_artifact(artifact_id, reason, replacement_id)`
2. Server validates artifact exists and is active
3. Updates status to 'deprecated'
4. Records deprecation timestamp and reason
5. Links to replacement artifact if provided
6. Deprecated artifacts excluded from active context loading

---

### 2.3 Context Retrieval

#### Load Context for Task Type

```
┌──────────────┐     ┌───────────────────┐     ┌─────────────────┐
│   AI Agent   │────▶│ load_task_context │────▶│ Context Loader  │
│              │     │       tool        │     │    Service      │
└──────────────┘     └───────────────────┘     └─────────────────┘
                                                       │
                                                       │ Query by task_type
                                                       │ Filter: status='active'
                                                       ▼
                                              ┌─────────────────────────┐
                                              │        SeekDB           │
                                              │  artifacts collection   │
                                              └─────────────────────────┘
                                                       │
                                                       ▼
                                              ┌─────────────────────────┐
                                              │    Aggregated Context   │
                                              │  - practices: [...]     │
                                              │  - rules: [...]         │
                                              │  - prompts: [...]       │
                                              └─────────────────────────┘
```

**Flow:**
1. Agent calls `load_task_context(task_type="cv_analysis")`
2. Context loader queries all active artifacts for task_type
3. Groups by artifact_type (practices, rules, prompts)
4. Returns structured context object

**Response Structure:**
```json
{
  "task_type": "cv_analysis",
  "context": {
    "practices": [
      {"id": "p1", "content": "Always start with contact info extraction..."},
      {"id": "p2", "content": "Use structured output format..."}
    ],
    "rules": [
      {"id": "r1", "content": "Technical skills must match job requirements..."},
      {"id": "r2", "content": "Experience years calculation must be accurate..."}
    ],
    "prompts": [
      {"id": "pr1", "content": "Analyze the following CV against job description..."}
    ]
  },
  "loaded_at": "2025-12-06T10:30:00Z"
}
```

---

### 2.4 Task Execution

Complete workflow from user query to result storage.

```
┌──────────┐   ┌───────────────┐   ┌───────────────┐   ┌───────────────┐   ┌───────────┐
│   User   │──▶│   AI Agent    │──▶│  MCP Server   │──▶│    SeekDB     │──▶│  AI Agent │
│          │   │               │   │               │   │               │   │           │
│ "analyze │   │ 1. Parse      │   │ 2. Load       │   │ 3. Return     │   │ 4. Execute│
│  this CV"│   │    query      │   │    context    │   │    context    │   │    task   │
└──────────┘   └───────────────┘   └───────────────┘   └───────────────┘   └───────────┘
                                                                                   │
                                                                                   ▼
┌──────────┐   ┌───────────────┐   ┌───────────────┐   ┌───────────────┐   ┌───────────┐
│   User   │◀──│   AI Agent    │◀──│  MCP Server   │◀──│    SeekDB     │◀──│  AI Agent │
│          │   │               │   │               │   │               │   │           │
│ Receives │   │ 7. Return     │   │ 6. Store      │   │ 5. Save       │   │ 5. Store  │
│ analysis │   │    result     │   │    result     │   │    result     │   │    result │
└──────────┘   └───────────────┘   └───────────────┘   └───────────────┘   └───────────┘
```

**Detailed Flow:**

1. **User Query:** "analyze this CV for senior Python developer position"

2. **Query Parsing:**
   - Extract task_type: `cv_analysis`
   - Extract keywords: ["CV", "senior", "Python", "developer"]
   - Classify intent: `analyze`

3. **Context Loading:**
   - Load all active practices, rules, prompts for `cv_analysis`
   - Find similar past results (top 10)

4. **Task Execution:**
   - Agent uses loaded context to perform analysis
   - Applies rules and follows practices

5. **Result Storage:**
   - Store execution result as artifact (type: 'result')
   - Include metadata: success, duration, context_used

6. **Metrics Recording:**
   - Record execution for performance analysis
   - Track which artifacts were used

7. **Return Result:**
   - Formatted analysis returned to user

---

## 3. Search Workflows

### 3.1 Semantic Search

Find artifacts by meaning, not just keywords.

```
┌──────────────┐     ┌───────────────────┐     ┌─────────────────┐
│   AI Agent   │────▶│  search_artifacts │────▶│  Search Service │
│              │     │       tool        │     │                 │
└──────────────┘     └───────────────────┘     └─────────────────┘
                                                       │
                                                       │ 1. Generate query embedding
                                                       │ 2. Vector similarity search
                                                       ▼
                                              ┌─────────────────────────┐
                                              │        SeekDB           │
                                              │  collection.query(      │
                                              │    query_texts=[...],   │
                                              │    n_results=10         │
                                              │  )                      │
                                              └─────────────────────────┘
                                                       │
                                                       ▼
                                              ┌─────────────────────────┐
                                              │   Ranked Results        │
                                              │   (by similarity)       │
                                              └─────────────────────────┘
```

**Example:**
```
Query: "handling edge cases in CV parsing"

Results (ranked by semantic similarity):
1. [0.89] "Edge case: CV with no dates - assume current year..."
2. [0.85] "Handle missing sections gracefully..."
3. [0.82] "Default values for incomplete data..."
```

---

### 3.2 Hybrid Search

Combine vector similarity + full-text + metadata filtering.

```
┌──────────────┐     ┌───────────────────┐     ┌─────────────────┐
│   AI Agent   │────▶│  search_artifacts │────▶│  Search Service │
│              │     │       tool        │     │                 │
└──────────────┘     └───────────────────┘     └─────────────────┘
                                                       │
                                                       ▼
                                              ┌─────────────────────────┐
                                              │   Hybrid Search         │
                                              │                         │
                                              │   1. Vector Search      │
                                              │      (semantic)         │
                                              │                         │
                                              │   2. Full-Text Search   │
                                              │      (keywords)         │
                                              │                         │
                                              │   3. Metadata Filter    │
                                              │      (task_type, etc)   │
                                              │                         │
                                              │   4. RRF Ranking        │
                                              │      (combine scores)   │
                                              └─────────────────────────┘
                                                       │
                                                       ▼
                                              ┌─────────────────────────┐
                                              │   Final Ranked Results  │
                                              └─────────────────────────┘
```

**RRF (Reciprocal Rank Fusion) Scoring:**
```
score = Σ 1/(k + rank_i) for each search method

Where:
- k = 60 (constant)
- rank_i = position in each result list
```

---

### 3.3 Context Auto-Loading

Automatic context retrieval from minimal user query.

```
┌──────────┐         ┌───────────────────────────────────────────────────────────┐
│   User   │         │                       MCP Server                          │
│          │         │                                                           │
│ "write   │────────▶│  ┌─────────────┐   ┌─────────────┐   ┌─────────────┐    │
│  reqs"   │         │  │Query Parser │──▶│Context      │──▶│Similar      │    │
│          │         │  │             │   │Loader       │   │Results      │    │
└──────────┘         │  │ task_type:  │   │             │   │Finder       │    │
                     │  │ reqs_writing│   │ practices   │   │             │    │
                     │  │             │   │ rules       │   │ top 10      │    │
                     │  │ intent:     │   │ prompts     │   │ similar     │    │
                     │  │ create      │   │             │   │ results     │    │
                     │  └─────────────┘   └─────────────┘   └─────────────┘    │
                     │                                                           │
                     │  ┌─────────────────────────────────────────────────────┐ │
                     │  │              Execution Context                       │ │
                     │  │  - task_type: requirements_writing                   │ │
                     │  │  - practices: [p1, p2, p3]                          │ │
                     │  │  - rules: [r1, r2]                                  │ │
                     │  │  - prompts: [main_prompt]                           │ │
                     │  │  - similar_results: [prev1, prev2, ...]             │ │
                     │  └─────────────────────────────────────────────────────┘ │
                     └───────────────────────────────────────────────────────────┘
```

**Query Parser Intelligence:**

| User Input              | Detected Task Type        | Intent  |
| ----------------------- | ------------------------- | ------- |
| "write requirements"    | `requirements_writing`    | create  |
| "analyze CV"            | `cv_analysis`             | analyze |
| "create autotests"      | `autotest_creation`       | create  |
| "improve test coverage" | `test_automation_concept` | update  |

---

## 4. Version Management Workflows

### 4.1 Version Creation

Every update creates a new version, preserving history.

```
                    ┌─────────────────────────────────────────┐
                    │           Artifact Timeline              │
                    │                                          │
    create          │  v1 ──────▶ v2 ──────▶ v3 ──────▶ v4   │
      │             │  │          │          │          │     │
      ▼             │  │          │          │          │     │
    ┌───┐           │  active     archived   archived   active│
    │v1 │           │             │          │                │
    │   │──update──▶│             │          │                │
    └───┘           │          update     update              │
                    │                                          │
                    └─────────────────────────────────────────┘
```

**Version Metadata:**
```json
{
  "artifact_id": "art_123",
  "version": 3,
  "content": "Updated rule content...",
  "status": "active",
  "created_at": "2025-12-06T10:30:00Z",
  "change_reason": "Improved accuracy for edge cases",
  "previous_version": 2
}
```

---

### 4.2 Version History & Comparison

```
┌──────────────┐     ┌───────────────────────┐     ┌─────────────────┐
│   AI Agent   │────▶│ get_artifact_history  │────▶│ Version Service │
│              │     │       tool            │     │                 │
└──────────────┘     └───────────────────────┘     └─────────────────┘
                                                           │
                                                           ▼
                                                  ┌─────────────────────────┐
                                                  │   Version History       │
                                                  │                         │
                                                  │   v1: 2025-12-01 (init) │
                                                  │   v2: 2025-12-03 (+edge)│
                                                  │   v3: 2025-12-05 (fix)  │
                                                  │   v4: 2025-12-06 (active│
                                                  └─────────────────────────┘
```

**Comparison Output:**
```
┌─────────────────────────────────────────────────────────────┐
│  Comparing artifact_id: art_123                              │
│  Version 2 → Version 4                                       │
├─────────────────────────────────────────────────────────────┤
│  REMOVED:                                                    │
│  - "Use simple string matching for skills"                   │
│                                                              │
│  ADDED:                                                      │
│  + "Use semantic matching for skills extraction"             │
│  + "Handle skill synonyms (e.g., JS = JavaScript)"          │
│                                                              │
│  MODIFIED:                                                   │
│  ~ "Extract top 5 skills" → "Extract top 10 skills"         │
└─────────────────────────────────────────────────────────────┘
```

---

### 4.3 Rollback

Restore a previous version when needed.

```
┌──────────────┐     ┌───────────────────┐     ┌─────────────────┐
│   AI Agent   │────▶│ rollback_artifact │────▶│ Version Service │
│              │     │       tool        │     │                 │
└──────────────┘     └───────────────────┘     └─────────────────┘
                                                       │
                                                       │ 1. Get target version content
                                                       │ 2. Archive current version
                                                       │ 3. Create new version from target
                                                       ▼
                                              ┌─────────────────────────────┐
                                              │        Version History       │
                                              │                              │
                                              │  v1 ─▶ v2 ─▶ v3 ─▶ v4 ─▶ v5│
                                              │       (target)        (new) │
                                              │                       ▲     │
                                              │                       │     │
                                              │            rollback ──┘     │
                                              │            (copy of v2)     │
                                              └─────────────────────────────┘
```

**Rollback preserves history:**
- Current version archived (not deleted)
- New version created with content from target
- Rollback reason recorded in metadata

---

## 5. Autonomous Improvement Workflows

### 5.1 Metrics Collection

Every task execution feeds the improvement loop.

```
┌──────────────┐     ┌─────────────────────┐     ┌─────────────────┐
│   AI Agent   │────▶│ record_task         │────▶│ Metrics Service │
│              │     │ _execution tool     │     │                 │
└──────────────┘     └─────────────────────┘     └─────────────────┘
                                                         │
                                                         ▼
                                                ┌─────────────────────────┐
                                                │   Execution Record      │
                                                │                         │
                                                │   task_type: cv_analysis│
                                                │   success: true         │
                                                │   duration: 45s         │
                                                │   artifacts_used: [...]│
                                                │   quality_score: 0.92   │
                                                │   user_corrections: 0   │
                                                │   timestamp: ...        │
                                                └─────────────────────────┘
```

**Metrics Tracked:**
| Metric             | Description                | Aggregation                 |
| ------------------ | -------------------------- | --------------------------- |
| `success_rate`     | % of successful executions | Per artifact, per task type |
| `duration`         | Execution time             | Average, P95                |
| `quality_score`    | Output quality (0-1)       | Average                     |
| `user_corrections` | Manual fixes needed        | Count                       |
| `re_runs`          | Task re-executed           | Count                       |

---

### 5.2 Performance Analysis

Identify underperforming artifacts.

```
┌───────────────────────────────────────────────────────────────────────────────┐
│                         Analysis Engine                                        │
│                                                                               │
│   ┌─────────────────┐     ┌─────────────────┐     ┌─────────────────┐       │
│   │  Aggregate      │────▶│  Identify       │────▶│  Generate       │       │
│   │  Metrics        │     │  Patterns       │     │  Hypothesis     │       │
│   └─────────────────┘     └─────────────────┘     └─────────────────┘       │
│                                                                               │
│   Last 30 days:           Pattern found:          Hypothesis:                │
│   - Rule A: 95% success   - Tasks with Rule B     "Rule B lacks technical   │
│   - Rule B: 60% success     often miss tech       skills extraction         │
│   - Rule C: 88% success     skills section        guidance"                 │
│                                                                               │
└───────────────────────────────────────────────────────────────────────────────┘
```

**Analysis Output:**
```json
{
  "artifact_id": "rule_42",
  "period": "30_days",
  "metrics": {
    "executions": 150,
    "success_rate": 0.60,
    "avg_quality": 0.72,
    "user_corrections": 23
  },
  "patterns": [
    {
      "pattern": "missing_tech_skills",
      "frequency": 0.35,
      "impact": "high"
    }
  ],
  "hypothesis": "Rule lacks emphasis on technical skills extraction",
  "recommended_action": "update"
}
```

---

### 5.3 Proposal Generation

Create structured improvement proposals.

```
┌──────────────────────────────────────────────────────────────────────────────────┐
│                            Improvement Proposal                                   │
│                                                                                  │
│   Artifact: CV Analysis Rule #42                                                 │
│   Current Success Rate: 60%                                                      │
│   Estimated New Rate: 85% (+25%)                                                 │
│                                                                                  │
│   ┌────────────────────────────────────────────────────────────────────────────┐│
│   │  Current Version (v3):                                                      ││
│   │  "Extract candidate skills from the Skills section of the CV"               ││
│   └────────────────────────────────────────────────────────────────────────────┘│
│                                                                                  │
│   ┌────────────────────────────────────────────────────────────────────────────┐│
│   │  Proposed Version (v4):                                                     ││
│   │  "Extract technical skills from ALL sections including:                     ││
│   │   - Explicit Skills section                                                 ││
│   │   - Work experience (technologies used)                                     ││
│   │   - Projects (tech stack mentioned)                                         ││
│   │   Match skills against job requirements using semantic similarity"          ││
│   └────────────────────────────────────────────────────────────────────────────┘│
│                                                                                  │
│   Evidence:                                                                      │
│   - 23 user corrections in last 30 days                                         │
│   - 35% of failures: missing tech skills                                        │
│   - Similar rule (Rule A) with tech focus: 95% success                          │
│                                                                                  │
│   Confidence: 0.82                                                               │
│                                                                                  │
│   Actions: [ Approve ] [ Test (A/B) ] [ Reject ]                                │
│                                                                                  │
└──────────────────────────────────────────────────────────────────────────────────┘
```

---

### 5.4 Approval Workflow

User-gated changes for critical artifacts.

```
                              ┌─────────────────┐
                              │    Proposal     │
                              │    Generated    │
                              └────────┬────────┘
                                       │
                                       ▼
                              ┌─────────────────┐
                              │  User Reviews   │
                              │    Proposal     │
                              └────────┬────────┘
                                       │
                    ┌──────────────────┼──────────────────┐
                    │                  │                  │
                    ▼                  ▼                  ▼
           ┌─────────────┐    ┌─────────────┐    ┌─────────────┐
           │   Approve   │    │    Test     │    │   Reject    │
           │             │    │   (A/B)     │    │             │
           └──────┬──────┘    └──────┬──────┘    └──────┬──────┘
                  │                  │                  │
                  ▼                  ▼                  ▼
           ┌─────────────┐    ┌─────────────┐    ┌─────────────┐
           │  Immediate  │    │   Start     │    │    Log      │
           │  Deploy     │    │  Experiment │    │  Rejection  │
           │             │    │             │    │  + Reason   │
           └─────────────┘    └─────────────┘    └─────────────┘
```

**Approval Actions:**

| Action         | Effect                                              |
| -------------- | --------------------------------------------------- |
| **Approve**    | New version deployed immediately, old deprecated    |
| **Test (A/B)** | Start experiment, 50/50 traffic split               |
| **Reject**     | Proposal archived with reason, learn from rejection |

---

### 5.5 A/B Testing

Validate improvements before full deployment.

```
┌─────────────────────────────────────────────────────────────────────────────────┐
│                              A/B Experiment                                      │
│                                                                                 │
│   Experiment ID: exp_789                                                        │
│   Artifact: rule_42                                                             │
│   Status: RUNNING                                                               │
│                                                                                 │
│   ┌───────────────────────────────┬───────────────────────────────┐            │
│   │         Control (v3)          │         Variant (v4)          │            │
│   │         50% traffic           │         50% traffic           │            │
│   ├───────────────────────────────┼───────────────────────────────┤            │
│   │  Executions: 45               │  Executions: 47               │            │
│   │  Success Rate: 62%            │  Success Rate: 87%            │            │
│   │  Avg Quality: 0.74            │  Avg Quality: 0.91            │            │
│   │  User Corrections: 12         │  User Corrections: 3          │            │
│   └───────────────────────────────┴───────────────────────────────┘            │
│                                                                                 │
│   Statistical Significance: 94%                                                 │
│   Minimum Required: 95%                                                         │
│   Remaining Samples: ~8                                                         │
│                                                                                 │
│   Auto-Promote: When significance >= 95%                                        │
│                                                                                 │
└─────────────────────────────────────────────────────────────────────────────────┘
```

**Experiment Lifecycle:**

```
┌────────┐     ┌────────┐     ┌────────┐     ┌────────┐
│ Create │────▶│ Running│────▶│Evaluate│────▶│ Close  │
└────────┘     └────────┘     └────────┘     └────────┘
                   │                              │
                   │ Each execution               │
                   │ assigned variant             │
                   ▼                              ▼
              ┌────────┐                    ┌──────────┐
              │ Record │                    │ Promote  │
              │Outcome │                    │ Winner   │
              └────────┘                    │   OR     │
                                            │ Rollback │
                                            └──────────┘
```

**Termination Conditions:**
1. Statistical significance >= 95% → Promote winner
2. Sample limit reached (100 executions) → Evaluate manually
3. Variant significantly worse → Auto-rollback

---

## 6. End-to-End Scenarios

### 6.1 New Task Type Setup

Complete workflow for adding a new task type with initial artifacts.

```
┌─────────────────────────────────────────────────────────────────────────────────┐
│                     Setting Up: "code_review" Task Type                          │
└─────────────────────────────────────────────────────────────────────────────────┘

Step 1: Register Task Type
─────────────────────────
Agent: register_task_type(
  task_type="code_review",
  description="Automated code review for Python projects"
)
Server: ✓ Task type "code_review" registered

Step 2: Add Best Practices
──────────────────────────
Agent: add_artifact(
  task_type="code_review",
  artifact_type="practice",
  content="Focus on: 1) Logic errors, 2) Security issues, 3) Performance...",
  metadata={"priority": "high", "author": "system"}
)
Server: ✓ Artifact created: practice_001, v1

Step 3: Add Rules
─────────────────
Agent: add_artifact(
  task_type="code_review",
  artifact_type="rule",
  content="Always check for SQL injection vulnerabilities in database queries...",
  metadata={"category": "security", "severity": "critical"}
)
Server: ✓ Artifact created: rule_001, v1

Agent: add_artifact(
  task_type="code_review",
  artifact_type="rule",
  content="Flag any function longer than 50 lines for refactoring...",
  metadata={"category": "maintainability", "severity": "warning"}
)
Server: ✓ Artifact created: rule_002, v1

Step 4: Add Prompt Template
───────────────────────────
Agent: add_artifact(
  task_type="code_review",
  artifact_type="prompt",
  content="Review the following Python code. Apply all active rules...",
  metadata={"use_case": "main_review"}
)
Server: ✓ Artifact created: prompt_001, v1

Step 5: Verify Setup
────────────────────
Agent: load_task_context(task_type="code_review")
Server: ✓ Context loaded:
  - 1 practice
  - 2 rules
  - 1 prompt
  
Ready for use!
```

---

### 6.2 Minimal Query Processing

How "analyze CV" becomes a full execution.

```
┌─────────────────────────────────────────────────────────────────────────────────┐
│                         Minimal Query: "analyze CV"                              │
└─────────────────────────────────────────────────────────────────────────────────┘

User Input: "analyze CV"
              │
              ▼
┌─────────────────────────────────────────────────────────────────────────────────┐
│ STEP 1: Query Parsing                                                            │
│                                                                                  │
│   Input: "analyze CV"                                                            │
│   Output:                                                                        │
│     - task_type: "cv_analysis"                                                   │
│     - intent: "analyze"                                                          │
│     - keywords: ["CV", "analyze"]                                                │
│     - confidence: 0.95                                                           │
└─────────────────────────────────────────────────────────────────────────────────┘
              │
              ▼
┌─────────────────────────────────────────────────────────────────────────────────┐
│ STEP 2: Context Loading                                                          │
│                                                                                  │
│   Query: task_type="cv_analysis", status="active"                                │
│                                                                                  │
│   Loaded:                                                                        │
│     Practices: 3 items                                                           │
│       - "Start with contact info extraction"                                     │
│       - "Use structured JSON output"                                             │
│       - "Compare skills to job requirements"                                     │
│                                                                                  │
│     Rules: 5 items                                                               │
│       - "Technical skills must be matched semantically"                          │
│       - "Experience calculation: end_date - start_date"                          │
│       - "Education level: highest degree counts"                                 │
│       - ...                                                                      │
│                                                                                  │
│     Prompts: 1 item                                                              │
│       - Main analysis prompt template                                            │
└─────────────────────────────────────────────────────────────────────────────────┘
              │
              ▼
┌─────────────────────────────────────────────────────────────────────────────────┐
│ STEP 3: Similar Results Search                                                   │
│                                                                                  │
│   Query: semantic search for "CV analysis"                                       │
│   Filter: artifact_type="result", last 30 days                                   │
│                                                                                  │
│   Found: 10 similar past analyses                                                │
│     1. [0.92] Senior Python Developer CV - success                               │
│     2. [0.89] Full Stack Engineer CV - success                                   │
│     3. [0.87] Data Scientist CV - partial (missing skills)                       │
│     ...                                                                          │
└─────────────────────────────────────────────────────────────────────────────────┘
              │
              ▼
┌─────────────────────────────────────────────────────────────────────────────────┐
│ STEP 4: Build Execution Context                                                  │
│                                                                                  │
│   {                                                                              │
│     "task_type": "cv_analysis",                                                  │
│     "practices": [...],                                                          │
│     "rules": [...],                                                              │
│     "prompt_template": "...",                                                    │
│     "similar_results": [...],                                                    │
│     "execution_hints": [                                                         │
│       "Previous failures often due to missing technical skills",                 │
│       "High success when using structured output format"                         │
│     ]                                                                            │
│   }                                                                              │
└─────────────────────────────────────────────────────────────────────────────────┘
              │
              ▼
┌─────────────────────────────────────────────────────────────────────────────────┐
│ STEP 5: Agent Executes Analysis                                                  │
│                                                                                  │
│   Agent uses loaded context to perform CV analysis                               │
│   Applies all rules, follows practices                                           │
│   References similar successful results for format                               │
└─────────────────────────────────────────────────────────────────────────────────┘
              │
              ▼
┌─────────────────────────────────────────────────────────────────────────────────┐
│ STEP 6: Store Result & Record Metrics                                            │
│                                                                                  │
│   add_artifact(                                                                  │
│     task_type="cv_analysis",                                                     │
│     artifact_type="result",                                                      │
│     content=<analysis_output>,                                                   │
│     metadata={                                                                   │
│       "success": true,                                                           │
│       "duration_ms": 4500,                                                       │
│       "artifacts_used": ["practice_1", "rule_1", "rule_2", ...],                │
│       "quality_indicators": {...}                                                │
│     }                                                                            │
│   )                                                                              │
│                                                                                  │
│   record_task_execution(...)                                                     │
└─────────────────────────────────────────────────────────────────────────────────┘
              │
              ▼
         ┌─────────┐
         │  User   │
         │receives │
         │ result  │
         └─────────┘
```

---

### 6.3 Self-Improving Agent Loop

Complete autonomous improvement cycle.

```
┌─────────────────────────────────────────────────────────────────────────────────┐
│                        Self-Improvement Loop                                     │
└─────────────────────────────────────────────────────────────────────────────────┘

                    ┌──────────────────────────────────────┐
                    │                                      │
                    ▼                                      │
            ┌───────────────┐                              │
            │  Execute      │                              │
            │  Tasks        │                              │
            │  (normal ops) │                              │
            └───────┬───────┘                              │
                    │                                      │
                    ▼                                      │
            ┌───────────────┐                              │
            │  Collect      │                              │
            │  Metrics      │                              │
            │  (every exec) │                              │
            └───────┬───────┘                              │
                    │                                      │
                    ▼                                      │
            ┌───────────────┐         ┌───────────────┐   │
            │  Analyze      │─────────│ No issues     │───┘
            │  Performance  │         │ found         │
            │  (weekly)     │         └───────────────┘
            └───────┬───────┘
                    │
                    │ Issues detected
                    ▼
            ┌───────────────┐
            │  Generate     │
            │  Proposals    │
            └───────┬───────┘
                    │
                    ▼
            ┌───────────────┐
            │  User         │
            │  Review       │
            └───────┬───────┘
                    │
        ┌───────────┴───────────┐
        │                       │
        ▼                       ▼
┌───────────────┐       ┌───────────────┐
│  Approved     │       │  Start A/B    │
│  (deploy)     │       │  Test         │
└───────┬───────┘       └───────┬───────┘
        │                       │
        │               ┌───────┴───────┐
        │               │               │
        │               ▼               ▼
        │       ┌───────────┐   ┌───────────┐
        │       │ Winner    │   │ Rollback  │
        │       │ (promote) │   │ (discard) │
        │       └─────┬─────┘   └───────────┘
        │             │
        └──────┬──────┘
               │
               ▼
        ┌───────────────┐
        │  Learn from   │
        │  Outcome      │
        └───────┬───────┘
                │
                │ Apply learnings to future proposals
                │
                └──────────────────────────────────────────┐
                                                           │
                    ┌──────────────────────────────────────┘
                    │
                    ▼
            ┌───────────────┐
            │  Continue     │
            │  Operations   │
            └───────────────┘
```

**Learning Loop Details:**

```
Week 1: Observe
─────────────────
- Execute 150 tasks across task types
- Collect success/failure metrics
- Record user corrections

Week 2: Analyze
─────────────────
- Run analysis engine
- Identify: Rule B has 60% success (others 85%+)
- Pattern: 35% failures miss technical skills

Week 3: Propose
─────────────────
- Generate improvement proposal
- Estimate: 60% → 85% success after update
- Evidence: 23 corrections, pattern analysis

Week 4: Test
─────────────────
- User selects "Test (A/B)"
- 50/50 traffic split
- After 92 executions:
  - Control: 62% success
  - Variant: 87% success
  - Significance: 96%

Week 5: Promote
─────────────────
- Auto-promote variant (significance > 95%)
- Deprecate old version
- Log improvement outcome

Week 6+: Learn
─────────────────
- Record: "Technical skills focus improved success by 25%"
- Apply pattern to similar rules proactively
- Reduce future proposal review burden
```

---

## 7. Data Flow Diagrams

### Complete System Data Flow

```
┌─────────────────────────────────────────────────────────────────────────────────┐
│                              DATA FLOW OVERVIEW                                  │
└─────────────────────────────────────────────────────────────────────────────────┘

                                    ┌─────────────┐
                                    │    User     │
                                    └──────┬──────┘
                                           │
                                           │ Natural language query
                                           ▼
┌──────────────────────────────────────────────────────────────────────────────────┐
│                                  AI Agent                                         │
│  ┌─────────────┐   ┌─────────────┐   ┌─────────────┐   ┌─────────────┐          │
│  │   Parse     │──▶│   Load      │──▶│   Execute   │──▶│   Store     │          │
│  │   Query     │   │   Context   │   │   Task      │   │   Result    │          │
│  └─────────────┘   └─────────────┘   └─────────────┘   └─────────────┘          │
└──────────────────────────────────────────────────────────────────────────────────┘
         │                  │                                    │
         │                  │                                    │
         ▼                  ▼                                    ▼
┌──────────────────────────────────────────────────────────────────────────────────┐
│                              MCP Server                                           │
│                                                                                  │
│  ┌─────────────────────────────────────────────────────────────────────────────┐│
│  │                              Tools Layer                                     ││
│  │  ┌───────────┐ ┌───────────┐ ┌───────────┐ ┌───────────┐ ┌───────────┐     ││
│  │  │   CRUD    │ │  Search   │ │  Version  │ │  Metrics  │ │ Proposals │     ││
│  │  │   Tools   │ │  Tools    │ │  Tools    │ │  Tools    │ │   Tools   │     ││
│  │  └───────────┘ └───────────┘ └───────────┘ └───────────┘ └───────────┘     ││
│  └─────────────────────────────────────────────────────────────────────────────┘│
│                                      │                                           │
│  ┌─────────────────────────────────────────────────────────────────────────────┐│
│  │                            Services Layer                                    ││
│  │  ┌───────────┐ ┌───────────┐ ┌───────────┐ ┌───────────┐ ┌───────────┐     ││
│  │  │ Embedding │ │  Search   │ │  Context  │ │  Version  │ │  Analysis │     ││
│  │  │  Service  │ │  Service  │ │  Loader   │ │  Service  │ │  Engine   │     ││
│  │  └───────────┘ └───────────┘ └───────────┘ └───────────┘ └───────────┘     ││
│  └─────────────────────────────────────────────────────────────────────────────┘│
│                                      │                                           │
│  ┌─────────────────────────────────────────────────────────────────────────────┐│
│  │                          Repositories Layer                                  ││
│  │  ┌─────────────────────────────┐  ┌─────────────────────────────┐          ││
│  │  │     Artifacts Repository    │  │   Task Catalog Repository   │          ││
│  │  └─────────────────────────────┘  └─────────────────────────────┘          ││
│  └─────────────────────────────────────────────────────────────────────────────┘│
│                                      │                                           │
└──────────────────────────────────────┼───────────────────────────────────────────┘
                                       │
                                       ▼
┌──────────────────────────────────────────────────────────────────────────────────┐
│                              SeekDB (Embedded)                                    │
│                                                                                  │
│  ┌────────────────────────────────────────────────────────────────────────────┐ │
│  │                              Collections                                    │ │
│  │  ┌─────────────────────────┐  ┌─────────────────────────────────────────┐ │ │
│  │  │     task_catalog        │  │              artifacts                   │ │ │
│  │  │                         │  │                                          │ │ │
│  │  │  - task_type (PK)      │  │  - artifact_id (PK)                      │ │ │
│  │  │  - description         │  │  - task_type (FK)                        │ │ │
│  │  │  - created_at          │  │  - artifact_type                         │ │ │
│  │  │  - updated_at          │  │  - version                               │ │ │
│  │  │                         │  │  - content                               │ │ │
│  │  │                         │  │  - embedding [384]                       │ │ │
│  │  │                         │  │  - metadata (JSON)                       │ │ │
│  │  │                         │  │  - status                                │ │ │
│  │  │                         │  │  - created_at                            │ │ │
│  │  └─────────────────────────┘  └─────────────────────────────────────────┘ │ │
│  └────────────────────────────────────────────────────────────────────────────┘ │
│                                                                                  │
│  Storage: ./seekdb_data/                                                         │
└──────────────────────────────────────────────────────────────────────────────────┘
```

---

## 8. Error Handling

### Error Categories & Recovery

```
┌─────────────────────────────────────────────────────────────────────────────────┐
│                           Error Handling Strategy                                │
└─────────────────────────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────────────────────────┐
│ CATEGORY 1: Validation Errors                                                    │
├─────────────────────────────────────────────────────────────────────────────────┤
│                                                                                  │
│ Error: Invalid task_type                                                         │
│ ────────────────────────                                                         │
│ Trigger: add_artifact() with unregistered task_type                              │
│ Response: Return error with list of valid task_types                             │
│ Recovery: User/agent selects valid type or registers new one                     │
│                                                                                  │
│ Error: Artifact not found                                                        │
│ ────────────────────────                                                         │
│ Trigger: get_artifact() with non-existent ID                                     │
│ Response: Return error with search suggestions                                   │
│ Recovery: Search for similar artifacts                                           │
│                                                                                  │
│ Error: Version conflict                                                          │
│ ────────────────────────                                                         │
│ Trigger: update_artifact() on already-updated artifact                           │
│ Response: Return current version, prompt for re-read                             │
│ Recovery: Reload current state, retry update                                     │
│                                                                                  │
└─────────────────────────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────────────────────────┐
│ CATEGORY 2: Search Errors                                                        │
├─────────────────────────────────────────────────────────────────────────────────┤
│                                                                                  │
│ Error: Embedding generation failed                                               │
│ ────────────────────────────────                                                 │
│ Trigger: Model not loaded or text too long                                       │
│ Response: Fallback to full-text search only                                      │
│ Recovery: Graceful degradation, log for investigation                            │
│                                                                                  │
│ Error: No results found                                                          │
│ ────────────────────────                                                         │
│ Trigger: Query matches nothing                                                   │
│ Response: Suggest broader search terms or related task_types                     │
│ Recovery: Expand search scope automatically                                      │
│                                                                                  │
└─────────────────────────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────────────────────────┐
│ CATEGORY 3: Database Errors                                                      │
├─────────────────────────────────────────────────────────────────────────────────┤
│                                                                                  │
│ Error: Database connection failed                                                │
│ ────────────────────────────────                                                 │
│ Trigger: SeekDB file locked or corrupted                                         │
│ Response: Retry with exponential backoff (3 attempts)                            │
│ Recovery: If persistent, report critical error, suggest restart                  │
│                                                                                  │
│ Error: Transaction failed                                                        │
│ ────────────────────────                                                         │
│ Trigger: ACID violation or disk full                                             │
│ Response: Rollback transaction, return to previous state                         │
│ Recovery: Report error, no partial state persisted                               │
│                                                                                  │
└─────────────────────────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────────────────────────┐
│ CATEGORY 4: A/B Testing Errors                                                   │
├─────────────────────────────────────────────────────────────────────────────────┤
│                                                                                  │
│ Error: Variant significantly underperforming                                     │
│ ─────────────────────────────────────────────                                    │
│ Trigger: New variant success rate < control - 20%                                │
│ Response: Auto-terminate experiment, rollback to control                         │
│ Recovery: Log failure, adjust proposal algorithm                                 │
│                                                                                  │
│ Error: Experiment stalled                                                        │
│ ─────────────────────────                                                        │
│ Trigger: No executions for 7 days                                                │
│ Response: Send notification, extend or close experiment                          │
│ Recovery: User decides to extend, close, or reassign traffic                     │
│                                                                                  │
└─────────────────────────────────────────────────────────────────────────────────┘
```

### Error Response Format

```json
{
  "status": "error",
  "error": {
    "code": "ARTIFACT_NOT_FOUND",
    "message": "Artifact with ID 'art_999' not found",
    "details": {
      "searched_id": "art_999",
      "suggestions": ["art_998", "art_1000"],
      "hint": "Try searching by content: search_artifacts(query='...')"
    }
  },
  "recovery": {
    "action": "search",
    "params": {"query": "related keywords"}
  }
}
```

---

## Summary

This workflow documentation covers:

1. **Core Operations** - Task types, artifacts, context management
2. **Search Capabilities** - Semantic, full-text, and hybrid search
3. **Version Control** - History, comparison, rollback
4. **Autonomous Improvement** - Metrics → Analysis → Proposals → Testing
5. **End-to-End Scenarios** - Real-world usage patterns
6. **Error Handling** - Graceful degradation and recovery

The system is designed for minimal user input while maintaining human oversight for critical changes through the approval workflow.
