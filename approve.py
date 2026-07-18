import asyncio
import sys
from src.agents.graph import app

async def approve_execution(incident_id: str):
    config = {"configurable": {"thread_id": incident_id}}
    
    # 1. Query PostgreSQL asynchronously
    state = await app.aget_state(config)
    
    if not state.next:
        print(f"❌ Incident {incident_id} has no pending interruptions.")
        print("It either finished executing or hasn't reached the execution node yet.")
        return
        
    print(f"✅ Found paused graph for {incident_id}.")
    print(f"⏸️  Paused right before executing: {state.next}")
    print("🚀 Human Approval received. Resuming execution and triggering GitHub MCP...\n")
    
    # 2. Resume the graph asynchronously
    async for output in app.astream(None, config):
        for key, value in output.items():
            print(f"Finished node: {key}")
            
    print("\n🎉 Execution complete! Check your GitHub repository for the drafted Pull Request.")

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python approve.py <INCIDENT_ID>")
        sys.exit(1)
        
    incident_id = sys.argv[1]
    asyncio.run(approve_execution(incident_id))