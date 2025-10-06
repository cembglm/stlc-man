"""
mcp_server.py
------------
Model Context Protocol (MCP) Server for Test Execution
Handles test code execution via AI providers (LM Studio and Gemini)
Protocol: JSON-RPC 2.0
"""

import asyncio
import json
import logging
import uuid
from datetime import datetime
from typing import Dict, Any, Optional
import aiohttp
import google.generativeai as genai
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
import uvicorn
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Logger configuration
logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO)

# MCP Server configuration
MCP_SERVER_PORT = int(os.getenv("MCP_SERVER_PORT", "8001"))
LM_STUDIO_BASE_URL = os.getenv("LM_STUDIO_BASE_URL", "http://localhost:1234")
DEFAULT_LM_STUDIO_MODEL = os.getenv("DEFAULT_LM_STUDIO_MODEL", "llama-3.2-3b-instruct")

app = FastAPI(title="MCP Test Execution Server", version="1.0.0")

class JsonRpcRequest(BaseModel):
    jsonrpc: str = "2.0"
    method: str
    params: Optional[Dict[str, Any]] = None
    id: Optional[str] = None

class JsonRpcResponse(BaseModel):
    jsonrpc: str = "2.0"
    result: Optional[Dict[str, Any]] = None
    error: Optional[Dict[str, Any]] = None
    id: Optional[str] = None

class TestExecuteParams(BaseModel):
    model_config = {"protected_namespaces": ()}
    
    test_code: str
    provider: str  # "lm_studio" or "gemini"
    api_key: Optional[str] = None  # Required for Gemini
    model_name: Optional[str] = None  # Optional model override

class MCPServer:
    def __init__(self):
        self.session_id = str(uuid.uuid4())
        self.execution_prompt = self._get_execution_prompt()
    
    def _get_execution_prompt(self) -> str:
        """Get the standard MCP execution prompt"""
        return """You are operating inside the STLC Manager project as a Model Context Protocol (MCP) execution agent.
Your task is to execute the following test code and return only the raw execution results
exactly as a terminal would show. Do not add explanations or formatting.

Test Code to Execute:
"""

    async def execute_test(self, params: TestExecuteParams) -> Dict[str, Any]:
        """
        Main test execution method that routes to appropriate AI provider
        """
        try:
            logger.info(f"Executing test with provider: {params.provider}")
            
            if params.provider.lower() == "lm_studio":
                return await self._execute_via_lm_studio(params)
            elif params.provider.lower() == "gemini":
                return await self._execute_via_gemini(params)
            else:
                raise ValueError(f"Unsupported provider: {params.provider}")
                
        except Exception as e:
            logger.error(f"Test execution failed: {str(e)}")
            return {
                "success": False,
                "error": str(e),
                "terminal_output": f"Error: Test execution failed - {str(e)}",
                "timestamp": datetime.now().isoformat(),
                "provider": params.provider
            }

    async def _execute_via_lm_studio(self, params: TestExecuteParams) -> Dict[str, Any]:
        """Execute test code via LM Studio local API"""
        try:
            model_name = params.model_name or DEFAULT_LM_STUDIO_MODEL
            
            # Construct the full prompt
            full_prompt = self.execution_prompt + params.test_code
            
            # Prepare LM Studio API request
            payload = {
                "model": model_name,
                "messages": [
                    {
                        "role": "system",
                        "content": "You are a test execution terminal. Execute the provided test code and return only the raw terminal output without explanations."
                    },
                    {
                        "role": "user", 
                        "content": full_prompt
                    }
                ],
                "temperature": 0.1,
                "max_tokens": 2000,
                "stream": False
            }
            
            async with aiohttp.ClientSession() as session:
                async with session.post(
                    f"{LM_STUDIO_BASE_URL}/v1/chat/completions",
                    json=payload,
                    timeout=aiohttp.ClientTimeout(total=60)
                ) as response:
                    if response.status != 200:
                        raise HTTPException(
                            status_code=response.status,
                            detail=f"LM Studio API error: {await response.text()}"
                        )
                    
                    result = await response.json()
                    
                    if "choices" not in result or not result["choices"]:
                        raise ValueError("Invalid response from LM Studio API")
                    
                    terminal_output = result["choices"][0]["message"]["content"]
                    
                    return {
                        "success": True,
                        "terminal_output": terminal_output,
                        "provider": "lm_studio",
                        "model_used": model_name,
                        "timestamp": datetime.now().isoformat(),
                        "token_usage": result.get("usage", {})
                    }
                    
        except Exception as e:
            logger.error(f"LM Studio execution error: {str(e)}")
            raise

    async def _execute_via_gemini(self, params: TestExecuteParams) -> Dict[str, Any]:
        """Execute test code via Gemini API"""
        try:
            if not params.api_key:
                raise ValueError("API key is required for Gemini provider")
            
            # Configure Gemini
            genai.configure(api_key=params.api_key)
            
            # Use provided model or default
            model_name = params.model_name or "gemini-1.5-flash"
            model = genai.GenerativeModel(model_name)
            
            # Construct the full prompt
            full_prompt = self.execution_prompt + params.test_code
            
            # Generate response
            response = await asyncio.to_thread(
                model.generate_content,
                full_prompt,
                generation_config=genai.types.GenerationConfig(
                    temperature=0.1,
                    max_output_tokens=2000
                )
            )
            
            if not response.text:
                raise ValueError("Empty response from Gemini API")
            
            return {
                "success": True,
                "terminal_output": response.text,
                "provider": "gemini",
                "model_used": model_name,
                "timestamp": datetime.now().isoformat(),
                "finish_reason": getattr(response.candidates[0], 'finish_reason', 'STOP') if response.candidates else None
            }
            
        except Exception as e:
            logger.error(f"Gemini execution error: {str(e)}")
            raise

# MCP JSON-RPC 2.0 Handler
@app.post("/jsonrpc")
async def handle_jsonrpc(request: JsonRpcRequest):
    """Handle JSON-RPC 2.0 requests for MCP protocol"""
    try:
        logger.info(f"Received JSON-RPC request: method={request.method}, id={request.id}")
        
        if request.method == "executeTest":
            # Validate parameters
            if not request.params:
                raise ValueError("Parameters are required for executeTest method")
            
            # Parse parameters
            params = TestExecuteParams(**request.params)
            
            # Create MCP server instance and execute
            mcp_server = MCPServer()
            result = await mcp_server.execute_test(params)
            
            return JsonRpcResponse(
                result=result,
                id=request.id
            )
        
        elif request.method == "ping":
            return JsonRpcResponse(
                result={"status": "ok", "timestamp": datetime.now().isoformat()},
                id=request.id
            )
        
        else:
            raise ValueError(f"Unknown method: {request.method}")
    
    except Exception as e:
        logger.error(f"JSON-RPC error: {str(e)}")
        return JsonRpcResponse(
            error={
                "code": -32603,
                "message": "Internal error",
                "data": str(e)
            },
            id=request.id
        )

# Health check endpoint
@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "service": "MCP Test Execution Server",
        "version": "1.0.0",
        "timestamp": datetime.now().isoformat()
    }

# Provider status check
@app.get("/providers/status")
async def check_providers():
    """Check the status of available AI providers"""
    providers = {}
    
    # Check LM Studio
    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(
                f"{LM_STUDIO_BASE_URL}/v1/models",
                timeout=aiohttp.ClientTimeout(total=5)
            ) as response:
                if response.status == 200:
                    models_data = await response.json()
                    providers["lm_studio"] = {
                        "status": "available",
                        "base_url": LM_STUDIO_BASE_URL,
                        "models": [model.get("id") for model in models_data.get("data", [])]
                    }
                else:
                    providers["lm_studio"] = {"status": "error", "message": "API not accessible"}
    except Exception as e:
        providers["lm_studio"] = {"status": "error", "message": str(e)}
    
    # Check Gemini (basic check without API key)
    providers["gemini"] = {
        "status": "available",
        "note": "Requires API key for execution",
        "models": ["gemini-1.5-flash", "gemini-1.5-pro", "gemini-pro"]
    }
    
    return {
        "timestamp": datetime.now().isoformat(),
        "providers": providers
    }

if __name__ == "__main__":
    logger.info(f"Starting MCP Test Execution Server on port {MCP_SERVER_PORT}")
    uvicorn.run(
        "mcp_server:app",
        host="0.0.0.0",
        port=MCP_SERVER_PORT,
        reload=True,
        log_level="info"
    )