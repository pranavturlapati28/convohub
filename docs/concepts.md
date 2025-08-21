# ConvoHub Concepts

This guide explains the core concepts behind ConvoHub: Directed Acyclic Graphs (DAGs), branches, merges, and how they enable powerful conversation management.

## What is ConvoHub?

ConvoHub is a conversation management system that treats conversations as **Directed Acyclic Graphs (DAGs)** rather than linear threads. This allows you to:

- **Branch** conversations to explore different topics or approaches
- **Merge** branches to combine insights and findings
- **Compare** different conversation paths
- **Maintain context** across complex, multi-threaded discussions

## Core Concepts

### 1. Threads

A **thread** is the top-level container for a conversation. Think of it as a project or research topic that can contain multiple branches.

```
Thread: "Climate Change Research"
├── Branch: "Scientific Evidence"
├── Branch: "Economic Impact" 
└── Branch: "Policy Solutions"
```

### 2. Branches

A **branch** is a conversation path within a thread. Branches can be created from other branches, forming a tree-like structure.

**Key characteristics:**
- Each branch has a unique message history
- Branches can be created from any point in another branch
- Branches maintain their own context and memory
- Multiple branches can exist simultaneously

**Example:**
```
Main Branch: "What are climate change impacts?"
├── Branch A: "Focus on scientific evidence"
├── Branch B: "Focus on economic costs"
└── Branch C: "Focus on policy solutions"
```

### 3. Messages

**Messages** are the individual exchanges within a branch. Each message has:
- A **role** (user, assistant, system)
- **Content** (text, structured data)
- **Metadata** (timestamps, relationships)

Messages form a linear sequence within each branch, but the overall conversation structure is a DAG.

### 4. Directed Acyclic Graph (DAG)

A **DAG** is a mathematical structure where:
- **Directed**: Connections have direction (parent → child)
- **Acyclic**: No circular references or loops
- **Graph**: Nodes connected by edges

In ConvoHub, the DAG structure enables:

```
Thread
├── Branch A (root)
│   ├── Message 1
│   └── Message 2
├── Branch B (from A)
│   ├── Message 1 (copied from A)
│   ├── Message 2 (copied from A)
│   ├── Message 3 (new)
│   └── Message 4 (new)
└── Branch C (from A)
    ├── Message 1 (copied from A)
    ├── Message 2 (copied from A)
    └── Message 5 (new)
```

### 5. Merges

A **merge** combines two branches by:
1. Finding the **Lowest Common Ancestor (LCA)** - the last shared message
2. Identifying **deltas** - messages unique to each branch
3. Applying a **merge strategy** to combine the content

**Merge Strategies:**
- **`append-last`**: Simple concatenation of summaries and union of memories
- **`resolver`**: LLM-powered intelligent merging with conflict resolution

### 6. Context Building

**Context** is the information available to the AI when generating responses. ConvoHub builds context by:

1. **Message Window**: Recent messages (configurable size)
2. **Summary**: Rolling summary of the conversation
3. **Memory**: Structured facts and preferences extracted from the conversation
4. **System Messages**: Instructions and configuration

## How It All Works Together

### Example: Research Workflow

1. **Create Thread**: "AI Safety Research"
2. **Create Main Branch**: Start with the core question
3. **Branch Out**: Create specialized branches for different aspects
4. **Develop Each Branch**: Add messages and get AI responses
5. **Merge Insights**: Combine findings from different branches
6. **Follow Up**: Ask new questions based on merged knowledge

### Visual Example

```
Thread: "AI Safety Research"
│
├── Main Branch
│   ├── "What are the main AI safety concerns?"
│   ├── "How do we measure AI safety?"
│   └── [Merged from other branches]
│
├── Technical Branch
│   ├── "What are the main AI safety concerns?"
│   ├── "Focus on technical alignment issues"
│   ├── "Explain reward hacking"
│   └── "Discuss control problems"
│
├── Policy Branch
│   ├── "What are the main AI safety concerns?"
│   ├── "Focus on policy and governance"
│   ├── "Regulatory approaches"
│   └── "International coordination"
│
└── Ethics Branch
    ├── "What are the main AI safety concerns?"
    ├── "Focus on ethical considerations"
    ├── "Value alignment"
    └── "Human-AI interaction"
```

## Advanced Concepts

### 1. Lowest Common Ancestor (LCA)

The LCA is the last message shared between two branches. It's used to:
- Determine what content is unique to each branch
- Calculate the merge delta
- Organize message ranges for comparison

### 2. Content-Based Matching

ConvoHub uses content-based matching to find LCAs by comparing:
- Message text content
- Message role (user/assistant)
- Timestamps and ordering

### 3. Three-Way Diff

When comparing branches, ConvoHub performs three-way diffs:
- **Base**: Common ancestor content
- **Left**: Content unique to left branch
- **Right**: Content unique to right branch

### 4. Memory and Summaries

**Memory**: Structured facts extracted from conversations
- User preferences
- Key facts and data
- Contextual information

**Summaries**: Rolling summaries that capture conversation essence
- Updated after each assistant message
- Target token count for efficiency
- Preserved across branches and merges

### 5. Rate Limiting and Quotas

ConvoHub includes built-in rate limiting:
- **Token bucket algorithm** for rate limiting
- **Daily quotas** for different operation types
- **Multi-tenant isolation** with tenant-specific limits

## Use Cases

### 1. Research and Analysis
- Explore multiple hypotheses simultaneously
- Compare different methodologies
- Merge findings from different approaches

### 2. Decision Making
- Evaluate different options in parallel
- Compare pros and cons systematically
- Merge insights for final decisions

### 3. Collaborative Work
- Multiple team members work on different aspects
- Merge individual contributions
- Maintain context across team members

### 4. Learning and Education
- Explore different learning paths
- Compare different explanations
- Build comprehensive understanding

## Benefits of the DAG Approach

1. **Non-linear Thinking**: Break free from linear conversation constraints
2. **Parallel Exploration**: Explore multiple paths simultaneously
3. **Structured Comparison**: Systematically compare different approaches
4. **Context Preservation**: Maintain context across complex discussions
5. **Scalable Collaboration**: Support multiple contributors and viewpoints
6. **Intelligent Merging**: Combine insights intelligently with AI assistance

## Next Steps

- Try the [Quickstart Guide](quickstart.md) to see these concepts in action
- Explore [Recipes](recipes.md) for practical use cases
- Check out the [Research DAG Example](../examples/research_dag.py) for a complete workflow
