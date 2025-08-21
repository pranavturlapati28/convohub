# ConvoHub SDKs

This directory contains the official SDKs for ConvoHub, providing easy-to-use client libraries for Python and TypeScript.

## Overview

ConvoHub SDKs provide a simple, intuitive interface for interacting with the ConvoHub API. They handle authentication, request formatting, response parsing, and provide type safety.

## Available SDKs

### Python SDK

**Location**: `python/`

A Python client library for ConvoHub with full type hints and comprehensive functionality.

**Features:**
- Full type hints and dataclass models
- Automatic authentication handling
- Comprehensive error handling
- Support for all API endpoints
- Easy-to-use interface

**Installation:**
```bash
# From source
cd python
pip install -e .

# Or install dependencies only
pip install requests
```

**Quick Start:**
```python
from convohub import ConvoHubClient

# Initialize client
client = ConvoHubClient("http://127.0.0.1:8000")

# Authenticate
token = client.login("admin@default.local", "default.local", "test")

# Create thread
thread = client.create_thread("My Research", "Exploring different approaches")

# Create branch
branch = client.create_branch(thread.id, "main", "Main research branch")

# Send message
response = client.send_message(branch.id, "user", "What are the main challenges?")

# Merge branches
merge = client.merge(thread.id, source_branch.id, target_branch.id, "resolver")

# Compare branches
diff = client.diff(left_branch.id, right_branch.id, DiffMode.MESSAGES)
```

### TypeScript SDK

**Location**: `typescript/`

A TypeScript client library for ConvoHub with full type safety and modern async/await patterns.

**Features:**
- Full TypeScript type definitions
- Modern async/await API
- Comprehensive error handling
- Support for all API endpoints
- Model factory classes

**Installation:**
```bash
# From source
cd typescript
npm install
npm run build

# Or install dependencies only
npm install
```

**Quick Start:**
```typescript
import { ConvoHubClient } from 'convohub';

// Initialize client
const client = new ConvoHubClient('http://127.0.0.1:8000');

// Authenticate
const token = await client.login('admin@default.local', 'default.local', 'test');

// Create thread
const thread = await client.createThread('My Research', 'Exploring different approaches');

// Create branch
const branch = await client.createBranch(thread.id, 'main', 'Main research branch');

// Send message
const response = await client.sendMessage(branch.id, 'user', 'What are the main challenges?');

// Merge branches
const merge = await client.merge(thread.id, sourceBranch.id, targetBranch.id, 'resolver');

// Compare branches
const diff = await client.diff(leftBranch.id, rightBranch.id, DiffMode.MESSAGES);
```

## Core Features

Both SDKs provide the following core functionality:

### Authentication
- JWT token-based authentication
- Automatic token management
- Multi-tenant support

### Thread Management
- Create and manage conversation threads
- Thread metadata and organization

### Branch Management
- Create branches from other branches
- Branch metadata and relationships
- DAG structure support

### Message Handling
- Send messages with automatic AI responses
- Message pagination and filtering
- Message DAG edge management

### Merge Operations
- Intelligent branch merging
- Multiple merge strategies (append-last, resolver)
- Idempotency support

### Diff and Comparison
- Three-way diff for memories
- Summary comparison
- Message range analysis
- Multiple diff modes

### Context Building
- Intelligent context assembly
- Configurable context policies
- Summary and memory integration

### Rate Limiting
- Built-in rate limit handling
- Quota management
- Retry logic

## API Coverage

Both SDKs support all ConvoHub API endpoints:

### Core Operations
- ✅ Authentication (`/v1/auth/login`)
- ✅ Threads (`/v1/threads`)
- ✅ Branches (`/v1/threads/{id}/branches`)
- ✅ Messages (`/v1/branches/{id}/messages`)
- ✅ Merge (`/v1/merge`)
- ✅ Diff (`/v1/diff`, `/v1/diff/memory`, `/v1/diff/summary`, `/v1/diff/messages`)

### Advanced Features
- ✅ Context (`/v1/context/{branch_id}`)
- ✅ Summaries (`/v1/threads/{id}/summaries`)
- ✅ Memories (`/v1/threads/{id}/memories`)
- ✅ Edges (`/v1/messages/{id}/edges`)
- ✅ Usage (`/v1/usage`)
- ✅ Health (`/health`)
- ✅ OpenAPI Schema (`/openapi.json`)

## Error Handling

Both SDKs provide comprehensive error handling:

```python
# Python
try:
    thread = client.create_thread("My Thread")
except Exception as e:
    print(f"Error: {e}")
```

```typescript
// TypeScript
try {
  const thread = await client.createThread('My Thread');
} catch (error) {
  console.error('Error:', error);
}
```

## Type Safety

### Python
- Full type hints throughout
- Dataclass models for all entities
- Enum types for constants
- Optional type support

### TypeScript
- Complete TypeScript definitions
- Interface-based models
- Enum types for constants
- Generic type support

## Examples

### Research Workflow
```python
# Python
from convohub import ConvoHubClient, DiffMode

client = ConvoHubClient("http://127.0.0.1:8000")
client.login("admin@default.local", "default.local", "test")

# Create research thread
thread = client.create_thread("AI Safety Research", "Multi-branch research")

# Create main branch
main_branch = client.create_branch(thread.id, "main", "Main research")

# Create specialized branches
scientific_branch = client.create_branch(
    thread.id, "scientific", "Scientific analysis", 
    created_from_branch_id=main_branch.id
)

# Develop each branch
client.send_message(main_branch.id, "user", "What are AI safety concerns?")
client.send_message(scientific_branch.id, "user", "Focus on technical alignment")

# Compare approaches
diff = client.diff_summary(main_branch.id, scientific_branch.id)

# Merge insights
merge = client.merge(thread.id, scientific_branch.id, main_branch.id, "resolver")
```

```typescript
// TypeScript
import { ConvoHubClient, DiffMode } from 'convohub';

const client = new ConvoHubClient('http://127.0.0.1:8000');
await client.login('admin@default.local', 'default.local', 'test');

// Create research thread
const thread = await client.createThread('AI Safety Research', 'Multi-branch research');

// Create main branch
const mainBranch = await client.createBranch(thread.id, 'main', 'Main research');

// Create specialized branches
const scientificBranch = await client.createBranch(
  thread.id, 'scientific', 'Scientific analysis', mainBranch.id
);

// Develop each branch
await client.sendMessage(mainBranch.id, 'user', 'What are AI safety concerns?');
await client.sendMessage(scientificBranch.id, 'user', 'Focus on technical alignment');

// Compare approaches
const diff = await client.diffSummary(mainBranch.id, scientificBranch.id);

// Merge insights
const merge = await client.merge(thread.id, scientificBranch.id, mainBranch.id, 'resolver');
```

## Development

### Python SDK Development
```bash
cd python

# Install development dependencies
pip install -e ".[dev]"

# Run tests
pytest

# Format code
black convohub/
isort convohub/

# Type checking
mypy convohub/
```

### TypeScript SDK Development
```bash
cd typescript

# Install dependencies
npm install

# Build
npm run build

# Run tests
npm test

# Format code
npm run format

# Lint
npm run lint
```

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests
5. Ensure all tests pass
6. Submit a pull request

## Documentation

- [Quickstart Guide](../../docs/quickstart.md)
- [API Reference](../../docs/api-reference.md)
- [Concepts](../../docs/concepts.md)
- [Recipes](../../docs/recipes.md)
- [cURL Snippets](../../docs/curl_snippets.md)

## Support

- Check the [documentation](../../docs/)
- Review the [examples](../examples/)
- Try the [Research DAG example](../examples/research_dag.py)
- Import the [Postman collection](../../docs/ConvoHub_API.postman_collection.json)

## License

MIT License - see LICENSE file for details.
