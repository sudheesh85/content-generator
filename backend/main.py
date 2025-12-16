import os
import uuid
import asyncio
from fastapi import FastAPI, UploadFile, File, Form, HTTPException
from fastapi.middleware.cors import CORSMiddleware
try:
    from backend.models.campaign import CampaignRequest
    from backend.api.content_management import router as content_router, campaign_storage
    from backend.api.campaign_status import router as campaign_router
    from backend.api.health import router as health_router
    from backend.api.test import router as test_router
    from backend.api.approval import router as approval_router
except ModuleNotFoundError:
    from models.campaign import CampaignRequest
    from api.content_management import router as content_router, campaign_storage
    from api.campaign_status import router as campaign_router
    from api.health import router as health_router
    from api.test import router as test_router
    from api.approval import router as approval_router
from typing import List, Optional
import uvicorn
from dotenv import load_dotenv
try:
    from backend.agents.maf_workflow import CampaignWorkflow
except ModuleNotFoundError:
    from agents.maf_workflow import CampaignWorkflow

load_dotenv()

# Setup logging
try:
    from backend.utils.logger import setup_logging
except ModuleNotFoundError:
    try:
        from utils.logger import setup_logging
    except ModuleNotFoundError:
        # Fallback if logger not available
        def setup_logging(*args, **kwargs):
            pass

setup_logging(log_level=os.getenv("LOG_LEVEL", "INFO"))

app = FastAPI(
    title="AI Social Media Content Generator",
    description="Production-ready social media content generation and publishing platform",
    version="1.0.0"
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, specify actual origins
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Add timeout middleware (optional)
try:
    from backend.middleware.timeout import TimeoutMiddleware
    app.add_middleware(TimeoutMiddleware, timeout=900)  # 15 minutes
except (ModuleNotFoundError, ImportError):
    pass  # Middleware optional

app.include_router(content_router)
app.include_router(campaign_router)
app.include_router(health_router)
app.include_router(test_router)
app.include_router(approval_router)

# Serve static media files
from fastapi.staticfiles import StaticFiles
import os
media_dir = os.path.join(os.path.dirname(__file__), "media")
if os.path.exists(media_dir):
    app.mount("/media", StaticFiles(directory=media_dir), name="media")

@app.get("/")
def read_root():
    return {
        "message": "AI Social Media Content Generator API is running",
        "version": "1.0.0",
            "endpoints": {
                "campaign": "/api/campaign/start",
                "content": "/api/content",
                "status": "/api/campaign/{campaign_id}/status",
                "health": "/api/health"
            }
    }


@app.post("/api/campaign/start")
async def start_campaign(request: CampaignRequest, background: bool = False):
    """
    Start a new campaign workflow.
    
    Args:
        request: Campaign parameters
        background: If True, runs in background and returns campaign_id immediately
    """
    import logging
    import asyncio
    import traceback
    logger = logging.getLogger(__name__)
    
    workflow = None
    campaign_id = str(uuid.uuid4())[:8]
    
    # If background mode, start workflow async and return immediately
    if background:
        logger.info(f"Starting campaign {campaign_id} in background mode with goal: {request.goal}")
        
        # Clear old media files from previous campaigns
        try:
            import shutil
            media_images_dir = os.path.join(os.path.dirname(__file__), "media", "images")
            if os.path.exists(media_images_dir):
                logger.info(f"Clearing old media files from {media_images_dir}")
                for filename in os.listdir(media_images_dir):
                    file_path = os.path.join(media_images_dir, filename)
                    if os.path.isfile(file_path):
                        os.unlink(file_path)
                logger.info("Old media files cleared")
        except Exception as e:
            logger.warning(f"Failed to clear old media files: {str(e)}")
        
        # Store initial status
        campaign_storage[campaign_id] = {
            "status": "running",
            "progress": "Initializing workflow...",
            "request": request,
            "started_at": asyncio.get_event_loop().time()
        }
        
        # Run workflow in background
        async def run_background_workflow():
            try:
                logger.info(f"Initializing workflow for campaign {campaign_id}")
                workflow = CampaignWorkflow()
                campaign_storage[campaign_id]["progress"] = "Workflow initialized, generating strategy..."
                
                logger.info(f"Starting workflow execution for campaign {campaign_id}")
                final_result = await asyncio.wait_for(
                    workflow.run_campaign(request),
                    timeout=900.0
                )
                
                logger.info(f"Workflow completed for campaign {campaign_id}, storing results...")
                # Update storage with results
                campaign_storage[campaign_id].update({
                    "status": "completed",
                    "progress": "Campaign generation complete",
                    "strategy": final_result.strategy,
                    "research": final_result.research,
                    "brand_voice": final_result.brand_voice,
                    "content": final_result.content,
                    "calendar": final_result.calendar,
                    "publish_result": final_result.publish_result,
                    "completed_at": asyncio.get_event_loop().time()
                })
                logger.info(f"Background campaign {campaign_id} completed successfully")
            except asyncio.TimeoutError:
                logger.error(f"Background campaign {campaign_id} timed out after 15 minutes")
                campaign_storage[campaign_id].update({
                    "status": "failed",
                    "progress": "Workflow timed out after 15 minutes",
                    "error": "Campaign generation timed out",
                    "error_type": "TimeoutError"
                })
            except Exception as e:
                logger.error(f"Background campaign {campaign_id} failed: {str(e)}", exc_info=True)
                error_msg = str(e)
                # Simplify validation errors for frontend
                if "validation error" in error_msg.lower():
                    error_msg = "Data validation error. Please try again or check logs."
                
                campaign_storage[campaign_id].update({
                    "status": "failed",
                    "progress": f"Error: {error_msg}",
                    "error": error_msg,
                    "error_type": type(e).__name__
                })
        
        # Start background task
        asyncio.create_task(run_background_workflow())
        
        return {
            "status": "started",
            "campaign_id": campaign_id,
            "message": "Campaign workflow started in background. Use /api/campaign/{campaign_id}/status to check progress."
        }
    
    # Original synchronous mode
    try:
        logger.info(f"Starting campaign {campaign_id} with goal: {request.goal}")
        
        # Initialize workflow
        try:
            workflow = CampaignWorkflow()
            logger.info(f"Workflow initialized for campaign {campaign_id}")
        except Exception as e:
            logger.error(f"Failed to initialize workflow: {str(e)}", exc_info=True)
            raise HTTPException(
                status_code=500,
                detail={
                    "error": f"Failed to initialize workflow: {str(e)}",
                    "campaign_id": campaign_id,
                    "type": "WorkflowInitializationError"
                }
            )
        
        # Execute workflow with timeout
        try:
            logger.info(f"Executing workflow for campaign {campaign_id}")
            # Add overall timeout for the entire workflow (15 minutes)
            final_result = await asyncio.wait_for(
                workflow.run_campaign(request),
                timeout=900.0  # 15 minutes
            )
            logger.info(f"Campaign {campaign_id} completed successfully")
        except asyncio.TimeoutError:
            logger.error(f"Campaign {campaign_id} timed out after 15 minutes")
            raise HTTPException(
                status_code=504,
                detail={
                    "error": "Campaign generation timed out. The workflow took longer than 15 minutes.",
                    "campaign_id": campaign_id,
                    "type": "TimeoutError",
                    "suggestion": "Try with a simpler request or check backend logs"
                }
            )
        except Exception as e:
            error_trace = traceback.format_exc()
            logger.error(f"Workflow execution failed for campaign {campaign_id}: {str(e)}\n{error_trace}")
            raise HTTPException(
                status_code=500,
                detail={
                    "error": f"Workflow execution failed: {str(e)}",
                    "campaign_id": campaign_id,
                    "type": type(e).__name__,
                    "traceback": error_trace if os.getenv("DEBUG", "false").lower() == "true" else None
                }
            )
        
        # Store campaign data for later access (editing, approval, etc.)
        try:
            campaign_storage[campaign_id] = {
                "request": request,
                "strategy": final_result.strategy,
                "research": final_result.research,
                "brand_voice": final_result.brand_voice,
                "content": final_result.content,
                "calendar": final_result.calendar,
                "publish_result": final_result.publish_result
            }
            logger.info(f"Campaign {campaign_id} stored successfully")
        except Exception as e:
            logger.warning(f"Failed to store campaign {campaign_id}: {str(e)}")
            # Continue even if storage fails
        
        # Convert result to dict for JSON serialization
        try:
            strategy_dict = final_result.strategy.model_dump() if hasattr(final_result.strategy, 'model_dump') else final_result.strategy
            research_dict = final_result.research.model_dump() if hasattr(final_result.research, 'model_dump') else final_result.research
            brand_voice_dict = final_result.brand_voice.model_dump() if hasattr(final_result.brand_voice, 'model_dump') else final_result.brand_voice
            
            content_dict = {
                "captions": [c.model_dump() if hasattr(c, 'model_dump') else c for c in final_result.content.captions],
                "image_briefs": [i.model_dump() if hasattr(i, 'model_dump') else i for i in final_result.content.image_briefs],
                "video_scripts": [v.model_dump() if hasattr(v, 'model_dump') else v for v in final_result.content.video_scripts],
            }
            
            calendar_dict = final_result.calendar.model_dump() if hasattr(final_result.calendar, 'model_dump') else final_result.calendar
            
            result_dict = {
                "campaign_id": campaign_id,
                "strategy": strategy_dict,
                "research": research_dict,
                "brand_voice": brand_voice_dict,
                "content": content_dict,
                "calendar": calendar_dict,
                "publish_result": final_result.publish_result
            }
            
            logger.info(f"Campaign {campaign_id} serialized successfully")
            return {"status": "success", "data": result_dict}
            
        except Exception as e:
            error_trace = traceback.format_exc()
            logger.error(f"Serialization error for campaign {campaign_id}: {str(e)}\n{error_trace}")
            traceback.print_exc()
            raise HTTPException(
                status_code=500, 
                detail={
                    "error": f"Serialization error: {str(e)}",
                    "campaign_id": campaign_id,
                    "type": type(e).__name__
                }
            )
    
    except HTTPException:
        # Re-raise HTTP exceptions (they're already properly formatted)
        raise
    except Exception as e:
        # Catch any other unexpected errors
        error_trace = traceback.format_exc()
        logger.error(f"Unexpected error in campaign {campaign_id}: {str(e)}\n{error_trace}")
        traceback.print_exc()
        raise HTTPException(
            status_code=500,
            detail={
                "error": f"Unexpected error: {str(e)}",
                "campaign_id": campaign_id,
                "type": type(e).__name__,
                "traceback": error_trace if os.getenv("DEBUG", "false").lower() == "true" else None
            }
        )

if __name__ == "__main__":
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
