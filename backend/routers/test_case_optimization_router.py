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

@router.get("/models")
async def get_available_models():
    """
    Kullanılabilir LLM modellerini getir.
    """
    try:
        # Model mapping'den mevcut modelleri al
        from utils.model_client import LLMClient
        
        # Model mapping'i statik olarak döndür
        available_models = [
            {"key": "codegeex4:9b", "name": "CodeGeeX4 (9B)", "description": "Code generation optimized model"},
            {"key": "codellama:7b", "name": "Code Llama (7B)", "description": "Meta's code-focused model"},
            {"key": "deepseek-coder:6.7b", "name": "DeepSeek Coder (6.7B)", "description": "DeepSeek's coding model"},
            {"key": "gemma2:2b", "name": "Gemma 2 (2B)", "description": "Google's lightweight model"},
            {"key": "gemma3:4b", "name": "Gemma 3 (4B)", "description": "Google's enhanced model"},
            {"key": "llama3.2:3b", "name": "Llama 3.2 (3B)", "description": "Meta's latest efficient model"},
            {"key": "qwen2.5:7b", "name": "Qwen 2.5 (7B)", "description": "Alibaba's advanced model"},
            {"key": "qwen2.5:7b-1m", "name": "Qwen 2.5 (7B-1M)", "description": "Large context version"},
            {"key": "qwen2.5-coder:3b", "name": "Qwen 2.5 Coder (3B)", "description": "Coding-focused Qwen model"},
            {"key": "stable-code:3b", "name": "Stable Code (3B)", "description": "Stability AI's code model"},
            {"key": "starcoder2:7b", "name": "StarCoder 2 (7B)", "description": "BigCode's enhanced model"}
        ]
        
        return JSONResponse(
            status_code=200,
            content={
                "success": True,
                "message": "Available models retrieved successfully",
                "data": available_models
            }
        )
    except Exception as e:
        logger.error(f"Error in get_available_models: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/process-titles-with-counts")
async def get_process_titles_with_counts():
    """
    Process title'ları ve test case sayılarını getir.
    """
    try:
        service = TestCaseOptimizationService()
        process_data = service.get_process_titles_with_counts()
        
        return JSONResponse(
            status_code=200,
            content={
                "success": True,
                "message": "Process titles with counts retrieved successfully",
                "data": process_data
            }
        )
    except Exception as e:
        logger.error(f"Error in get_process_titles_with_counts: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/test-cases-multi-process")
async def get_test_cases_by_multiple_processes(request: Request):
    """
    Birden fazla process_title için test case'leri getir.
    """
    try:
        body = await request.json()
        process_titles = body.get("process_titles", [])
        
        if not process_titles:
            raise HTTPException(status_code=400, detail="Process titles list is required")
        
        service = TestCaseOptimizationService()
        test_cases = service.get_test_cases_by_process_titles(process_titles)
        
        return JSONResponse(
            status_code=200,
            content={
                "success": True,
                "message": f"Test cases for {len(process_titles)} processes retrieved successfully",
                "data": test_cases
            }
        )
    except Exception as e:
        logger.error(f"Error in get_test_cases_by_multiple_processes: {e}")
        raise HTTPException(status_code=500, detail=str(e))

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
        process_titles = data.get("process_titles", [])  # Accept multiple process titles
        process_title = data.get("process_title", "")  # Backward compatibility
        process_name = data.get("process_name", "")  # Get process name for saving optimization
        custom_prompt = data.get("custom_prompt", "")  # Get custom prompt from request
        selected_model = data.get("selected_model", "")  # Get selected model - don't use default
        session_id = data.get("session_id") or str(uuid.uuid4())  # Generate session_id if not provided
        
        if not selected_test_cases:
            raise HTTPException(status_code=400, detail="No test cases selected")
        
        # Handle both single and multiple process titles
        if process_titles:
            target_processes = process_titles
        elif process_title:
            target_processes = [process_title]
        else:
            raise HTTPException(status_code=400, detail="Process title(s) required")
        
        # Model seçimi zorunlu
        if not selected_model:
            raise HTTPException(status_code=400, detail="Model selection required")
            
        # Process name zorunlu
        if not process_name or process_name.strip() == "":
            raise HTTPException(status_code=400, detail="Process name is required")
        
        service = TestCaseOptimizationService()
        
        # Smart selection işlemini çalıştır (model parametresi ile)
        result = await service.run_smart_selection(selected_test_cases, custom_prompt, selected_model)
        
        if not result["success"]:
            raise HTTPException(status_code=400, detail=result["message"])
        
        # Sonuçları her process için test_case_optimizations koleksiyonuna kaydet
        save_results = []
        for proc_title in target_processes:
            save_success = service.save_optimization_results(proc_title, result["data"], selected_model)
            save_results.append(save_success)
        
        if all(save_results):
            result["message"] += f" and saved successfully for {len(target_processes)} process(es)"
        else:
            result["message"] += f" but failed to save some results"
        
        # Session history'ye kaydet
        try:
            session_data = {
                "session_id": session_id,
                "output": result["data"],
                "edited_prompt": bool(custom_prompt),  # True if custom prompt was used
                "used_prompt": custom_prompt or "Default optimization prompt",
                "used_model": selected_model,  # Use the actual selected model
                "process_name": process_name,  # Save process name for test_case_optimization
                "process_titles": target_processes,  # Save multiple process titles
                "process_count": len(target_processes)
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

@router.get("/process-names")
async def get_available_process_names():
    """
    Kaydedilmiş process name'leri getir.
    """
    try:
        from core.database import get_db
        db = get_db()
        session_collection = db["session_history"]
        
        # test_case_optimization süreçlerinden process_name'leri getir
        pipeline = [
            {"$match": {"processes.test_case_optimization": {"$exists": True}}},
            {"$project": {"process_name": "$processes.test_case_optimization.process_name"}},
            {"$match": {"process_name": {"$exists": True, "$ne": ""}}},
            {"$group": {"_id": "$process_name", "count": {"$sum": 1}}},
            {"$sort": {"_id": 1}}
        ]
        
        results = list(session_collection.aggregate(pipeline))
        process_names = [{"process_name": result["_id"], "count": result["count"]} for result in results]
        
        return JSONResponse(
            status_code=200,
            content={
                "success": True,
                "message": "Process names retrieved successfully",
                "data": process_names
            }
        )
    except Exception as e:
        logger.error(f"Error in get_available_process_names: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/results/by-process-name/{process_name}")
async def get_optimization_results_by_process_name(process_name: str):
    """
    Process name'e göre optimization sonuçlarını getir.
    """
    try:
        from core.database import get_db
        db = get_db()
        session_collection = db["session_history"]
        
        # Process name'e göre optimization sonuçlarını getir
        results = list(session_collection.find(
            {"processes.test_case_optimization.process_name": process_name},
            {"processes.test_case_optimization": 1, "session_id": 1, "timestamp": 1}
        ).sort("timestamp", -1))
        
        if not results:
            return JSONResponse(
                status_code=404,
                content={
                    "success": False,
                    "message": "No optimization results found for this process name",
                    "data": None
                }
            )
        
        # Format the results
        formatted_results = []
        for result in results:
            session_id = result.get("session_id", "")
            timestamp = result.get("timestamp", "")
            optimization_data = result.get("processes", {}).get("test_case_optimization", {})
            
            formatted_results.append({
                "session_id": session_id,
                "timestamp": timestamp,
                "process_name": optimization_data.get("process_name", ""),
                "used_model": optimization_data.get("used_model", ""),
                "process_titles": optimization_data.get("process_titles", []),
                "process_count": optimization_data.get("process_count", 0),
                "output": optimization_data.get("output", {})
            })
        
        return JSONResponse(
            status_code=200,
            content={
                "success": True,
                "message": f"Optimization results for '{process_name}' retrieved successfully",
                "data": formatted_results
            }
        )
        
    except Exception as e:
        logger.error(f"Error in get_optimization_results_by_process_name: {e}")
        raise HTTPException(status_code=500, detail=str(e))
