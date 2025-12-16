# Validation Error Fix

## Problem
The workflow was failing with Pydantic validation errors:

```
ValidationError: 5 validation errors for ResearchSummary
faq_list.0
  Input should be a valid string [type=string_type, input_value={'question': '...', 'answer': '...'}, input_type=dict]
```

## Root Cause
The LLM (GPT-4) was returning FAQ items as structured dictionaries:
```json
{
  "faq_list": [
    {"question": "What is...", "answer": "It is..."},
    {"question": "How...", "answer": "By..."}
  ]
}
```

But the `ResearchSummary` model expected simple strings:
```python
class ResearchSummary(BaseModel):
    faq_list: List[str]  # Expected strings, got dicts!
```

## Solution

### 1. Added Field Validator
Updated `ResearchSummary` model in `backend/models/campaign.py`:

```python
class ResearchSummary(BaseModel):
    key_facts: List[str]
    topic_list: List[str]
    faq_list: List[Any]  # Now accepts both strings and dicts
    quotes_or_stats: List[str]
    
    @field_validator('faq_list', mode='before')
    @classmethod
    def validate_faq_list(cls, v):
        """Convert FAQ dictionaries to strings if needed."""
        if not v:
            return []
        
        result = []
        for item in v:
            if isinstance(item, dict):
                # Convert dict to string format
                q = item.get('question', '')
                a = item.get('answer', '')
                result.append(f"Q: {q}\nA: {a}")
            elif isinstance(item, str):
                result.append(item)
            else:
                result.append(str(item))
        return result
```

### 2. Improved Error Handling
- Added better logging in `research_agent.py`
- Added error simplification for frontend display
- Added timeout handling in background workflow

### 3. Better Progress Tracking
- Updated background workflow to show more detailed progress
- Simplified error messages for users

## How It Works Now

1. **LLM returns dicts**: `{"question": "...", "answer": "..."}`
2. **Validator converts**: `"Q: ...\nA: ..."`
3. **Model accepts**: Successfully validates as `List[str]`

## Testing

The workflow should now complete without validation errors. If you see:
- ✅ "Workflow initialized, generating strategy..."
- ✅ "Campaign generation complete"

Then it worked!

## Files Modified

1. `backend/models/campaign.py` - Added FAQ validator
2. `backend/agents/research_agent.py` - Better error handling
3. `backend/main.py` - Improved progress tracking

## Restart Required

**Important**: Restart the backend server to load the new code:

```bash
# Stop backend (Ctrl+C)
# Restart backend
cd backend
python -m uvicorn main:app --reload --port 8000
```

Frontend should auto-reload if already running.

