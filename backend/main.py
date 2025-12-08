import os
from fastapi import FastAPI, UploadFile, File, Form, HTTPException
try:
    from backend.models.campaign import CampaignRequest
except ModuleNotFoundError:
    from models.campaign import CampaignRequest
from typing import List, Optional
import uvicorn
from dotenv import load_dotenv
try:
    from backend.agents.maf_workflow import CampaignWorkflow
except ModuleNotFoundError:
    from agents.maf_workflow import CampaignWorkflow

load_dotenv()

app = FastAPI(title="AI Social Media Content Generator")

@app.get("/")
def read_root():
    return {"message": "AI Social Media Content Generator API is running"}

@app.post("/api/campaign/start")
async def start_campaign(request: CampaignRequest):
    workflow = CampaignWorkflow()
    try:
        final_result = await workflow.run_campaign(request)
        
        print("Final result type:", type(final_result))
        print("Strategy:", final_result.strategy)
        print("Research:", final_result.research)
        print("Brand voice:", final_result.brand_voice)
        print("Content:", final_result.content)
        print("Calendar:", final_result.calendar)
        
        # Convert result to dict for JSON serialization with detailed error handling
        try:
            strategy_dict = final_result.strategy.model_dump() if hasattr(final_result.strategy, 'model_dump') else final_result.strategy
            print("Strategy serialized successfully")
        except Exception as e:
            print(f"Error serializing strategy: {e}")
            raise
            
        try:
            research_dict = final_result.research.model_dump() if hasattr(final_result.research, 'model_dump') else final_result.research
            print("Research serialized successfully")
        except Exception as e:
            print(f"Error serializing research: {e}")
            raise
            
        try:
            brand_voice_dict = final_result.brand_voice.model_dump() if hasattr(final_result.brand_voice, 'model_dump') else final_result.brand_voice
            print("Brand voice serialized successfully")
        except Exception as e:
            print(f"Error serializing brand_voice: {e}")
            raise
            
        try:
            content_dict = {
                "captions": [c.model_dump() if hasattr(c, 'model_dump') else c for c in final_result.content.captions],
                "image_briefs": [i.model_dump() if hasattr(i, 'model_dump') else i for i in final_result.content.image_briefs],
                "video_scripts": [v.model_dump() if hasattr(v, 'model_dump') else v for v in final_result.content.video_scripts],
            }
            print("Content serialized successfully")
        except Exception as e:
            print(f"Error serializing content: {e}")
            print(f"Content type: {type(final_result.content)}")
            print(f"Content value: {final_result.content}")
            raise
            
        try:
            calendar_dict = final_result.calendar.model_dump() if hasattr(final_result.calendar, 'model_dump') else final_result.calendar
            print("Calendar serialized successfully")
        except Exception as e:
            print(f"Error serializing calendar: {e}")
            raise
        
        result_dict = {
            "strategy": strategy_dict,
            "research": research_dict,
            "brand_voice": brand_voice_dict,
            "content": content_dict,
            "calendar": calendar_dict,
            "publish_result": final_result.publish_result
        }
        
        print("Full result serialized successfully")
        return {"status": "success", "data": result_dict}
            
    except Exception as e:
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=str(e))

if __name__ == "__main__":
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
