"""
docker_execution_router.py
--------------------------
API Router for Docker-based test execution
Provides endpoints for containerized test execution including hardware simulations
"""

import logging
from fastapi import APIRouter, HTTPException, Request
from pydantic import BaseModel
from typing import Optional, Dict, Any, List
from services.docker_executor import docker_executor
from core.database import get_database
from datetime import datetime
import json

logger = logging.getLogger(__name__)

router = APIRouter(
    prefix="/api/docker-execution",
    tags=["docker-execution"]
)

# Request Models
class DockerTestExecutionRequest(BaseModel):
    test_code: str
    language: str = "python"
    base_image: Optional[str] = None
    additional_packages: Optional[List[str]] = None
    environment_vars: Optional[Dict[str, str]] = None
    timeout: int = 300

class RobotSimulationRequest(BaseModel):
    test_code: str
    robot_type: str = "generic"  # generic, industrial, collaborative
    simulation_config: Optional[Dict[str, Any]] = None

class ProcessDockerExecutionRequest(BaseModel):
    process_name: str  # Test Code Generation process name
    language: str = "python"
    additional_packages: Optional[List[str]] = None
    environment_vars: Optional[Dict[str, str]] = None
    timeout: int = 300

class ImagePullRequest(BaseModel):
    image_name: str

# Response Models
class DockerExecutionResponse(BaseModel):
    success: bool
    output: str
    error: Optional[str] = None
    exit_code: Optional[int] = None
    execution_time: Optional[str] = None
    container_info: Optional[Dict[str, Any]] = None

class DockerStatusResponse(BaseModel):
    docker_available: bool
    images: List[str]
    container_status: Dict[str, Any]

@router.get("/status", response_model=DockerStatusResponse)
async def get_docker_status():
    """
    Get Docker environment status
    """
    try:
        available = docker_executor.is_available()
        images = docker_executor.list_available_images() if available else []
        container_status = docker_executor.get_container_status()
        
        return DockerStatusResponse(
            docker_available=available,
            images=images,
            container_status=container_status
        )
    except Exception as e:
        logger.error(f"Error getting Docker status: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/execute", response_model=DockerExecutionResponse)
async def execute_test_in_docker(request: DockerTestExecutionRequest):
    """
    Execute test code in a Docker container
    
    This endpoint provides isolated test execution environment using Docker.
    Perfect for testing code that requires specific dependencies or system configurations.
    """
    try:
        if not docker_executor.is_available():
            raise HTTPException(
                status_code=503,
                detail="Docker is not available. Please ensure Docker is installed and running."
            )
        
        logger.info(f"🐳 Executing test in Docker container (language: {request.language})")
        
        result = await docker_executor.execute_test_in_container(
            test_code=request.test_code,
            language=request.language,
            base_image=request.base_image,
            additional_packages=request.additional_packages,
            environment_vars=request.environment_vars,
            timeout=request.timeout
        )
        
        # Save execution to database
        await save_docker_execution_result(
            execution_type="docker_test",
            request_data=request.dict(),
            result=result
        )
        
        return DockerExecutionResponse(**result)
        
    except Exception as e:
        logger.error(f"Docker execution error: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/execute-robot-simulation", response_model=DockerExecutionResponse)
async def execute_robot_simulation(request: RobotSimulationRequest):
    """
    Execute robot arm simulation tests
    
    Simulates robot arm movements and control logic in a containerized environment.
    Supports various robot types: generic (3-DOF), industrial (6-DOF), collaborative.
    
    Example test code:
    ```python
    # Test robot movement
    success, pos = robot.move_to_position([0.5, 0.3, 0.2])
    print(f"Position reached: {pos}")
    
    # Move to another position
    success, pos = robot.move_to_position([1.0, 0.5, 0.1])
    print(f"Final position: {pos}")
    ```
    """
    try:
        if not docker_executor.is_available():
            raise HTTPException(
                status_code=503,
                detail="Docker is not available. Please ensure Docker is installed and running."
            )
        
        logger.info(f"🤖 Executing robot arm simulation (type: {request.robot_type})")
        
        result = await docker_executor.execute_robot_arm_simulation(
            test_code=request.test_code,
            robot_type=request.robot_type,
            simulation_config=request.simulation_config
        )
        
        # Save execution to database
        await save_docker_execution_result(
            execution_type="robot_simulation",
            request_data=request.dict(),
            result=result
        )
        
        return DockerExecutionResponse(**result)
        
    except Exception as e:
        logger.error(f"Robot simulation error: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/execute-from-process", response_model=DockerExecutionResponse)
async def execute_from_process(request: ProcessDockerExecutionRequest):
    """
    Execute test code from a Test Code Generation process in Docker
    
    Fetches test code from MongoDB and executes it in an isolated Docker container.
    """
    try:
        if not docker_executor.is_available():
            raise HTTPException(
                status_code=503,
                detail="Docker is not available. Please ensure Docker is installed and running."
            )
        
        # Fetch test code from database
        test_code = await fetch_test_code_by_process_name(request.process_name)
        
        logger.info(f"🐳 Executing process '{request.process_name}' in Docker container")
        
        result = await docker_executor.execute_test_in_container(
            test_code=test_code,
            language=request.language,
            additional_packages=request.additional_packages,
            environment_vars=request.environment_vars,
            timeout=request.timeout
        )
        
        # Save execution to database
        await save_docker_execution_result(
            execution_type="docker_process",
            request_data={
                "process_name": request.process_name,
                **request.dict()
            },
            result=result
        )
        
        return DockerExecutionResponse(**result)
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Process Docker execution error: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/pull-image")
async def pull_docker_image(request: ImagePullRequest):
    """
    Pull a Docker image for test execution
    """
    try:
        if not docker_executor.is_available():
            raise HTTPException(
                status_code=503,
                detail="Docker is not available"
            )
        
        success = docker_executor.pull_image(request.image_name)
        
        if success:
            return {
                "success": True,
                "message": f"Successfully pulled image: {request.image_name}"
            }
        else:
            raise HTTPException(
                status_code=500,
                detail=f"Failed to pull image: {request.image_name}"
            )
            
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Image pull error: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/available-robots")
async def get_available_robot_types():
    """
    Get list of available robot simulation types
    """
    return {
        "robot_types": [
            {
                "id": "generic",
                "name": "Generic 3-DOF Robot",
                "description": "Simple 3-axis robotic arm for basic operations",
                "dof": 3
            },
            {
                "id": "industrial",
                "name": "Industrial 6-DOF Robot",
                "description": "Industrial-grade 6-axis robotic arm for complex tasks",
                "dof": 6
            },
            {
                "id": "collaborative",
                "name": "Collaborative Robot",
                "description": "Safe collaborative robot for human-robot interaction",
                "dof": 4
            }
        ]
    }

@router.get("/supported-languages")
async def get_supported_languages():
    """
    Get list of supported programming languages for Docker execution
    """
    return {
        "languages": [
            {
                "id": "python",
                "name": "Python",
                "default_image": "python:3.9-slim",
                "extensions": [".py"]
            },
            {
                "id": "javascript",
                "name": "JavaScript",
                "default_image": "node:18-alpine",
                "extensions": [".js"]
            },
            {
                "id": "java",
                "name": "Java",
                "default_image": "openjdk:11-jre-slim",
                "extensions": [".java"]
            },
            {
                "id": "csharp",
                "name": "C#",
                "default_image": "mcr.microsoft.com/dotnet/sdk:6.0",
                "extensions": [".cs"]
            },
            {
                "id": "go",
                "name": "Go",
                "default_image": "golang:1.19-alpine",
                "extensions": [".go"]
            },
            {
                "id": "rust",
                "name": "Rust",
                "default_image": "rust:1.70-slim",
                "extensions": [".rs"]
            }
        ]
    }

# Helper Functions
async def fetch_test_code_by_process_name(process_name: str) -> str:
    """
    Fetch test code from MongoDB by code_generation_process_name
    """
    try:
        db = await get_database()
        collection = db["session_history"]
        
        # Find the most recent test code generation with matching process name
        session = await collection.find_one(
            {
                "processes.test_code_generation.process_name": process_name
            },
            sort=[("processes.test_code_generation.timestamp", -1)]
        )
        
        if not session:
            raise HTTPException(
                status_code=404,
                detail=f"No test code generation found for process: {process_name}"
            )
        
        # Extract test code from output
        test_code_gen = session.get("processes", {}).get("test_code_generation", {})
        output = test_code_gen.get("output", {})
        
        # Try multiple possible locations for test code
        test_code = None
        
        if isinstance(output, dict):
            test_code = output.get("test_code") or output.get("generated_code")
            
            if not test_code and "data" in output:
                data = output["data"]
                if isinstance(data, dict):
                    test_code = data.get("test_code") or data.get("generated_code")
        
        if not test_code:
            raise HTTPException(
                status_code=404,
                detail=f"No executable test code found for process: {process_name}"
            )
        
        logger.info(f"Successfully fetched test code for process: {process_name}")
        return test_code.strip()
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error fetching test code: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

async def save_docker_execution_result(
    execution_type: str,
    request_data: Dict[str, Any],
    result: Dict[str, Any]
) -> str:
    """
    Save Docker execution result to database
    """
    try:
        db = await get_database()
        collection = db["session_history"]
        
        session_id = f"docker-exec-{datetime.now().strftime('%Y%m%d-%H%M%S')}"
        
        record = {
            "session_id": session_id,
            "timestamp": datetime.now().isoformat(),
            "processes": {
                "docker_execution": {
                    "execution_type": execution_type,
                    "status": "completed" if result.get("success") else "failed",
                    "timestamp": datetime.now().isoformat(),
                    "input": request_data,
                    "output": result
                }
            }
        }
        
        await collection.insert_one(record)
        logger.info(f"✅ Saved Docker execution result: {session_id}")
        
        return session_id
        
    except Exception as e:
        logger.error(f"Failed to save Docker execution result: {str(e)}")
        return None
