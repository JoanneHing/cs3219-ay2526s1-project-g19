# Session Service - Database Schema & API Overview

## API Endpoints Overview

### History Management
- `GET /api/history` - Get all history entries for the authenticated user
- `GET /api/history/{history_id}` - Get specific history entry details
- `DELETE /api/history/{history_id}` - Delete a history entry (optional)

## Event Handling
- QuestionChosen Event - Creates and stores session id, publishes SessionCreated event
- SessionEnd Event - Stores session metadata in SessionMetadata Table

## Database Schema

### Session Table
```sql
CREATE TABLE sessions (
    session_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    created_at TIMESTAMP NOT NULL DEFAULT NOW(),
    is_active BOOLEAN DEFAULT TRUE,
    language VARCHAR(10) NOT NULL
);

CREATE TABLE session_users (
    session_id UUID NOT NULL REFERENCES sessions(session_id) ON DELETE CASCADE,
    user_id UUID NOT NULL,
    PRIMARY KEY (session_id, user_id)
);

CREATE TABLE session_metadata (
    session_id UUID NOT NULL REFERENCES sessions(session_id) ON DELETE CASCADE,
    question_id UUID,
    time_taken BIGINT,
    attempts INT,
    PRIMARY KEY (session_id)
);
```
