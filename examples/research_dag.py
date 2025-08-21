#!/usr/bin/env python3
"""
Research DAG Example

This example demonstrates a research workflow using ConvoHub:
1. Root question → 3 branches (different research approaches)
2. Merge branches → follow-up questions
3. Shows the power of branching conversations for research

Usage:
    python research_dag.py
"""

import asyncio
import sys
import os
from datetime import datetime

# Add the SDK to the path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'sdk', 'python'))

from convohub import ConvoHubClient, DiffMode

class ResearchDAGExample:
    def __init__(self, base_url: str = "http://127.0.0.1:8000"):
        self.client = ConvoHubClient(base_url)
        self.thread = None
        self.main_branch = None
        self.branches = {}
        
    def print_step(self, step: str, description: str):
        """Print a formatted step header"""
        print(f"\n{'='*60}")
        print(f"STEP {step}: {description}")
        print(f"{'='*60}")
    
    def print_branch_info(self, branch_name: str, branch_id: str):
        """Print branch information"""
        print(f"📁 {branch_name}: {branch_id}")
    
    def print_message(self, role: str, content: str):
        """Print a formatted message"""
        role_emoji = {"user": "👤", "assistant": "🤖", "system": "⚙️"}
        emoji = role_emoji.get(role, "💬")
        print(f"{emoji} {role.upper()}: {content}")
    
    def run(self):
        """Run the complete research DAG example"""
        try:
            # Step 1: Authentication
            self.print_step("1", "Authentication")
            token = self.client.login(
                email="admin@default.local",
                tenant_domain="default.local", 
                password="test"
            )
            print(f"✅ Authenticated successfully")
            
            # Step 2: Create Research Thread
            self.print_step("2", "Create Research Thread")
            self.thread = self.client.create_thread(
                title="Climate Change Impact Research",
                description="Multi-branch research on climate change impacts and solutions"
            )
            print(f"📝 Thread created: {self.thread.id}")
            print(f"   Title: {self.thread.title}")
            print(f"   Description: {self.thread.description}")
            
            # Step 3: Create Main Branch with Root Question
            self.print_step("3", "Create Main Branch with Root Question")
            self.main_branch = self.client.create_branch(
                thread_id=self.thread.id,
                name="main",
                description="Main research branch with root question"
            )
            self.print_branch_info("Main", self.main_branch.id)
            
            # Send root question
            response = self.client.send_message(
                branch_id=self.main_branch.id,
                role="user",
                text="What are the most significant impacts of climate change on global ecosystems, and what are the most promising solutions to address these challenges?"
            )
            print("🌱 Root question sent")
            self.print_message("user", "What are the most significant impacts of climate change on global ecosystems, and what are the most promising solutions to address these challenges?")
            
            # Step 4: Create Three Research Branches
            self.print_step("4", "Create Three Research Branches")
            
            # Branch 1: Scientific Research
            scientific_branch = self.client.create_branch(
                thread_id=self.thread.id,
                name="scientific-research",
                description="Focus on scientific evidence and data",
                created_from_branch_id=self.main_branch.id
            )
            self.branches["scientific"] = scientific_branch
            self.print_branch_info("Scientific Research", scientific_branch.id)
            
            # Branch 2: Economic Analysis
            economic_branch = self.client.create_branch(
                thread_id=self.thread.id,
                name="economic-analysis", 
                description="Focus on economic impacts and cost-benefit analysis",
                created_from_branch_id=self.main_branch.id
            )
            self.branches["economic"] = economic_branch
            self.print_branch_info("Economic Analysis", economic_branch.id)
            
            # Branch 3: Policy Solutions
            policy_branch = self.client.create_branch(
                thread_id=self.thread.id,
                name="policy-solutions",
                description="Focus on policy recommendations and implementation",
                created_from_branch_id=self.main_branch.id
            )
            self.branches["policy"] = policy_branch
            self.print_branch_info("Policy Solutions", policy_branch.id)
            
            # Step 5: Develop Each Branch
            self.print_step("5", "Develop Each Research Branch")
            
            # Scientific Research Branch
            print("\n🔬 Developing Scientific Research Branch:")
            response = self.client.send_message(
                branch_id=scientific_branch.id,
                role="user", 
                text="Focus on the latest scientific evidence about climate change impacts. What are the most concerning findings from recent studies?"
            )
            self.print_message("user", "Focus on the latest scientific evidence about climate change impacts. What are the most concerning findings from recent studies?")
            
            # Economic Analysis Branch
            print("\n💰 Developing Economic Analysis Branch:")
            response = self.client.send_message(
                branch_id=economic_branch.id,
                role="user",
                text="Analyze the economic costs of climate change and the financial benefits of different mitigation strategies."
            )
            self.print_message("user", "Analyze the economic costs of climate change and the financial benefits of different mitigation strategies.")
            
            # Policy Solutions Branch
            print("\n📋 Developing Policy Solutions Branch:")
            response = self.client.send_message(
                branch_id=policy_branch.id,
                role="user",
                text="What are the most effective policy interventions that governments can implement to address climate change?"
            )
            self.print_message("user", "What are the most effective policy interventions that governments can implement to address climate change?")
            
            # Step 6: Merge Branches
            self.print_step("6", "Merge Research Branches")
            
            print("🔄 Merging scientific research into main branch...")
            merge1 = self.client.merge(
                thread_id=self.thread.id,
                source_branch_id=scientific_branch.id,
                target_branch_id=self.main_branch.id,
                strategy="resolver",
                idempotency_key=f"merge-scientific-{datetime.now().timestamp()}"
            )
            print(f"✅ Scientific research merged: {merge1.id}")
            
            print("🔄 Merging economic analysis into main branch...")
            merge2 = self.client.merge(
                thread_id=self.thread.id,
                source_branch_id=economic_branch.id,
                target_branch_id=self.main_branch.id,
                strategy="resolver",
                idempotency_key=f"merge-economic-{datetime.now().timestamp()}"
            )
            print(f"✅ Economic analysis merged: {merge2.id}")
            
            print("🔄 Merging policy solutions into main branch...")
            merge3 = self.client.merge(
                thread_id=self.thread.id,
                source_branch_id=policy_branch.id,
                target_branch_id=self.main_branch.id,
                strategy="resolver",
                idempotency_key=f"merge-policy-{datetime.now().timestamp()}"
            )
            print(f"✅ Policy solutions merged: {merge3.id}")
            
            # Step 7: Follow-up Questions
            self.print_step("7", "Follow-up Questions Based on Merged Research")
            
            print("🤔 Asking follow-up questions based on merged research...")
            
            # Follow-up 1: Implementation
            response = self.client.send_message(
                branch_id=self.main_branch.id,
                role="user",
                text="Based on the scientific evidence, economic analysis, and policy recommendations we've gathered, what are the most practical next steps for immediate implementation?"
            )
            self.print_message("user", "Based on the scientific evidence, economic analysis, and policy recommendations we've gathered, what are the most practical next steps for immediate implementation?")
            
            # Follow-up 2: Stakeholder Engagement
            response = self.client.send_message(
                branch_id=self.main_branch.id,
                role="user",
                text="How can we best engage different stakeholders (governments, businesses, communities) to implement these solutions effectively?"
            )
            self.print_message("user", "How can we best engage different stakeholders (governments, businesses, communities) to implement these solutions effectively?")
            
            # Step 8: Analyze Differences
            self.print_step("8", "Analyze Branch Differences")
            
            print("📊 Analyzing differences between research approaches...")
            
            # Compare scientific vs economic approaches
            diff_response = self.client.diff_summary(
                left_branch_id=scientific_branch.id,
                right_branch_id=economic_branch.id
            )
            print(f"🔍 Scientific vs Economic Summary Diff:")
            print(f"   Common content: {len(diff_response.summary_diff.common_content.split())} words")
            print(f"   Scientific unique: {len(diff_response.summary_diff.left_only.split())} words")
            print(f"   Economic unique: {len(diff_response.summary_diff.right_only.split())} words")
            
            # Compare all branches using memory diff
            diff_response = self.client.diff_memory(
                left_branch_id=scientific_branch.id,
                right_branch_id=policy_branch.id
            )
            print(f"🧠 Scientific vs Policy Memory Diff:")
            print(f"   Added memories: {len(diff_response.memory_diff.added)}")
            print(f"   Removed memories: {len(diff_response.memory_diff.removed)}")
            print(f"   Modified memories: {len(diff_response.memory_diff.modified)}")
            print(f"   Conflicts: {len(diff_response.memory_diff.conflicts)}")
            
            # Step 9: Final Summary
            self.print_step("9", "Final Research Summary")
            
            print("📋 Getting final research summary...")
            summaries = self.client.get_summaries(self.thread.id)
            print(f"📊 Total summaries: {len(summaries.get('summaries', []))}")
            
            memories = self.client.get_memories(self.thread.id)
            print(f"🧠 Total memories: {memories.get('total_memories', 0)}")
            
            print("\n🎉 Research DAG Example Completed Successfully!")
            print(f"📁 Thread ID: {self.thread.id}")
            print(f"🌿 Main Branch: {self.main_branch.id}")
            print(f"🔬 Scientific Branch: {scientific_branch.id}")
            print(f"💰 Economic Branch: {economic_branch.id}")
            print(f"📋 Policy Branch: {policy_branch.id}")
            
        except Exception as e:
            print(f"❌ Error: {e}")
            import traceback
            traceback.print_exc()

if __name__ == "__main__":
    print("🚀 Starting ConvoHub Research DAG Example")
    print("This example demonstrates branching conversations for research workflows")
    
    example = ResearchDAGExample()
    example.run()
