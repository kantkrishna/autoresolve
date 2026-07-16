```mermaid
sequenceDiagram
    participant Agent as Execution Agent
    participant Check as SQLite Checkpointer
    participant Slack as Slack API
    participant Human as SRE (Human)
    participant Git as GitHub
    
    Agent->>Git: Draft PR to bump memory limits
    Agent->>Check: Pause Graph Execution (Interrupt)
    Check->>Slack: Send PR Link & Approval Request
    Human->>Slack: Clicks "Approve"
    Slack->>Check: Resume Graph State
    Check->>Agent: Merge PR