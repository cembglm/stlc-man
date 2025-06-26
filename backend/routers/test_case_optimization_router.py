from fastapi import APIRouter, HTTPException, Request
from fastapi.responses import JSONResponse
from services.test_case_optimization_service import TestCaseOptimizationService
from core.prompt_manager import save_session_data
from typing import List, Dict, Any
import logging
import uuid

logger = logging.getLogger(__name__)

router = APIRouter(
    prefix="/api/test-case-optimization",
    tags=["test-case-optimization"]
)

@router.get("/process-titles")
async def get_process_titles():
    """
    Mevcut process_title değerlerini getir.
    """
    try:
        service = TestCaseOptimizationService()
        process_titles = service.get_available_process_titles()
        
        return JSONResponse(
            status_code=200,
            content={
                "success": True,
                "message": "Process titles retrieved successfully",
                "data": process_titles
            }
        )
    except Exception as e:
        logger.error(f"Error in get_process_titles: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/test-cases/{process_title}")
async def get_test_cases_by_process_title(process_title: str):
    """
    Belirli bir process_title için test case'leri getir.
    """
    try:
        service = TestCaseOptimizationService()
        test_cases = service.get_test_cases_by_process_title(process_title)
        
        return JSONResponse(
            status_code=200,
            content={
                "success": True,
                "message": f"Test cases for {process_title} retrieved successfully",
                "data": test_cases
            }
        )
    except Exception as e:
        logger.error(f"Error in get_test_cases_by_process_title: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/smart-selection")
async def run_smart_selection(request: Request):
    """
    Seçilen test case'ler üzerinde smart selection işlemini çalıştır.
    """
    try:
        data = await request.json()
        selected_test_cases = data.get("selected_test_cases", [])
        process_title = data.get("process_title", "")
        custom_prompt = data.get("custom_prompt", "")  # Get custom prompt from request
        session_id = data.get("session_id") or str(uuid.uuid4())  # Generate session_id if not provided
        
        if not selected_test_cases:
            raise HTTPException(status_code=400, detail="No test cases selected")
        
        if not process_title:
            raise HTTPException(status_code=400, detail="Process title is required")
        
        service = TestCaseOptimizationService()
        
        # Smart selection işlemini çalıştır
        result = await service.run_smart_selection(selected_test_cases, custom_prompt)
        
        if not result["success"]:
            raise HTTPException(status_code=400, detail=result["message"])
        
        # Sonuçları test_case_optimizations koleksiyonuna kaydet
        save_success = service.save_optimization_results(process_title, result["data"])
        
        if save_success:
            result["message"] += " and saved successfully"
        else:
            result["message"] += " but failed to save results"
        
        # Session history'ye kaydet
        try:
            session_data = {
                "session_id": session_id,
                "output": result["data"],
                "edited_prompt": bool(custom_prompt),  # True if custom prompt was used
                "used_prompt": custom_prompt or "Default optimization prompt",
                "used_model": "llama-3.2-1b-instruct",  # Default model used in service
                "process_title": process_title
            }
            
            save_session_result = save_session_data(session_data, "test_case_optimization")
            if save_session_result:
                logger.info(f"Session data saved successfully for session_id: {session_id}")
            else:
                logger.warning(f"Failed to save session data for session_id: {session_id}")
                
        except Exception as session_error:
            logger.error(f"Error saving session data: {session_error}")
            # Don't fail the main request if session saving fails
        
        # Add session_id to response
        result["session_id"] = session_id
        
        return JSONResponse(
            status_code=200,
            content=result
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error in run_smart_selection: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/results/{process_title}")
async def get_optimization_results(process_title: str):
    """
    Belirli bir process_title için kaydedilmiş optimization sonuçlarını getir.
    """
    try:
        service = TestCaseOptimizationService()
        results = service.get_optimization_results(process_title)
        
        if results is None:
            return JSONResponse(
                status_code=404,
                content={
                    "success": False,
                    "message": "No optimization results found for this process title",
                    "data": None
                }
            )
        
        return JSONResponse(
            status_code=200,
            content={
                "success": True,
                "message": "Optimization results retrieved successfully",
                "data": results
            }
        )
        
    except Exception as e:
        logger.error(f"Error in get_optimization_results: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.delete("/results/{process_title}")
async def delete_optimization_results(process_title: str):
    """
    Belirli bir process_title için optimization sonuçlarını sil.
    """
    try:
        service = TestCaseOptimizationService()
        
        # Sonuçları sil
        optimization_collection = service.db["test_case_optimizations"]
        result = optimization_collection.delete_one({"process_title": process_title})
        
        if result.deleted_count == 0:
            return JSONResponse(
                status_code=404,
                content={
                    "success": False,
                    "message": "No optimization results found to delete",
                    "data": None
                }
            )
        
        return JSONResponse(
            status_code=200,
            content={
                "success": True,
                "message": "Optimization results deleted successfully",
                "data": None
            }
        )
        
    except Exception as e:
        logger.error(f"Error in delete_optimization_results: {e}")
        raise HTTPException(status_code=500, detail=str(e))
