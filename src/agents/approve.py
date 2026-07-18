import sys
from src.agents.graph import app as agent_app

def approve_fix(thread_id: str):
    print(f"👍 Human SRE Approved the fix for Incident: {thread_id}")
    thread_config = {"configurable": {"thread_id": thread_id}}
    
    # Passing 'None' to invoke tells LangGraph to resume exactly where it paused!
    for event in agent_app.stream(None, config=thread_config):
        for node_name, node_state in event.items():
            print(f"🚀 Resumed and Completed Node: [{node_name}]")
            
    print("✅ Incident Fully Resolved and Closed!")

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: poetry run python -m src.agents.approve <THREAD_ID>")
        sys.exit(1)
    approve_fix(sys.argv[1])