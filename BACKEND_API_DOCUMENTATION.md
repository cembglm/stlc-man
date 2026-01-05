# STLC Manager - Backend API Dokümantasyonu

## 📚 İçindekiler
1. [Genel Bilgiler](#genel-bilgiler)
2. [Authentication & Validation](#authentication--validation)
3. [Model Yönetimi](#model-yönetimi)
4. [Prompt Yönetimi](#prompt-yönetimi)
5. [STLC Süreçleri](#stlc-süreçleri)
6. [Test Case Optimization](#test-case-optimization)
7. [Test Code Generation](#test-code-generation)
8. [Test Execution](#test-execution)
9. [Test Reporting](#test-reporting)
10. [Test Closure](#test-closure)
11. [Docker Execution](#docker-execution)

---

## Genel Bilgiler

### Base URL
```
http://localhost:8000
```

### CORS Ayarları
Backend, tüm originlere (`*`) izin verecek şekilde yapılandırılmıştır. Farklı platform ve uygulamalardan istek atabilirsiniz.

### Health Check Endpoints

#### 1. Root Health Check
```http
GET /
```

**Yanıt:**
```json
{
  "message": "STLC Manager Backend is running!"
}
```

#### 2. Prompts Status Check
```http
GET /api/health/prompts
```

**Yanıt:**
```json
{
  "all_modules_ready": true,
  "modules": {
    "code_review": {
      "available": true,
      "prompt_length": 1250
    },
    "requirement_analysis": {
      "available": true,
      "prompt_length": 980
    },
    "test_planning": {
      "available": true,
      "prompt_length": 1100
    },
    "environment_setup": {
      "available": true,
      "prompt_length": 1340
    },
    "test_scenario_generation": {
      "available": true,
      "prompt_length": 1500
    },
    "test_execution": {
      "available": true,
      "prompt_length": 890
    }
  },
  "message": "All prompts loaded successfully!"
}
```

---

## Authentication & Validation

### API Key Validation Endpoints

#### 1. Google API Key Test
```http
POST /api/test-google-api-key
Content-Type: application/json
```

**Request Body:**
```json
{
  "api_key": "AIzaSyXXXXXXXXXXXXXXXXXXXXXXXXXXXXXX"
}
```

**Yanıt (Başarılı):**
```json
{
  "success": true,
  "message": "Google API key is valid and working",
  "provider": "google"
}
```

**Yanıt (Hatalı):**
```json
{
  "success": false,
  "message": "Google API key validation failed: Invalid API key",
  "provider": "google"
}
```

#### 2. OpenAI API Key Test
```http
POST /api/test-openai-api-key
Content-Type: application/json
```

**Request Body:**
```json
{
  "api_key": "sk-XXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXX"
}
```

**Yanıt (Başarılı):**
```json
{
  "success": true,
  "message": "OpenAI API key is valid and working",
  "provider": "openai"
}
```

---

## Model Yönetimi

### Model Endpoints

#### 1. Tüm Modelleri Getir
```http
GET /api/models/?model_type=local&category=code&performance=fast
```

**Query Parameters:**
- `model_type` (optional): "local" veya "api"
- `category` (optional): "code", "general", "reasoning", vb.
- `performance` (optional): "fast", "medium", "slow"
- `optimization_ready` (optional): true/false
- `requires_api_key` (optional): true/false
- `legacy_format` (optional): true/false (eski format için)

**Yanıt:**
```json
{
  "success": true,
  "message": "Retrieved 21 models successfully",
  "data": [
    {
      "key": "llama3.2:3b",
      "name": "Llama 3.2 (3B)",
      "description": "Meta's latest efficient model",
      "type": "local",
      "category": "general",
      "performance": "fast",
      "optimization_ready": true,
      "requires_api_key": false,
      "provider": null,
      "recommended_for": ["test_generation", "code_review"]
    },
    {
      "key": "gemini-2.5-flash",
      "name": "Gemini 2.5 Flash",
      "description": "Google's latest fast model",
      "type": "api",
      "category": "general",
      "performance": "fast",
      "optimization_ready": false,
      "requires_api_key": true,
      "provider": "Google",
      "recommended_for": ["test_execution", "reporting"]
    }
  ],
  "metadata": {
    "total_count": 21,
    "filtered": true,
    "legacy_format": false
  }
}
```

#### 2. Model Kategorilerini Getir
```http
GET /api/models/categories
```

**Yanıt:**
```json
{
  "success": true,
  "message": "Model categories retrieved successfully",
  "data": {
    "categories": ["code", "general", "reasoning", "vision"],
    "counts": {
      "code": 5,
      "general": 10,
      "reasoning": 4,
      "vision": 2
    },
    "total_categories": 4
  }
}
```

#### 3. Model Tiplerini Getir
```http
GET /api/models/types
```

**Yanıt:**
```json
{
  "success": true,
  "message": "Model types retrieved successfully",
  "data": {
    "types": ["local", "api"],
    "counts": {
      "local": 17,
      "api": 4
    }
  }
}
```

---

## Prompt Yönetimi

Her STLC süreci için prompt GET ve POST endpoint'leri bulunur.

### 1. Code Review Prompts

#### Get Code Review Prompt
```http
GET /api/prompts/code-review
```

**Yanıt:**
```json
{
  "prompt_text": "Acting as a senior software engineer...",
  "system_suffix": "Provide detailed code review feedback...",
  "process_type": "code-review"
}
```

#### Save Code Review Prompt
```http
POST /api/prompts/code-review
Content-Type: application/json
```

**Request Body:**
```json
{
  "prompt": "Your custom code review prompt here..."
}
```

**Yanıt:**
```json
{
  "status": "success",
  "message": "Prompt saved successfully",
  "process_type": "code-review"
}
```

### 2. Requirement Analysis Prompts

#### Get Requirement Analysis Prompt
```http
GET /api/prompts/requirement-analysis
```

**Yanıt:**
```json
{
  "prompt_text": "Acting as a business analyst...",
  "system_suffix": "Analyze requirements thoroughly...",
  "process_type": "requirement-analysis"
}
```

#### Save Requirement Analysis Prompt
```http
POST /api/prompts/requirement-analysis
Content-Type: application/json
```

**Request Body:**
```json
{
  "prompt": "Your custom requirement analysis prompt..."
}
```

**Yanıt:**
```json
{
  "status": "success",
  "message": "Prompt saved successfully",
  "process_type": "requirement-analysis"
}
```

### 3. Test Planning Prompts

#### Get Test Planning Prompt
```http
GET /api/prompts/test-planning
```

**Yanıt:**
```json
{
  "prompt_text": "Acting as a test manager...",
  "system_suffix": "Create comprehensive test plans...",
  "process_type": "test-planning"
}
```

#### Save Test Planning Prompt
```http
POST /api/prompts/test-planning
Content-Type: application/json
```

**Request Body:**
```json
{
  "prompt": "Your custom test planning prompt..."
}
```

### 4. Environment Setup Prompts

#### Get Environment Setup Prompt
```http
GET /api/prompts/environment-setup
```

**Yanıt:**
```json
{
  "prompt_text": "Acting as a DevOps engineer...",
  "system_suffix": "Provide environment setup instructions...",
  "process_type": "environment-setup"
}
```

#### Save Environment Setup Prompt
```http
POST /api/prompts/environment-setup
Content-Type: application/json
```

**Request Body:**
```json
{
  "prompt": "Your custom environment setup prompt..."
}
```

### 5. Test Scenario Generation Prompts

#### Get Test Scenario Generation Prompt
```http
GET /api/prompts/test-scenario-generation
```

**Yanıt:**
```json
{
  "prompt_text": "Acting as a senior ISTQB-certified test analyst...",
  "process_type": "test-scenario-generation",
  "status": "success"
}
```

#### Save Test Scenario Generation Prompt
```http
POST /api/prompts/test-scenario-generation
Content-Type: application/json
```

**Request Body:**
```json
{
  "prompt": "Your custom test scenario generation prompt..."
}
```

**Yanıt:**
```json
{
  "status": "success",
  "message": "Test scenario generation prompt saved successfully",
  "process_type": "test-scenario-generation"
}
```

### 6. Test Execution Prompts

#### Get Test Execution Prompt
```http
GET /api/prompts/test-execution
```

**Yanıt:**
```json
{
  "base_prompt": "You are an AI test execution agent...",
  "system_suffix": "Execute the test code and return the raw output..."
}
```

#### Save Test Execution Prompt
```http
POST /api/prompts/test-execution
Content-Type: application/json
```

**Request Body:**
```json
{
  "base_prompt": "Your custom test execution prompt..."
}
```

**Yanıt:**
```json
{
  "success": true,
  "message": "Test execution prompt saved successfully"
}
```

---

## STLC Süreçleri

### 1. Code Review

```http
POST /api/processes/code-review/run
Content-Type: multipart/form-data
```

**Form Data:**
```
files: [File1.java, File2.py, ...]  (multiple files)
types: ["code", "config"]  (optional, array)
model: "llama3.2:3b"  (optional)
custom_prompt: "Custom review instructions..."  (optional)
session_id: "uuid-session-id"  (optional)
api_key: "your-api-key"  (optional, for API models)
```

**Yanıt:**
```json
{
  "status": "success",
  "session_id": "123e4567-e89b-12d3-a456-426614174000",
  "review_results": {
    "File1.java": {
      "issues_found": 3,
      "code_quality_score": 8.5,
      "suggestions": [
        "Consider using dependency injection",
        "Add input validation",
        "Improve error handling"
      ],
      "security_concerns": [],
      "best_practices": [
        "Follow SOLID principles",
        "Add unit tests"
      ]
    }
  },
  "summary": {
    "total_files": 2,
    "total_issues": 5,
    "average_quality_score": 8.2
  }
}
```

### 2. Requirement Analysis

```http
POST /api/processes/requirement_analysis/run
Content-Type: multipart/form-data
```

**Form Data:**
```
files: [requirements.txt, specs.pdf, ...]
types: ["requirement", "specification"]  (optional)
model: "qwen2.5:7b"  (optional)
custom_prompt: "Analyze requirements..."  (optional)
session_id: "uuid-session-id"  (optional)
api_key: "your-api-key"  (optional)
```

**Yanıt:**
```json
{
  "status": "success",
  "session_id": "223e4567-e89b-12d3-a456-426614174000",
  "analysis_results": {
    "functional_requirements": [
      {
        "id": "FR-001",
        "description": "User login functionality",
        "priority": "High",
        "testability": "High"
      }
    ],
    "non_functional_requirements": [
      {
        "id": "NFR-001",
        "description": "System response time < 2s",
        "type": "Performance",
        "measurable": true
      }
    ],
    "ambiguities": [
      "Clarification needed for payment processing flow"
    ],
    "missing_requirements": [
      "Error handling scenarios not specified"
    ]
  },
  "summary": {
    "total_requirements": 15,
    "functional": 10,
    "non_functional": 5,
    "clarity_score": 7.8
  }
}
```

### 3. Test Planning

```http
POST /api/processes/test-planning/run
Content-Type: multipart/form-data
```

**Form Data:**
```
files: [design_doc.pdf, requirements.txt, ...]
model: "gemini-2.5-flash"  (optional)
custom_prompt: "Create test plan..."  (optional)
session_id: "uuid-session-id"  (optional)
api_key: "AIzaSyXXXXXXXX"  (required for Gemini)
```

**Yanıt:**
```json
{
  "status": "success",
  "session_id": "323e4567-e89b-12d3-a456-426614174000",
  "test_plan": {
    "test_strategy": {
      "approach": "Risk-based testing",
      "test_levels": ["Unit", "Integration", "System", "UAT"],
      "test_types": ["Functional", "Performance", "Security"]
    },
    "scope": {
      "in_scope": ["User authentication", "Payment processing"],
      "out_of_scope": ["Third-party integrations"]
    },
    "resources": {
      "team_size": 5,
      "tools": ["Selenium", "JUnit", "JMeter"],
      "environment": "AWS Test Environment"
    },
    "schedule": {
      "start_date": "2026-02-01",
      "end_date": "2026-03-15",
      "milestones": [
        {
          "phase": "Unit Testing",
          "duration": "2 weeks"
        }
      ]
    },
    "risks": [
      {
        "risk": "Delayed API delivery",
        "impact": "High",
        "mitigation": "Use mock APIs"
      }
    ]
  }
}
```

### 4. Environment Setup

```http
POST /api/processes/environment-setup/run
Content-Type: multipart/form-data
```

**Form Data:**
```
files: [config.yml, docker-compose.yml, ...]
types: ["config", "setup"]
model: "codellama:7b"  (optional)
custom_prompt: "Setup instructions..."  (optional)
session_id: "uuid-session-id"  (optional)
environment_name: "Test Environment 1"  (required)
api_key: "your-api-key"  (optional)
```

**Yanıt:**
```json
{
  "status": "success",
  "session_id": "423e4567-e89b-12d3-a456-426614174000",
  "environment_name": "Test Environment 1",
  "setup_instructions": {
    "prerequisites": [
      "Docker 20.x or higher",
      "Node.js 18.x",
      "PostgreSQL 14.x"
    ],
    "installation_steps": [
      {
        "step": 1,
        "command": "docker-compose up -d",
        "description": "Start all services"
      },
      {
        "step": 2,
        "command": "npm install",
        "description": "Install dependencies"
      }
    ],
    "configuration": {
      "database": {
        "host": "localhost",
        "port": 5432,
        "database": "testdb"
      },
      "api_endpoint": "http://localhost:3000"
    },
    "validation": [
      "Check Docker containers are running",
      "Verify database connection",
      "Test API health endpoint"
    ]
  },
  "estimated_setup_time": "30 minutes"
}
```

### 5. Test Scenario Generation

#### Generate Custom Prompt
```http
POST /api/processes/test-scenario-generation/generate-prompt
Content-Type: application/json
```

**Request Body:**
```json
{
  "fileContents": [
    {
      "name": "UserService.java",
      "content": "public class UserService { ... }",
      "type": "code"
    }
  ],
  "test_category": "Functional",
  "test_type": "API Testing",
  "additional_context": "Focus on authentication flows"
}
```

**Yanıt:**
```json
{
  "generated_custom_prompt": "Generate comprehensive test scenarios for the UserService class...",
  "session_id": "523e4567-e89b-12d3-a456-426614174000",
  "status": "success"
}
```

#### Run Test Scenario Generation
```http
POST /api/processes/test-scenario-generation/run
Content-Type: multipart/form-data
```

**Form Data:**
```
files: [UserService.java, ProductController.js, ...]
model: "llama3.2:3b"
final_prompt: "Generate test scenarios focusing on..."
test_category: "Functional"  (optional)
test_type: "Integration"  (optional)
session_id: "523e4567-e89b-12d3-a456-426614174000"  (optional)
process_title: "User Module Testing"  (required)
api_key: "your-api-key"  (optional)
```

**Yanıt:**
```json
{
  "status": "success",
  "session_id": "523e4567-e89b-12d3-a456-426614174000",
  "process_title": "User Module Testing",
  "test_scenarios": [
    {
      "scenario_id": "TS-001",
      "title": "User Registration - Happy Path",
      "description": "Verify successful user registration with valid data",
      "preconditions": [
        "Database is accessible",
        "Email service is running"
      ],
      "test_steps": [
        {
          "step": 1,
          "action": "Navigate to registration page",
          "expected_result": "Registration form is displayed"
        },
        {
          "step": 2,
          "action": "Enter valid user details",
          "expected_result": "All fields accept input"
        },
        {
          "step": 3,
          "action": "Click Register button",
          "expected_result": "Success message displayed, confirmation email sent"
        }
      ],
      "priority": "High",
      "test_data": {
        "username": "testuser",
        "email": "test@example.com",
        "password": "SecurePass123!"
      }
    },
    {
      "scenario_id": "TS-002",
      "title": "User Registration - Invalid Email",
      "description": "Verify error handling for invalid email format",
      "test_steps": [
        {
          "step": 1,
          "action": "Enter invalid email format",
          "expected_result": "Email validation error displayed"
        }
      ],
      "priority": "Medium"
    }
  ],
  "summary": {
    "total_scenarios": 15,
    "by_priority": {
      "High": 8,
      "Medium": 5,
      "Low": 2
    },
    "coverage": {
      "positive_tests": 10,
      "negative_tests": 5
    }
  }
}
```

---

## Test Case Optimization

### 1. Get Available Models
```http
GET /api/test-case-optimization/models
```

**Yanıt:**
```json
{
  "success": true,
  "message": "Available models retrieved successfully",
  "data": [
    {
      "key": "llama3.2:3b",
      "name": "Llama 3.2 (3B)",
      "description": "Meta's latest efficient model",
      "type": "local"
    },
    {
      "key": "gemini-2.5-flash",
      "name": "Gemini 2.5 Flash",
      "description": "Google's latest fast model",
      "type": "api",
      "provider": "Google"
    }
  ]
}
```

### 2. Get Process Titles with Counts
```http
GET /api/test-case-optimization/process-titles-with-counts
```

**Yanıt:**
```json
{
  "success": true,
  "message": "Process titles with counts retrieved successfully",
  "data": [
    {
      "process_title": "User Module Testing",
      "test_case_count": 25,
      "last_updated": "2026-01-04T10:30:00Z"
    },
    {
      "process_title": "Payment Integration Tests",
      "test_case_count": 18,
      "last_updated": "2026-01-03T15:20:00Z"
    }
  ]
}
```

### 3. Get Test Cases by Process Title
```http
GET /api/test-case-optimization/test-cases/{process_title}
```

**Örnek:**
```http
GET /api/test-case-optimization/test-cases/User%20Module%20Testing
```

**Yanıt:**
```json
{
  "success": true,
  "message": "Test cases for User Module Testing retrieved successfully",
  "data": [
    {
      "test_case_id": "TC-001",
      "title": "Verify user login with valid credentials",
      "description": "Test successful login flow",
      "priority": "High",
      "status": "Active",
      "test_steps": [
        "Enter valid username",
        "Enter valid password",
        "Click login button"
      ],
      "expected_result": "User successfully logged in"
    }
  ]
}
```

### 4. Get Test Cases by Multiple Processes
```http
POST /api/test-case-optimization/test-cases-multi-process
Content-Type: application/json
```

**Request Body:**
```json
{
  "process_titles": [
    "User Module Testing",
    "Payment Integration Tests"
  ]
}
```

**Yanıt:**
```json
{
  "success": true,
  "message": "Test cases for 2 processes retrieved successfully",
  "data": {
    "User Module Testing": [
      {
        "test_case_id": "TC-001",
        "title": "User login test"
      }
    ],
    "Payment Integration Tests": [
      {
        "test_case_id": "TC-050",
        "title": "Payment processing test"
      }
    ]
  }
}
```

### 5. Smart Selection (Test Case Optimization)
```http
POST /api/test-case-optimization/smart-selection
Content-Type: application/json
```

**Request Body:**
```json
{
  "selected_test_cases": [
    {
      "test_case_id": "TC-001",
      "title": "User login test",
      "description": "Verify user can login with valid credentials"
    },
    {
      "test_case_id": "TC-002",
      "title": "Password reset",
      "description": "Test password reset functionality"
    }
  ],
  "process_titles": ["User Module Testing"],
  "process_title": "User Module Testing",
  "process_name": "User Testing Optimization",
  "custom_prompt": "Optimize these test cases for faster execution",
  "selected_model": "qwen2.5:7b",
  "api_key": "your-api-key",
  "optimization_type": "individual",
  "session_id": "623e4567-e89b-12d3-a456-426614174000"
}
```

**Optimization Types:**
- `"individual"`: Her test case ayrı ayrı optimize edilir
- `"bulk"`: Tüm test case'ler tek seferde optimize edilir
- `"parallel"`: Test case'ler paralel olarak optimize edilir

**Yanıt:**
```json
{
  "success": true,
  "session_id": "623e4567-e89b-12d3-a456-426614174000",
  "optimization_type": "individual",
  "optimized_test_cases": [
    {
      "original_id": "TC-001",
      "optimized_title": "User login - Happy path",
      "optimized_description": "Verify successful login with valid credentials",
      "optimized_steps": [
        "Navigate to login page",
        "Enter username: testuser@example.com",
        "Enter password: SecurePass123",
        "Click Login button",
        "Verify redirect to dashboard"
      ],
      "optimization_notes": "Combined redundant steps, added specific test data",
      "estimated_time_saved": "30 seconds"
    }
  ],
  "summary": {
    "total_optimized": 2,
    "total_time_saved": "1 minute",
    "quality_improvements": [
      "More specific test data",
      "Clearer expected results",
      "Removed redundant steps"
    ]
  }
}
```

---

## Test Code Generation

### 1. Get Available Environment Setups
```http
GET /api/processes/test-code-generation/environment-setups
```

**Yanıt:**
```json
{
  "success": true,
  "data": [
    {
      "session_id": "423e4567-e89b-12d3-a456-426614174000",
      "environment_name": "Test Environment 1",
      "created_at": "2026-01-04T10:00:00Z",
      "status": "active"
    }
  ],
  "count": 1
}
```

### 2. Get Available Process Titles
```http
GET /api/processes/test-code-generation/process-titles
```

**Yanıt:**
```json
{
  "success": true,
  "data": [
    "User Module Testing",
    "Payment Integration Tests"
  ],
  "count": 2
}
```

### 3. Generate Test Code
```http
POST /api/processes/test-code-generation/run
Content-Type: multipart/form-data
```

**Form Data:**
```
process_title: "User Module Testing"  (required)
environment_session_id: "423e4567-e89b-12d3-a456-426614174000"  (required)
environment_name: "User Module Test Code Gen"  (required)
files: [UserService.java, UserTest.template, ...]  (required)
model: "llama3.2:3b"  (optional, default: llama3.2:3b)
custom_prompt: "Generate JUnit tests..."  (optional)
session_id: "723e4567-e89b-12d3-a456-426614174000"  (optional)
output_format: "JSON"  (optional, default: JSON)
api_key: "your-api-key"  (optional)
```

**Yanıt:**
```json
{
  "status": "success",
  "session_id": "723e4567-e89b-12d3-a456-426614174000",
  "environment_name": "User Module Test Code Gen",
  "generated_tests": [
    {
      "test_class": "UserServiceTest",
      "test_framework": "JUnit 5",
      "code": "import org.junit.jupiter.api.Test;\nimport static org.junit.jupiter.api.Assertions.*;\n\nclass UserServiceTest {\n    @Test\n    void testUserLogin_ValidCredentials() {\n        UserService service = new UserService();\n        User user = service.login(\"test@example.com\", \"password123\");\n        assertNotNull(user);\n        assertEquals(\"test@example.com\", user.getEmail());\n    }\n}",
      "test_count": 1,
      "coverage_target": "User login functionality"
    }
  ],
  "summary": {
    "total_test_files": 1,
    "total_test_methods": 5,
    "estimated_coverage": "75%"
  }
}
```

---

## Test Execution

### 1. Get Process Names
```http
GET /api/test-execution/process-names
```

**Yanıt:**
```json
{
  "success": true,
  "process_names": [
    "User Module Test Code Gen",
    "Payment Test Code Gen"
  ],
  "total_count": 2
}
```

### 2. Get Process Records (Test Code History)
```http
GET /api/test-execution/process/{process_name}/records
```

**Örnek:**
```http
GET /api/test-execution/process/User%20Module%20Test%20Code%20Gen/records
```

**Yanıt:**
```json
{
  "success": true,
  "process_name": "User Module Test Code Gen",
  "records": [
    {
      "id": "723e4567-e89b-12d3-a456-426614174000",
      "session_id": "723e4567-e89b-12d3-a456-426614174000",
      "timestamp": "2026-01-04T11:30:00Z",
      "code_snippet": "import org.junit.jupiter.api.Test;\nclass UserServiceTest {...",
      "full_code": "...",
      "status": "available"
    }
  ],
  "total_count": 1
}
```

### 3. Get Individual Tests
```http
GET /api/test-execution/process/{process_name}/individual-tests
```

**Yanıt:**
```json
{
  "success": true,
  "process_name": "User Module Test Code Gen",
  "tests": [
    {
      "test_id": "test-001",
      "session_id": "723e4567-e89b-12d3-a456-426614174000",
      "test_index": 0,
      "code_snippet": "@Test\nvoid testUserLogin_ValidCredentials() {...",
      "full_code": "...",
      "test_name": "testUserLogin_ValidCredentials",
      "source_code": "UserService.java content..."
    }
  ],
  "total_count": 5
}
```

### 4. Execute Test Code (By Process Name)
```http
POST /api/test-execution/execute
Content-Type: application/json
```

**Request Body:**
```json
{
  "process_name": "User Module Test Code Gen",
  "model": "gemini-2.5-flash",
  "api_key": "AIzaSyXXXXXXXX"
}
```

**Yanıt:**
```json
{
  "success": true,
  "terminal_output": "Running tests...\n\nUserServiceTest:\n  ✓ testUserLogin_ValidCredentials (45ms)\n  ✓ testUserLogin_InvalidPassword (30ms)\n  ✓ testUserRegistration (52ms)\n\nTests: 3 passed, 3 total\nTime: 2.5s",
  "error": null,
  "provider": "gemini",
  "model_used": "gemini-2.5-flash",
  "timestamp": "2026-01-04T12:00:00Z"
}
```

### 5. Execute Selected Records
```http
POST /api/test-execution/execute-selected-records
Content-Type: application/json
```

**Request Body:**
```json
{
  "record_ids": [
    "723e4567-e89b-12d3-a456-426614174000",
    "823e4567-e89b-12d3-a456-426614174001"
  ],
  "model": "llama3.2:1b",
  "api_key": null
}
```

**Yanıt:**
```json
{
  "success": true,
  "terminal_output": "Executing 2 test records...\n\n[Record 1]\n✓ All tests passed\n\n[Record 2]\n✗ 1 test failed",
  "error": null,
  "provider": "lm_studio",
  "model_used": "llama3.2:1b",
  "timestamp": "2026-01-04T12:05:00Z"
}
```

### 6. Execute Selected Individual Tests
```http
POST /api/test-execution/execute-selected-tests
Content-Type: application/json
```

**Request Body:**
```json
{
  "test_ids": [
    "test-001",
    "test-003"
  ],
  "model": "qwen2.5:7b",
  "api_key": null
}
```

**Yanıt:**
```json
{
  "success": true,
  "terminal_output": "Executing selected tests...\n\n✓ testUserLogin_ValidCredentials\n✓ testUserRegistration",
  "error": null,
  "provider": "lm_studio",
  "model_used": "qwen2.5:7b",
  "timestamp": "2026-01-04T12:10:00Z"
}
```

---

## Test Reporting

### 1. Get Available Sessions
```http
POST /api/test-reporting/sessions
Content-Type: application/json
```

**Request Body:**
```json
{
  "process_names": ["code_review", "test_scenario_generation"],
  "date_from": "2026-01-01",
  "date_to": "2026-01-04"
}
```

**Yanıt:**
```json
{
  "success": true,
  "sessions": [
    {
      "session_id": "123e4567-e89b-12d3-a456-426614174000",
      "created_at": "2026-01-04T10:00:00Z",
      "processes": {
        "code_review": {
          "status": "completed",
          "files_analyzed": 5
        },
        "test_scenario_generation": {
          "status": "completed",
          "scenarios_generated": 15
        }
      }
    }
  ],
  "total_count": 1
}
```

### 2. Get Process Data
```http
POST /api/test-reporting/process-data
Content-Type: application/json
```

**Request Body:**
```json
{
  "session_id": "123e4567-e89b-12d3-a456-426614174000",
  "process_name": "code_review"
}
```

**Yanıt:**
```json
{
  "success": true,
  "process_name": "code_review",
  "data": {
    "files_analyzed": 5,
    "total_issues": 12,
    "critical_issues": 2,
    "code_quality_score": 8.5,
    "details": "..."
  },
  "error": null
}
```

### 3. Generate Comprehensive Report
```http
POST /api/test-reporting/generate-report
Content-Type: application/json
```

**Request Body:**
```json
{
  "session_ids": [
    "123e4567-e89b-12d3-a456-426614174000",
    "223e4567-e89b-12d3-a456-426614174001"
  ],
  "model": "gemini-2.5-pro",
  "api_key": "AIzaSyXXXXXXXX",
  "analysis_depth": "detailed",
  "custom_prompt": "Focus on security and performance issues"
}
```

**Analysis Depth Options:**
- `"summary"`: Özet rapor
- `"detailed"`: Detaylı analiz
- `"deep"`: Derin analiz (tüm metrikler)

**Yanıt:**
```json
{
  "success": true,
  "report_content": "# STLC Comprehensive Test Report\n\n## Executive Summary\n...\n\n## Code Review Analysis\n- Files Analyzed: 5\n- Issues Found: 12\n- Critical: 2\n- Code Quality: 8.5/10\n\n## Test Scenarios\n- Total Scenarios: 15\n- Coverage: 85%\n...",
  "report_id": "report-923e4567-e89b-12d3-a456-426614174000",
  "error": null,
  "metadata": {
    "sessions_analyzed": 2,
    "processes_included": [
      "code_review",
      "test_scenario_generation",
      "test_planning"
    ],
    "generated_at": "2026-01-04T13:00:00Z",
    "model_used": "gemini-2.5-pro"
  }
}
```

---

## Test Closure

### 1. Get Closure Metrics
```http
POST /api/test-closure/metrics
Content-Type: application/json
```

**Request Body:**
```json
{
  "session_ids": [
    "123e4567-e89b-12d3-a456-426614174000"
  ],
  "date_from": "2026-01-01",
  "date_to": "2026-01-04"
}
```

**Yanıt:**
```json
{
  "success": true,
  "metrics": {
    "total_sessions": 1,
    "total_tests_executed": 45,
    "passed": 42,
    "failed": 3,
    "pass_rate": 93.3,
    "total_test_cases": 50,
    "execution_coverage": 90.0,
    "processes_completed": {
      "code_review": 1,
      "test_scenario_generation": 1,
      "test_execution": 1
    },
    "defects": {
      "total": 3,
      "critical": 0,
      "major": 1,
      "minor": 2
    },
    "time_metrics": {
      "total_execution_time": "5 hours",
      "average_test_time": "6.7 minutes"
    }
  },
  "sessions_analyzed": 1,
  "error": null
}
```

### 2. Generate Closure Report
```http
POST /api/test-closure/generate-report
Content-Type: application/json
```

**Request Body:**
```json
{
  "session_ids": [
    "123e4567-e89b-12d3-a456-426614174000"
  ],
  "date_from": "2026-01-01",
  "date_to": "2026-01-04",
  "model": "gemini-2.5-flash",
  "api_key": "AIzaSyXXXXXXXX",
  "custom_prompt": "Emphasize lessons learned and recommendations"
}
```

**Yanıt:**
```json
{
  "success": true,
  "report_content": "# Test Cycle Closure Report\n\n## Overview\n- Test Cycle: Jan 2026\n- Sessions Analyzed: 1\n- Total Tests: 45\n- Pass Rate: 93.3%\n\n## Achievements\n✓ Successfully completed all STLC phases\n✓ High test coverage (90%)\n✓ Minimal critical defects\n\n## Defects Summary\n- Total Defects: 3\n- Critical: 0\n- Major: 1\n- Minor: 2\n\n## Recommendations\n1. Improve error handling in payment module\n2. Add more edge case tests\n3. Consider performance testing\n\n## Lessons Learned\n...",
  "metrics": {
    "total_sessions": 1,
    "pass_rate": 93.3,
    "execution_coverage": 90.0
  },
  "sessions_analyzed": 1,
  "model_used": "gemini-2.5-flash",
  "provider": "gemini",
  "timestamp": "2026-01-04T14:00:00Z",
  "error": null
}
```

---

## Docker Execution

### 1. Get Docker Status
```http
GET /api/docker-execution/status
```

**Yanıt:**
```json
{
  "docker_available": true,
  "images": [
    "python:3.11-slim",
    "node:18-alpine",
    "openjdk:17-slim"
  ],
  "container_status": {
    "running_containers": 2,
    "total_containers": 5,
    "images_count": 3
  }
}
```

### 2. Execute Test in Docker
```http
POST /api/docker-execution/execute
Content-Type: application/json
```

**Request Body:**
```json
{
  "test_code": "import unittest\n\nclass TestExample(unittest.TestCase):\n    def test_addition(self):\n        self.assertEqual(2 + 2, 4)\n\nif __name__ == '__main__':\n    unittest.main()",
  "language": "python",
  "base_image": "python:3.11-slim",
  "additional_packages": ["pytest", "requests"],
  "environment_vars": {
    "API_KEY": "test-key",
    "ENV": "test"
  },
  "timeout": 300
}
```

**Yanıt:**
```json
{
  "success": true,
  "output": "Running tests in Docker container...\n\n.\n----------------------------------------------------------------------\nRan 1 test in 0.001s\n\nOK",
  "error": null,
  "exit_code": 0,
  "execution_time": "2.5s",
  "container_info": {
    "container_id": "abc123def456",
    "image": "python:3.11-slim",
    "status": "exited"
  }
}
```

### 3. Execute Robot Simulation
```http
POST /api/docker-execution/execute-robot-simulation
Content-Type: application/json
```

**Request Body:**
```json
{
  "test_code": "# Test robot movement\nsuccess, pos = robot.move_to_position([0.5, 0.3, 0.2])\nprint(f'Position reached: {pos}')\n\nsuccess, pos = robot.move_to_position([1.0, 0.5, 0.1])\nprint(f'Final position: {pos}')",
  "robot_type": "industrial",
  "simulation_config": {
    "degrees_of_freedom": 6,
    "workspace_bounds": {
      "x": [0, 2],
      "y": [0, 2],
      "z": [0, 1.5]
    }
  }
}
```

**Yanıt:**
```json
{
  "success": true,
  "output": "🤖 Robot Arm Simulation Started\n\nInitializing 6-DOF industrial robot...\nPosition reached: [0.5, 0.3, 0.2]\nFinal position: [1.0, 0.5, 0.1]\n\nSimulation completed successfully",
  "error": null,
  "exit_code": 0,
  "execution_time": "3.2s",
  "container_info": {
    "container_id": "robot-sim-789",
    "image": "robot-simulation:latest",
    "status": "exited"
  }
}
```

### 4. Execute Tests from Process
```http
POST /api/docker-execution/execute-from-process
Content-Type: application/json
```

**Request Body:**
```json
{
  "process_name": "User Module Test Code Gen",
  "language": "python",
  "additional_packages": ["pytest", "pytest-cov"],
  "environment_vars": {
    "DB_HOST": "localhost",
    "DB_PORT": "5432"
  },
  "timeout": 300
}
```

**Yanıt:**
```json
{
  "success": true,
  "output": "Fetching test code from process: User Module Test Code Gen\n\nExecuting tests in Docker...\n\n============================= test session starts ==============================\ncollected 5 items\n\ntest_user_service.py .....                                              [100%]\n\n============================== 5 passed in 1.23s ===============================",
  "error": null,
  "exit_code": 0,
  "execution_time": "5.4s",
  "container_info": {
    "container_id": "test-exec-456",
    "image": "python:3.11-slim",
    "status": "exited"
  }
}
```

### 5. Pull Docker Image
```http
POST /api/docker-execution/pull-image
Content-Type: application/json
```

**Request Body:**
```json
{
  "image_name": "python:3.12-slim"
}
```

**Yanıt:**
```json
{
  "success": true,
  "message": "Image pulled successfully",
  "image": "python:3.12-slim",
  "size": "125MB"
}
```

---

## Hata Kodları ve Mesajları

### HTTP Status Codes

| Status Code | Açıklama |
|-------------|----------|
| 200 | Başarılı istek |
| 400 | Hatalı istek (eksik veya geçersiz parametreler) |
| 404 | Kaynak bulunamadı |
| 500 | Sunucu hatası |
| 503 | Servis kullanılamıyor (Docker, LM Studio vb.) |

### Yaygın Hata Yanıtları

```json
{
  "detail": "No files uploaded."
}
```

```json
{
  "detail": "API key is required for Gemini models"
}
```

```json
{
  "detail": "Docker is not available. Please ensure Docker is installed and running."
}
```

```json
{
  "detail": "Session not found with session_id: xxx"
}
```

---

## Önemli Notlar

### 1. Model Kullanımı

- **Local Models (LM Studio)**: API key gerektirmez
- **API Models (Gemini)**: `api_key` parametresi zorunludur

### 2. File Upload

Tüm file upload işlemleri `multipart/form-data` kullanır:
```
Content-Type: multipart/form-data
```

### 3. Session Management

Her işlem için `session_id` otomatik üretilebilir veya manuel sağlanabilir. Session ID'ler MongoDB'de saklanır ve tüm süreçlerde takip edilir.

### 4. Async Operations

Tüm endpoint'ler asenkron çalışır ve await mekanizması kullanır.

### 5. Database

Backend MongoDB kullanır:
- Database: `stlc_data`
- Collections: `session_history`, `prompts_base`, `test_cases`, vb.

### 6. CORS

Backend'e herhangi bir platformdan (web, mobile, desktop) istek atabilirsiniz.

---

## Örnek Kullanım Senaryoları

### Senaryo 1: Tam STLC Döngüsü

```bash
# 1. Code Review
curl -X POST http://localhost:8000/api/processes/code-review/run \
  -F "files=@UserService.java" \
  -F "model=llama3.2:3b"

# 2. Requirement Analysis
curl -X POST http://localhost:8000/api/processes/requirement_analysis/run \
  -F "files=@requirements.txt" \
  -F "model=qwen2.5:7b"

# 3. Test Planning
curl -X POST http://localhost:8000/api/processes/test-planning/run \
  -F "files=@design.pdf" \
  -F "model=gemini-2.5-flash" \
  -F "api_key=AIzaSyXXXX"

# 4. Test Scenario Generation
curl -X POST http://localhost:8000/api/processes/test-scenario-generation/run \
  -F "files=@UserService.java" \
  -F "model=llama3.2:3b" \
  -F "process_title=User Module Testing" \
  -F "final_prompt=Generate comprehensive test scenarios"

# 5. Test Code Generation
curl -X POST http://localhost:8000/api/processes/test-code-generation/run \
  -F "process_title=User Module Testing" \
  -F "environment_session_id=env-session-id" \
  -F "environment_name=Test Code Gen" \
  -F "files=@UserService.java" \
  -F "model=codellama:7b"

# 6. Test Execution
curl -X POST http://localhost:8000/api/test-execution/execute \
  -H "Content-Type: application/json" \
  -d '{"process_name":"Test Code Gen","model":"gemini-2.5-flash","api_key":"AIzaSyXXXX"}'

# 7. Test Reporting
curl -X POST http://localhost:8000/api/test-reporting/generate-report \
  -H "Content-Type: application/json" \
  -d '{"session_ids":["session-1"],"model":"gemini-2.5-pro","api_key":"AIzaSyXXXX"}'

# 8. Test Closure
curl -X POST http://localhost:8000/api/test-closure/generate-report \
  -H "Content-Type: application/json" \
  -d '{"session_ids":["session-1"],"model":"gemini-2.5-flash","api_key":"AIzaSyXXXX"}'
```

### Senaryo 2: Python ile API Kullanımı

```python
import requests

BASE_URL = "http://localhost:8000"

# Test scenario generation
files = {'files': open('UserService.java', 'rb')}
data = {
    'model': 'llama3.2:3b',
    'process_title': 'User Testing',
    'final_prompt': 'Generate test scenarios'
}

response = requests.post(
    f"{BASE_URL}/api/processes/test-scenario-generation/run",
    files=files,
    data=data
)

print(response.json())
```

### Senaryo 3: Postman Collection

```json
{
  "info": {
    "name": "STLC Manager API",
    "schema": "https://schema.getpostman.com/json/collection/v2.1.0/collection.json"
  },
  "item": [
    {
      "name": "Health Check",
      "request": {
        "method": "GET",
        "header": [],
        "url": {
          "raw": "http://localhost:8000/",
          "protocol": "http",
          "host": ["localhost"],
          "port": "8000",
          "path": [""]
        }
      }
    },
    {
      "name": "Get Models",
      "request": {
        "method": "GET",
        "header": [],
        "url": {
          "raw": "http://localhost:8000/api/models/?model_type=local",
          "protocol": "http",
          "host": ["localhost"],
          "port": "8000",
          "path": ["api", "models", ""],
          "query": [
            {
              "key": "model_type",
              "value": "local"
            }
          ]
        }
      }
    }
  ]
}
```

---

## Sonuç

Bu dokümantasyon, STLC Manager Backend'inin tüm endpoint'lerini, giriş-çıkış formatlarını ve kullanım senaryolarını kapsamaktadır. Backend tamamen platform-bağımsız bir RESTful API olarak tasarlanmıştır ve herhangi bir frontend teknolojisi, mobil uygulama veya script ile entegre edilebilir.

**Önemli Linkler:**
- Backend Repo: [stlc-man](https://github.com/cembglm/stlc-man)
- API Base URL: `http://localhost:8000`
- Health Check: `http://localhost:8000/`
- Swagger UI: `http://localhost:8000/docs` (FastAPI otomatik dokümantasyon)
- ReDoc: `http://localhost:8000/redoc` (Alternatif dokümantasyon)

**Version:** 0.1.0  
**Son Güncelleme:** 4 Ocak 2026
