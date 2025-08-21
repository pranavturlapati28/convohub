# ConvoHub API cURL Snippets

Complete collection of cURL commands for every ConvoHub API endpoint. Use these snippets to test the API directly or integrate with your applications.

## Authentication

### Login
```bash
curl -X POST "http://127.0.0.1:8000/v1/auth/login" \
  -H "Content-Type: application/json" \
  -d '{
    "email": "admin@default.local",
    "tenant_domain": "default.local",
    "password": "test"
  }'
```

**Response:**
```json
{
  "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "token_type": "bearer",
  "user": {
    "id": "00000000-0000-0000-0000-000000000001",
    "email": "admin@default.local",
    "name": "Admin User",
    "role": "admin"
  }
}
```

## Threads

### Create Thread
```bash
curl -X POST "http://127.0.0.1:8000/v1/threads" \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN" \
  -d '{
    "title": "Research Project",
    "description": "Multi-branch research on climate change"
  }'
```

### Get Thread Summaries
```bash
curl -X GET "http://127.0.0.1:8000/v1/threads/THREAD_ID/summaries" \
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN"
```

### Get Thread Memories
```bash
curl -X GET "http://127.0.0.1:8000/v1/threads/THREAD_ID/memories" \
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN"
```

## Branches

### Create Branch
```bash
curl -X POST "http://127.0.0.1:8000/v1/threads/THREAD_ID/branches" \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN" \
  -d '{
    "name": "main",
    "description": "Main research branch",
    "created_from_branch_id": null
  }'
```

### Create Branch from Another Branch
```bash
curl -X POST "http://127.0.0.1:8000/v1/threads/THREAD_ID/branches" \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN" \
  -d '{
    "name": "alternative-approach",
    "description": "Exploring alternative solutions",
    "created_from_branch_id": "SOURCE_BRANCH_ID"
  }'
```

## Messages

### Send Message
```bash
curl -X POST "http://127.0.0.1:8000/v1/branches/BRANCH_ID/messages" \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN" \
  -d '{
    "role": "user",
    "text": "What are the impacts of climate change?"
  }'
```

### Send Message with Idempotency Key
```bash
curl -X POST "http://127.0.0.1:8000/v1/branches/BRANCH_ID/messages?idempotency_key=msg-123" \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN" \
  -d '{
    "role": "user",
    "text": "What are the impacts of climate change?"
  }'
```

### List Messages
```bash
curl -X GET "http://127.0.0.1:8000/v1/branches/BRANCH_ID/messages?limit=50&cursor=" \
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN"
```

### List Messages with Pagination
```bash
curl -X GET "http://127.0.0.1:8000/v1/branches/BRANCH_ID/messages?limit=20&cursor=NEXT_CURSOR" \
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN"
```

## Merge

### Merge Branches
```bash
curl -X POST "http://127.0.0.1:8000/v1/merge?idempotency_key=merge-123" \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN" \
  -d '{
    "thread_id": "THREAD_ID",
    "source_branch_id": "SOURCE_BRANCH_ID",
    "target_branch_id": "TARGET_BRANCH_ID",
    "strategy": "resolver"
  }'
```

### Merge with Append-Last Strategy
```bash
curl -X POST "http://127.0.0.1:8000/v1/merge?idempotency_key=merge-append-123" \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN" \
  -d '{
    "thread_id": "THREAD_ID",
    "source_branch_id": "SOURCE_BRANCH_ID",
    "target_branch_id": "TARGET_BRANCH_ID",
    "strategy": "append-last"
  }'
```

### Get Merge Strategies
```bash
curl -X GET "http://127.0.0.1:8000/v1/merge/strategies" \
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN"
```

## Diff

### General Diff (Messages Mode)
```bash
curl -X GET "http://127.0.0.1:8000/v1/diff?left=LEFT_BRANCH_ID&right=RIGHT_BRANCH_ID&mode=messages" \
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN"
```

### General Diff (Summary Mode)
```bash
curl -X GET "http://127.0.0.1:8000/v1/diff?left=LEFT_BRANCH_ID&right=RIGHT_BRANCH_ID&mode=summary" \
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN"
```

### General Diff (Memory Mode)
```bash
curl -X GET "http://127.0.0.1:8000/v1/diff?left=LEFT_BRANCH_ID&right=RIGHT_BRANCH_ID&mode=memory" \
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN"
```

### Memory Diff (Specialized Endpoint)
```bash
curl -X GET "http://127.0.0.1:8000/v1/diff/memory?left=LEFT_BRANCH_ID&right=RIGHT_BRANCH_ID" \
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN"
```

### Summary Diff (Specialized Endpoint)
```bash
curl -X GET "http://127.0.0.1:8000/v1/diff/summary?left=LEFT_BRANCH_ID&right=RIGHT_BRANCH_ID" \
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN"
```

### Message Ranges Diff (Specialized Endpoint)
```bash
curl -X GET "http://127.0.0.1:8000/v1/diff/messages?left=LEFT_BRANCH_ID&right=RIGHT_BRANCH_ID" \
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN"
```

## Context

### Get Context
```bash
curl -X GET "http://127.0.0.1:8000/v1/context/BRANCH_ID" \
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN"
```

### Get Context with Policy
```bash
curl -X GET "http://127.0.0.1:8000/v1/context/BRANCH_ID?policy=%7B%22window_size%22%3A10%2C%22use_summary%22%3Atrue%2C%22use_memory%22%3Atrue%7D" \
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN"
```

**Note:** The policy parameter is URL-encoded JSON: `{"window_size":10,"use_summary":true,"use_memory":true}`

## Edges (Message DAG)

### Add Edge
```bash
curl -X POST "http://127.0.0.1:8000/v1/messages/MESSAGE_ID/edges" \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN" \
  -d '{
    "target_message_id": "TARGET_MESSAGE_ID",
    "edge_type": "parent"
  }'
```

### Get Edges
```bash
curl -X GET "http://127.0.0.1:8000/v1/messages/MESSAGE_ID/edges" \
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN"
```

### Remove Edge
```bash
curl -X DELETE "http://127.0.0.1:8000/v1/messages/MESSAGE_ID/edges?target_message_id=TARGET_MESSAGE_ID" \
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN"
```

## Usage and Quotas

### Get Usage Summary
```bash
curl -X GET "http://127.0.0.1:8000/v1/usage" \
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN"
```

### Get Tenant Usage Summary
```bash
curl -X GET "http://127.0.0.1:8000/v1/usage/tenant" \
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN"
```

### Get Specific Usage Type
```bash
curl -X GET "http://127.0.0.1:8000/v1/usage/messages" \
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN"
```

## Health and System

### Health Check
```bash
curl -X GET "http://127.0.0.1:8000/health"
```

### OpenAPI Schema
```bash
curl -X GET "http://127.0.0.1:8000/openapi.json"
```

## Complete Workflow Example

Here's a complete workflow using cURL commands:

```bash
# 1. Login and get token
TOKEN=$(curl -s -X POST "http://127.0.0.1:8000/v1/auth/login" \
  -H "Content-Type: application/json" \
  -d '{
    "email": "admin@default.local",
    "tenant_domain": "default.local",
    "password": "test"
  }' | jq -r '.access_token')

echo "Token: $TOKEN"

# 2. Create thread
THREAD_RESPONSE=$(curl -s -X POST "http://127.0.0.1:8000/v1/threads" \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer $TOKEN" \
  -d '{
    "title": "Research Project",
    "description": "Multi-branch research"
  }')

THREAD_ID=$(echo $THREAD_RESPONSE | jq -r '.id')
echo "Thread ID: $THREAD_ID"

# 3. Create main branch
MAIN_BRANCH_RESPONSE=$(curl -s -X POST "http://127.0.0.1:8000/v1/threads/$THREAD_ID/branches" \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer $TOKEN" \
  -d '{
    "name": "main",
    "description": "Main research branch"
  }')

MAIN_BRANCH_ID=$(echo $MAIN_BRANCH_RESPONSE | jq -r '.id')
echo "Main Branch ID: $MAIN_BRANCH_ID"

# 4. Send message to main branch
MESSAGE_RESPONSE=$(curl -s -X POST "http://127.0.0.1:8000/v1/branches/$MAIN_BRANCH_ID/messages" \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer $TOKEN" \
  -d '{
    "role": "user",
    "text": "What are the main challenges in AI safety?"
  }')

echo "Message sent: $MESSAGE_RESPONSE"

# 5. Create alternative branch
ALT_BRANCH_RESPONSE=$(curl -s -X POST "http://127.0.0.1:8000/v1/threads/$THREAD_ID/branches" \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer $TOKEN" \
  -d '{
    "name": "alternative",
    "description": "Alternative approach",
    "created_from_branch_id": "'$MAIN_BRANCH_ID'"
  }')

ALT_BRANCH_ID=$(echo $ALT_BRANCH_RESPONSE | jq -r '.id')
echo "Alternative Branch ID: $ALT_BRANCH_ID"

# 6. Send message to alternative branch
curl -s -X POST "http://127.0.0.1:8000/v1/branches/$ALT_BRANCH_ID/messages" \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer $TOKEN" \
  -d '{
    "role": "user",
    "text": "Focus on technical alignment issues"
  }'

# 7. Compare branches
DIFF_RESPONSE=$(curl -s -X GET "http://127.0.0.1:8000/v1/diff?left=$MAIN_BRANCH_ID&right=$ALT_BRANCH_ID&mode=messages" \
  -H "Authorization: Bearer $TOKEN")

echo "Diff result: $DIFF_RESPONSE"

# 8. Merge branches
MERGE_RESPONSE=$(curl -s -X POST "http://127.0.0.1:8000/v1/merge?idempotency_key=merge-$(date +%s)" \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer $TOKEN" \
  -d '{
    "thread_id": "'$THREAD_ID'",
    "source_branch_id": "'$ALT_BRANCH_ID'",
    "target_branch_id": "'$MAIN_BRANCH_ID'",
    "strategy": "resolver"
  }')

echo "Merge result: $MERGE_RESPONSE"
```

## Environment Variables

For easier testing, you can set environment variables:

```bash
# Set base URL and token
export CONVOHUB_BASE_URL="http://127.0.0.1:8000"
export CONVOHUB_TOKEN="your_access_token_here"

# Use in commands
curl -X GET "$CONVOHUB_BASE_URL/v1/threads" \
  -H "Authorization: Bearer $CONVOHUB_TOKEN"
```

## Error Handling

### Check for Errors
```bash
# Add -v flag for verbose output
curl -v -X POST "http://127.0.0.1:8000/v1/threads" \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer $TOKEN" \
  -d '{"title": "Test"}'

# Check HTTP status code
HTTP_CODE=$(curl -s -o /dev/null -w "%{http_code}" \
  -X GET "http://127.0.0.1:8000/health")
echo "HTTP Status: $HTTP_CODE"
```

### Common Error Responses

**401 Unauthorized:**
```json
{
  "detail": "Not authenticated"
}
```

**422 Validation Error:**
```json
{
  "detail": [
    {
      "loc": ["body", "title"],
      "msg": "field required",
      "type": "value_error.missing"
    }
  ]
}
```

**409 Conflict (Idempotency):**
```json
{
  "detail": "Operation with key 'merge-123' is already in progress"
}
```

## Rate Limiting

### Check Rate Limit Headers
```bash
curl -I -X POST "http://127.0.0.1:8000/v1/branches/BRANCH_ID/messages" \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer $TOKEN" \
  -d '{"role": "user", "text": "test"}'
```

**Response headers:**
```
X-RateLimit-Limit: 100
X-RateLimit-Remaining: 99
X-RateLimit-Reset: 1640995200
Retry-After: 60
```

## Tips and Best Practices

1. **Always use idempotency keys** for POST operations to avoid duplicates
2. **Check rate limit headers** to avoid 429 errors
3. **Use jq for JSON parsing** in shell scripts
4. **Store tokens securely** and don't commit them to version control
5. **Use environment variables** for configuration
6. **Handle errors gracefully** by checking HTTP status codes
7. **Use pagination** for large result sets
8. **Test with small data first** before running large operations

## Next Steps

- Import the [Postman collection](ConvoHub_API.postman_collection.json) for GUI testing
- Try the [Python SDK](../sdk/python/) for programmatic access
- Try the [TypeScript SDK](../sdk/typescript/) for Node.js applications
- Check out the [Recipes](recipes.md) for practical use cases
