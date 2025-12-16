"""
Approval Agent
Manages human-in-the-loop approval workflow.
"""
from typing import Any, Dict, Optional
try:
    from backend.agents.base import BaseAgent
    from backend.models.campaign import ContentCalendar, ContentCalendarEntry
except ModuleNotFoundError:
    from agents.base import BaseAgent
    from models.campaign import ContentCalendar, ContentCalendarEntry
from datetime import datetime

class ApprovalAgent(BaseAgent):
    """Agent that manages content approval workflow."""
    
    def __init__(self):
        super().__init__(
            name="ApprovalAgent",
            instructions="You are an Approval Workflow Manager. Coordinate content approval processes."
        )
    
    async def process(self, context: Any) -> Dict[str, Any]:
        """
        Mark content for approval and return approval-ready calendar.
        
        Args:
            context: Dict with 'calendar' (ContentCalendar)
            
        Returns:
            Dict with 'calendar' (with pending_approval status) and 'approval_queue'
        """
        calendar = context.get("calendar")
        if not calendar:
            raise ValueError("Calendar is required")
        
        # Update all entries to pending_approval status
        approval_queue = []
        for entry in calendar.entries:
            entry.status = "pending_approval"
            entry.approval_status = "pending"
            
            approval_queue.append({
                "entry_id": id(entry),
                "date": entry.date,
                "time": entry.time,
                "channel": entry.channel,
                "post_type": entry.post_type,
                "caption_ref": entry.caption_ref,
                "image_brief_ref": entry.image_brief_ref,
                "video_script_ref": entry.video_script_ref
            })
        
        return {
            "calendar": calendar,
            "approval_queue": approval_queue,
            "total_pending": len(approval_queue),
            "status": "awaiting_approval"
        }
    
    async def approve_entry(
        self,
        entry_id: str,
        approved_by: str,
        calendar: ContentCalendar
    ) -> ContentCalendarEntry:
        """Approve a specific calendar entry."""
        for entry in calendar.entries:
            if str(id(entry)) == entry_id:
                entry.status = "approved"
                entry.approval_status = "approved"
                entry.approved_by = approved_by
                entry.approved_at = datetime.now().isoformat()
                return entry
        raise ValueError(f"Entry {entry_id} not found")
    
    async def reject_entry(
        self,
        entry_id: str,
        reason: str,
        calendar: ContentCalendar
    ) -> ContentCalendarEntry:
        """Reject a specific calendar entry."""
        for entry in calendar.entries:
            if str(id(entry)) == entry_id:
                entry.status = "rejected"
                entry.approval_status = "rejected"
                entry.approved_at = datetime.now().isoformat()
                return entry
        raise ValueError(f"Entry {entry_id} not found")

