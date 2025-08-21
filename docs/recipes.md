# ConvoHub Recipes

Practical recipes and use cases for ConvoHub. These examples show how to solve real-world problems using branching conversations.

## Recipe 1: RAG (Retrieval-Augmented Generation) Branch

Create a specialized branch for document-based research and retrieval.

### Use Case
You're researching a topic and want to create a branch that focuses specifically on information from documents, papers, or external sources.

### Implementation

```python
from convohub import ConvoHubClient

client = ConvoHubClient("http://127.0.0.1:8000")
client.login("admin@default.local", "default.local", "test")

# Create main research thread
thread = client.create_thread(
    title="AI Safety Research",
    description="Comprehensive research on AI safety with document-based analysis"
)

# Create main branch
main_branch = client.create_branch(
    thread_id=thread.id,
    name="main",
    description="General AI safety discussion"
)

# Create RAG branch
rag_branch = client.create_branch(
    thread_id=thread.id,
    name="document-research",
    description="Research based on specific documents and papers",
    created_from_branch_id=main_branch.id
)

# Set up RAG context in the branch
client.send_message(
    branch_id=rag_branch.id,
    role="system",
    text="""You are a research assistant focused on document analysis. 
    When answering questions, prioritize information from the following sources:
    - "Concrete Problems in AI Safety" by Amodei et al.
    - "AI Alignment: A Comprehensive Survey" 
    - Recent papers from top AI conferences
    
    Always cite specific sources and provide page numbers when possible."""
)

# Ask RAG-specific questions
client.send_message(
    branch_id=rag_branch.id,
    role="user",
    text="What are the main technical challenges mentioned in the AI safety literature?"
)

# Later, merge insights back to main branch
merge = client.merge(
    thread_id=thread.id,
    source_branch_id=rag_branch.id,
    target_branch_id=main_branch.id,
    strategy="resolver"
)
```

### TypeScript Version

```typescript
import { ConvoHubClient } from 'convohub';

const client = new ConvoHubClient('http://127.0.0.1:8000');
await client.login('admin@default.local', 'default.local', 'test');

// Create main research thread
const thread = await client.createThread(
  'AI Safety Research',
  'Comprehensive research on AI safety with document-based analysis'
);

// Create main branch
const mainBranch = await client.createBranch(
  thread.id,
  'main',
  'General AI safety discussion'
);

// Create RAG branch
const ragBranch = await client.createBranch(
  thread.id,
  'document-research',
  'Research based on specific documents and papers',
  mainBranch.id
);

// Set up RAG context
await client.sendMessage(
  ragBranch.id,
  'system',
  `You are a research assistant focused on document analysis. 
  When answering questions, prioritize information from the following sources:
  - "Concrete Problems in AI Safety" by Amodei et al.
  - "AI Alignment: A Comprehensive Survey" 
  - Recent papers from top AI conferences
  
  Always cite specific sources and provide page numbers when possible.`
);

// Ask RAG-specific questions
await client.sendMessage(
  ragBranch.id,
  'user',
  'What are the main technical challenges mentioned in the AI safety literature?'
);

// Merge insights back to main branch
const merge = await client.merge(
  thread.id,
  ragBranch.id,
  mainBranch.id,
  'resolver'
);
```

## Recipe 2: Hypothesis Testing Branch

Create branches to test different hypotheses or approaches systematically.

### Use Case
You want to explore multiple hypotheses about a problem and compare the results systematically.

### Implementation

```python
from convohub import ConvoHubClient, DiffMode

client = ConvoHubClient("http://127.0.0.1:8000")
client.login("admin@default.local", "default.local", "test")

# Create research thread
thread = client.create_thread(
    title="Market Analysis: Product Launch Strategy",
    description="Testing different hypotheses for product launch success"
)

# Create main branch with the core question
main_branch = client.create_branch(
    thread_id=thread.id,
    name="main",
    description="Core market analysis question"
)

# Ask the main question
client.send_message(
    branch_id=main_branch.id,
    role="user",
    text="What factors most influence the success of a new product launch?"
)

# Create hypothesis branches
hypotheses = [
    {
        "name": "price-sensitivity",
        "description": "Test hypothesis: Price is the primary factor",
        "focus": "Focus on pricing strategies, price elasticity, and competitive pricing analysis."
    },
    {
        "name": "marketing-channels", 
        "description": "Test hypothesis: Marketing channels are the primary factor",
        "focus": "Focus on digital marketing, traditional advertising, influencer marketing, and channel effectiveness."
    },
    {
        "name": "product-features",
        "description": "Test hypothesis: Product features are the primary factor", 
        "focus": "Focus on feature differentiation, user experience, and product-market fit."
    }
]

hypothesis_branches = {}

for hypothesis in hypotheses:
    branch = client.create_branch(
        thread_id=thread.id,
        name=hypothesis["name"],
        description=hypothesis["description"],
        created_from_branch_id=main_branch.id
    )
    
    hypothesis_branches[hypothesis["name"]] = branch
    
    # Set up hypothesis-specific context
    client.send_message(
        branch_id=branch.id,
        role="system",
        text=f"Focus your analysis on this hypothesis: {hypothesis['focus']}"
    )
    
    # Test the hypothesis
    client.send_message(
        branch_id=branch.id,
        role="user",
        text=f"Analyze how {hypothesis['name'].replace('-', ' ')} affects product launch success. Provide evidence and examples."
    )

# Compare hypotheses
print("Comparing hypothesis results...")

# Compare price vs marketing
diff = client.diff_summary(
    left_branch_id=hypothesis_branches["price-sensitivity"].id,
    right_branch_id=hypothesis_branches["marketing-channels"].id
)

print(f"Price vs Marketing Analysis:")
print(f"  Common insights: {len(diff.summary_diff.common_content.split())} words")
print(f"  Price-specific: {len(diff.summary_diff.left_only.split())} words")
print(f"  Marketing-specific: {len(diff.summary_diff.right_only.split())} words")

# Merge all insights back to main
for branch_name, branch in hypothesis_branches.items():
    merge = client.merge(
        thread_id=thread.id,
        source_branch_id=branch.id,
        target_branch_id=main_branch.id,
        strategy="resolver",
        idempotency_key=f"merge-{branch_name}-{datetime.now().timestamp()}"
    )
    print(f"Merged {branch_name} insights")

# Ask for final synthesis
client.send_message(
    branch_id=main_branch.id,
    role="user",
    text="Based on all the hypothesis testing, what are the top 3 most important factors for product launch success?"
)
```

## Recipe 3: Collaborative Research Branch

Enable multiple team members to work on different aspects of the same research.

### Use Case
A research team wants to divide work across different aspects of a project while maintaining context and ability to merge insights.

### Implementation

```python
from convohub import ConvoHubClient

client = ConvoHubClient("http://127.0.0.1:8000")
client.login("admin@default.local", "default.local", "test")

# Create collaborative research thread
thread = client.create_thread(
    title="Climate Change Impact Assessment",
    description="Multi-disciplinary research on climate change impacts"
)

# Create main coordination branch
main_branch = client.create_branch(
    thread_id=thread.id,
    name="coordination",
    description="Main coordination and synthesis branch"
)

# Create specialized branches for different team members
team_branches = {
    "scientist": client.create_branch(
        thread_id=thread.id,
        name="scientific-analysis",
        description="Scientific data analysis and modeling",
        created_from_branch_id=main_branch.id
    ),
    "economist": client.create_branch(
        thread_id=thread.id,
        name="economic-impact",
        description="Economic cost-benefit analysis",
        created_from_branch_id=main_branch.id
    ),
    "policy": client.create_branch(
        thread_id=thread.id,
        name="policy-recommendations",
        description="Policy analysis and recommendations",
        created_from_branch_id=main_branch.id
    )
}

# Set up specialized contexts for each team member
contexts = {
    "scientist": "You are a climate scientist. Focus on data analysis, modeling, and scientific evidence.",
    "economist": "You are an environmental economist. Focus on cost-benefit analysis and economic impacts.",
    "policy": "You are a policy analyst. Focus on policy implications and implementation strategies."
}

for role, branch in team_branches.items():
    client.send_message(
        branch_id=branch.id,
        role="system",
        text=contexts[role]
    )
    
    # Each team member asks their specialized question
    questions = {
        "scientist": "What are the most reliable climate models for predicting temperature changes?",
        "economist": "What are the economic costs of different climate change scenarios?",
        "policy": "What policy interventions would be most effective for climate mitigation?"
    }
    
    client.send_message(
        branch_id=branch.id,
        role="user",
        text=questions[role]
    )

# Periodic synthesis - merge insights back to main
for role, branch in team_branches.items():
    merge = client.merge(
        thread_id=thread.id,
        source_branch_id=branch.id,
        target_branch_id=main_branch.id,
        strategy="resolver",
        idempotency_key=f"merge-{role}-{datetime.now().timestamp()}"
    )
    print(f"Merged {role} insights")

# Ask for interdisciplinary synthesis
client.send_message(
    branch_id=main_branch.id,
    role="user",
    text="Synthesize the scientific, economic, and policy perspectives into a comprehensive assessment."
)
```

## Recipe 4: Decision Tree Branch

Create a structured decision-making process with multiple decision points.

### Use Case
You need to make a complex decision with multiple options and want to explore each path systematically.

### Implementation

```python
from convohub import ConvoHubClient

client = ConvoHubClient("http://127.0.0.1:8000")
client.login("admin@default.local", "default.local", "test")

# Create decision thread
thread = client.create_thread(
    title="Technology Stack Decision",
    description="Choosing the best technology stack for a new project"
)

# Create main decision branch
main_branch = client.create_branch(
    thread_id=thread.id,
    name="main-decision",
    description="Main decision process"
)

# Initial decision question
client.send_message(
    branch_id=main_branch.id,
    role="user",
    text="We need to choose a technology stack for a new web application. What are the main considerations?"
)

# Create decision branches for different approaches
decisions = [
    {
        "name": "monolithic",
        "description": "Monolithic architecture approach",
        "question": "What are the pros and cons of a monolithic architecture for our use case?"
    },
    {
        "name": "microservices",
        "description": "Microservices architecture approach", 
        "question": "What are the pros and cons of a microservices architecture for our use case?"
    },
    {
        "name": "serverless",
        "description": "Serverless architecture approach",
        "question": "What are the pros and cons of a serverless architecture for our use case?"
    }
]

decision_branches = {}

for decision in decisions:
    branch = client.create_branch(
        thread_id=thread.id,
        name=decision["name"],
        description=decision["description"],
        created_from_branch_id=main_branch.id
    )
    
    decision_branches[decision["name"]] = branch
    
    # Explore this decision path
    client.send_message(
        branch_id=branch.id,
        role="user",
        text=decision["question"]
    )
    
    # Follow up with specific considerations
    client.send_message(
        branch_id=branch.id,
        role="user",
        text="What are the specific implementation challenges and costs for this approach?"
    )

# Compare decision options
print("Comparing decision options...")

# Compare monolithic vs microservices
diff = client.diff_summary(
    left_branch_id=decision_branches["monolithic"].id,
    right_branch_id=decision_branches["microservices"].id
)

print(f"Monolithic vs Microservices:")
print(f"  Common considerations: {len(diff.summary_diff.common_content.split())} words")
print(f"  Monolithic-specific: {len(diff.summary_diff.left_only.split())} words")
print(f"  Microservices-specific: {len(diff.summary_diff.right_only.split())} words")

# Merge all insights for final decision
for decision_name, branch in decision_branches.items():
    merge = client.merge(
        thread_id=thread.id,
        source_branch_id=branch.id,
        target_branch_id=main_branch.id,
        strategy="resolver",
        idempotency_key=f"merge-{decision_name}-{datetime.now().timestamp()}"
    )

# Make final decision
client.send_message(
    branch_id=main_branch.id,
    role="user",
    text="Based on all the analysis, what is the recommended technology stack and why?"
)
```

## Recipe 5: Learning Path Branch

Create personalized learning paths for different learning styles or knowledge levels.

### Use Case
You want to create adaptive learning content that branches based on the learner's needs and preferences.

### Implementation

```python
from convohub import ConvoHubClient

client = ConvoHubClient("http://127.0.0.1:8000")
client.login("admin@default.local", "default.local", "test")

# Create learning thread
thread = client.create_thread(
    title="Machine Learning Fundamentals",
    description="Adaptive learning path for ML fundamentals"
)

# Create main learning branch
main_branch = client.create_branch(
    thread_id=thread.id,
    name="main-learning",
    description="Main learning path"
)

# Initial assessment
client.send_message(
    branch_id=main_branch.id,
    role="user",
    text="I want to learn machine learning. What should I know first?"
)

# Create specialized learning branches
learning_paths = {
    "beginner": {
        "name": "beginner-path",
        "description": "Beginner-friendly introduction to ML",
        "context": "You are teaching someone with no prior ML experience. Use simple analogies and avoid technical jargon."
    },
    "intermediate": {
        "name": "intermediate-path", 
        "description": "Intermediate ML concepts and implementation",
        "context": "You are teaching someone with basic programming knowledge. Include code examples and practical exercises."
    },
    "advanced": {
        "name": "advanced-path",
        "description": "Advanced ML theory and research",
        "context": "You are teaching someone with strong mathematical background. Focus on theory, proofs, and current research."
    }
}

learning_branches = {}

for level, path in learning_paths.items():
    branch = client.create_branch(
        thread_id=thread.id,
        name=path["name"],
        description=path["description"],
        created_from_branch_id=main_branch.id
    )
    
    learning_branches[level] = branch
    
    # Set up level-appropriate context
    client.send_message(
        branch_id=branch.id,
        role="system",
        text=path["context"]
    )
    
    # Start the learning path
    client.send_message(
        branch_id=branch.id,
        role="user",
        text=f"I'm a {level} learner. What should I focus on first in machine learning?"
    )

# Create follow-up branches for specific topics
for level, branch in learning_branches.items():
    # Create sub-branches for specific topics
    topics = ["supervised-learning", "unsupervised-learning", "neural-networks"]
    
    for topic in topics:
        sub_branch = client.create_branch(
            thread_id=thread.id,
            name=f"{level}-{topic}",
            description=f"{level.title()} {topic.replace('-', ' ')}",
            created_from_branch_id=branch.id
        )
        
        client.send_message(
            branch_id=sub_branch.id,
            role="user",
            text=f"Teach me about {topic.replace('-', ' ')} at a {level} level."
        )

# Merge insights for comprehensive learning
for level, branch in learning_branches.items():
    merge = client.merge(
        thread_id=thread.id,
        source_branch_id=branch.id,
        target_branch_id=main_branch.id,
        strategy="resolver",
        idempotency_key=f"merge-{level}-{datetime.now().timestamp()}"
    )

# Create personalized learning plan
client.send_message(
    branch_id=main_branch.id,
    role="user",
    text="Create a personalized learning plan that adapts to different skill levels and learning styles."
)
```

## Best Practices

### 1. Branch Naming
- Use descriptive, consistent naming conventions
- Include purpose or focus in branch names
- Use hyphens or underscores for multi-word names

### 2. Context Management
- Set up appropriate system messages for each branch
- Use clear, focused questions
- Maintain context across related branches

### 3. Merge Strategy Selection
- Use `append-last` for simple concatenation
- Use `resolver` for intelligent synthesis
- Always use unique idempotency keys

### 4. Comparison and Analysis
- Use appropriate diff modes (summary, memory, messages)
- Compare branches systematically
- Document insights and findings

### 5. Iterative Refinement
- Start with broad questions, then narrow down
- Create follow-up branches based on initial findings
- Merge insights periodically for synthesis

## Next Steps

- Try these recipes with your own use cases
- Explore the [Research DAG Example](../examples/research_dag.py) for a complete workflow
- Check out the [API Reference](api-reference.md) for more advanced features
- Join our community to share your own recipes and use cases
