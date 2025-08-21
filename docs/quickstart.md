# ConvoHub Quickstart Guide

Get started with ConvoHub in 10 minutes! This guide will walk you through creating your first threaded conversation with branching and merging.

## Prerequisites

- Python 3.8+ or Node.js 16+
- ConvoHub server running (see [Installation](#installation))
- OpenAI API key (optional, for AI responses)

## Installation

### Option 1: Python SDK

```bash
# Install the Python SDK
pip install convohub

# Or install from source
git clone https://github.com/convohub/convohub-python
cd convohub-python
pip install -e .
```

### Option 2: TypeScript SDK

```bash
# Install the TypeScript SDK
npm install convohub

# Or install from source
git clone https://github.com/convohub/convohub-typescript
cd convohub-typescript
npm install
npm run build
```

## Step 1: Authentication

First, authenticate with the ConvoHub API:

```python
# Python
from convohub import ConvoHubClient

client = ConvoHubClient("http://127.0.0.1:8000")
token = client.login(
    email="admin@default.local",
    tenant_domain="default.local",
    password="test"
)
```

```typescript
// TypeScript
import { ConvoHubClient } from 'convohub';

const client = new ConvoHubClient('http://127.0.0.1:8000');
const token = await client.login(
  'admin@default.local',
  'default.local',
  'test'
);
```

## Step 2: Create a Thread

Create your first conversation thread:

```python
# Python
thread = client.create_thread(
    title="My First Research Project",
    description="Exploring different approaches to a problem"
)
print(f"Created thread: {thread.id}")
```

```typescript
// TypeScript
const thread = await client.createThread(
  'My First Research Project',
  'Exploring different approaches to a problem'
);
console.log(`Created thread: ${thread.id}`);
```

## Step 3: Create Branches

Create multiple branches to explore different approaches:

```python
# Python
# Main branch
main_branch = client.create_branch(
    thread_id=thread.id,
    name="main",
    description="Main research branch"
)

# Alternative approach branch
alt_branch = client.create_branch(
    thread_id=thread.id,
    name="alternative-approach",
    description="Exploring alternative solutions",
    created_from_branch_id=main_branch.id
)
```

```typescript
// TypeScript
// Main branch
const mainBranch = await client.createBranch(
  thread.id,
  'main',
  'Main research branch'
);

// Alternative approach branch
const altBranch = await client.createBranch(
  thread.id,
  'alternative-approach',
  'Exploring alternative solutions',
  mainBranch.id
);
```

## Step 4: Send Messages

Add messages to your branches:

```python
# Python
# Send message to main branch
response = client.send_message(
    branch_id=main_branch.id,
    role="user",
    text="What are the best practices for implementing authentication?"
)

# Send message to alternative branch
response = client.send_message(
    branch_id=alt_branch.id,
    role="user",
    text="What are the security implications of different auth methods?"
)
```

```typescript
// TypeScript
// Send message to main branch
const response = await client.sendMessage(
  mainBranch.id,
  'user',
  'What are the best practices for implementing authentication?'
);

// Send message to alternative branch
const response2 = await client.sendMessage(
  altBranch.id,
  'user',
  'What are the security implications of different auth methods?'
);
```

## Step 5: Merge Branches

Combine insights from different branches:

```python
# Python
merge = client.merge(
    thread_id=thread.id,
    source_branch_id=alt_branch.id,
    target_branch_id=main_branch.id,
    strategy="resolver"
)
print(f"Merged branches: {merge.id}")
```

```typescript
// TypeScript
const merge = await client.merge(
  thread.id,
  altBranch.id,
  mainBranch.id,
  'resolver'
);
console.log(`Merged branches: ${merge.id}`);
```

## Step 6: Compare Branches

Analyze differences between branches:

```python
# Python
# Compare message histories
diff = client.diff_messages(
    left_branch_id=main_branch.id,
    right_branch_id=alt_branch.id
)
print(f"Found {len(diff.message_ranges)} message ranges")

# Compare summaries
summary_diff = client.diff_summary(
    left_branch_id=main_branch.id,
    right_branch_id=alt_branch.id
)
print(f"Common content: {len(summary_diff.common_content.split())} words")
```

```typescript
// TypeScript
// Compare message histories
const diff = await client.diffMessages(
  mainBranch.id,
  altBranch.id
);
console.log(`Found ${diff.message_ranges?.length || 0} message ranges`);

// Compare summaries
const summaryDiff = await client.diffSummary(
  mainBranch.id,
  altBranch.id
);
console.log(`Common content: ${summaryDiff.summary_diff?.common_content.split(' ').length || 0} words`);
```

## Step 7: Get Context

Retrieve conversation context for AI integration:

```python
# Python
context = client.get_context(
    branch_id=main_branch.id,
    policy={
        "window_size": 10,
        "use_summary": True,
        "use_memory": True,
        "max_tokens": 4000
    }
)
print(f"Context has {len(context['messages_window'])} messages")
```

```typescript
// TypeScript
const context = await client.getContext(
  mainBranch.id,
  {
    window_size: 10,
    use_summary: true,
    use_memory: true,
    max_tokens: 4000
  }
);
console.log(`Context has ${context.messages_window.length} messages`);
```

## Next Steps

Congratulations! You've completed the ConvoHub quickstart. Here's what you can explore next:

1. **Advanced Examples**: Check out the [Research DAG example](../examples/research_dag.py)
2. **API Reference**: Explore the complete [API documentation](api-reference.md)
3. **Concepts**: Learn about [DAGs, branches, and merges](concepts.md)
4. **Recipes**: Find practical [use cases and recipes](recipes.md)

## Troubleshooting

### Common Issues

1. **Connection Error**: Make sure the ConvoHub server is running on `http://127.0.0.1:8000`
2. **Authentication Error**: Verify your credentials and tenant domain
3. **Merge Conflicts**: Use different idempotency keys for each merge operation

### Getting Help

- Check the [API documentation](api-reference.md)
- Review the [Postman collection](../docs/ConvoHub_API.postman_collection.json)
- Join our community discussions

---

**Time to complete**: ~10 minutes

**What you've learned**:
- ✅ Authentication and API setup
- ✅ Creating threads and branches
- ✅ Sending messages and getting AI responses
- ✅ Merging branches with different strategies
- ✅ Comparing branch differences
- ✅ Retrieving conversation context
