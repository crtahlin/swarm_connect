# swarm_connect
Simpler server for accessing some Swarm features.

## Project structure

```
swarm_api_aggregator/
├── app/                    # Main application package
│   ├── __init__.py
│   ├── main.py             # FastAPI app instantiation and router inclusion
│   ├── api/                # API specific modules
│   │   ├── __init__.py
│   │   ├── deps.py         # Dependency injection functions (e.g., for auth later)
│   │   ├── endpoints/      # API route definitions
│   │   │   ├── __init__.py
│   │   │   └── stamps.py   # Endpoint(s) related to Swarm Stamps
│   │   └── models/         # Pydantic models for request/response validation
│   │       ├── __init__.py
│   │       └── stamp.py    # Pydantic model(s) for Stamp data
│   ├── core/               # Core application logic/configuration
│   │   ├── __init__.py
│   │   ├── config.py       # Configuration management (e.g., loading .env)
│   │   └── security.py     # Security related functions (auth, https setup later)
│   └── services/           # Logic for interacting with external services
│       ├── __init__.py
│       └── swarm_api.py    # Functions to call the EthSwarm Bee API
│
├── tests/                  # Unit and integration tests (Recommended)
│   └── ...
│
├── .env                    # Environment variables (API keys, URLs - NOT committed to Git)
├── .env.example            # Example environment file (Committed to Git)
├── .gitignore              # Files/directories to ignore in Git
├── requirements.txt        # Python package dependencies
├── README.md               # Project description, setup, and usage instructions
└── run.py                  # Script to easily run the development server
``` 

## Running



```
python3 -m venv /path/to/pythonvenv
# use the binaries in that folder from now on

pip install -r requirements.txt

# Copy .env.example to .env.

# Edit .env and ensure SWARM_BEE_API_URL points to your Bee node's API endpoint (e.g., http://localhost:1633 or the public gateway https://api.gateway.ethswarm.org).

# if port 8000 is taken, use a different one, e.g.:
export PORT=8001

```

## Architecture

Swarm Connect is a FastAPI-based API gateway that simplifies access to Ethereum Swarm (distributed storage network) functionality. Instead of clients directly calling complex Swarm Bee node APIs, they can use this cleaner, more focused interface.

### System Overview

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                              CLIENT APPLICATIONS                            │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐  ┌─────────────────────┐ │
│  │   Web Apps  │  │  Mobile App │  │  CLI Tools  │  │  Third-party Apps   │ │
│  └─────────────┘  └─────────────┘  └─────────────┘  └─────────────────────┘ │
└─────────────────────────────────────────────────────────────────────────────┘
                                    │
                           HTTP/HTTPS Requests
                                    │
┌─────────────────────────────────────────────────────────────────────────────┐
│                          SWARM CONNECT API GATEWAY                         │
│                              (FastAPI)                                     │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │                        API LAYER                                   │   │
│  │  ┌─────────────────┐  ┌─────────────────┐  ┌─────────────────────┐ │   │
│  │  │   Health Check  │  │   OpenAPI Docs  │  │   Stamps Endpoint   │ │   │
│  │  │   GET /         │  │   /docs /redoc  │  │ GET /api/v1/stamps/ │ │   │
│  │  └─────────────────┘  └─────────────────┘  └─────────────────────┘ │   │
│  └─────────────────────────────────────────────────────────────────────┘   │
│                                    │                                       │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │                      VALIDATION LAYER                              │   │
│  │  ┌─────────────────┐  ┌─────────────────┐  ┌─────────────────────┐ │   │
│  │  │  Request/Response│  │   StampDetails  │  │  Error Handling &   │ │   │
│  │  │    Validation   │  │   Pydantic Model│  │   HTTP Status Codes │ │   │
│  │  └─────────────────┘  └─────────────────┘  └─────────────────────┘ │   │
│  └─────────────────────────────────────────────────────────────────────┘   │
│                                    │                                       │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │                      BUSINESS LOGIC LAYER                          │   │
│  │  ┌─────────────────┐  ┌─────────────────┐  ┌─────────────────────┐ │   │
│  │  │  Stamp Filtering│  │  TTL Calculation│  │   Expiration Time   │ │   │
│  │  │   by Batch ID   │  │   & Processing  │  │   Formatting        │ │   │
│  │  └─────────────────┘  └─────────────────┘  └─────────────────────┘ │   │
│  └─────────────────────────────────────────────────────────────────────┘   │
│                                    │                                       │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │                        SERVICE LAYER                               │   │
│  │  ┌─────────────────┐  ┌─────────────────┐  ┌─────────────────────┐ │   │
│  │  │  Swarm API      │  │  HTTP Client    │  │   Error Recovery &  │ │   │
│  │  │  Integration    │  │  (Requests)     │  │   Retry Logic       │ │   │
│  │  └─────────────────┘  └─────────────────┘  └─────────────────────┘ │   │
│  └─────────────────────────────────────────────────────────────────────┘   │
│                                    │                                       │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │                     CONFIGURATION LAYER                            │   │
│  │  ┌─────────────────┐  ┌─────────────────┐  ┌─────────────────────┐ │   │
│  │  │  Environment    │  │   Settings      │  │   URL Validation &  │ │   │
│  │  │  Variables      │  │   Management    │  │   Caching           │ │   │
│  │  └─────────────────┘  └─────────────────┘  └─────────────────────┘ │   │
│  └─────────────────────────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────────────────────────┘
                                    │
                           HTTP Requests (10s timeout)
                                    │
┌─────────────────────────────────────────────────────────────────────────────┐
│                              SWARM BEE NODE                                │
│                           (localhost:1633)                                 │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │                        BEE API ENDPOINTS                           │   │
│  │  ┌─────────────────┐  ┌─────────────────┐  ┌─────────────────────┐ │   │
│  │  │   GET /batches  │  │   Stamp Data    │  │   Blockchain        │ │   │
│  │  │   (All Stamps)  │  │   Repository    │  │   Integration       │ │   │
│  │  └─────────────────┘  └─────────────────┘  └─────────────────────┘ │   │
│  └─────────────────────────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────────────────────────┘
```

### Core Features

#### 🚀 API Features
- **Stamp Lookup**: Retrieve detailed information about specific Swarm postage stamps by batch ID
- **Expiration Calculation**: Automatically calculates stamp expiration time (current time + TTL)
- **Data Aggregation**: Fetches all stamps and filters for specific ones
- **JSON API**: RESTful endpoints with structured JSON responses

#### 🔧 Technical Features
- **FastAPI Framework**: Modern, fast web framework with automatic OpenAPI documentation
- **Auto-Documentation**: Interactive API docs at `/docs` and `/redoc`
- **Type Validation**: Pydantic models ensure data integrity and type safety
- **Error Handling**: Comprehensive error responses with appropriate HTTP status codes
- **Configuration Management**: Environment-based settings with validation
- **Development Server**: Hot-reload development server with SSL support

#### 🛡️ Reliability Features
- **Request Timeouts**: 10-second timeout for external API calls
- **Error Recovery**: Multiple layers of exception handling
- **Flexible Response Parsing**: Handles different Swarm API response formats
- **Logging**: Structured logging for debugging and monitoring
- **Health Checks**: Basic health check endpoint for monitoring

### Component Architecture

#### Configuration Layer (`app/core/config.py`)
- Loads environment variables on startup
- Validates Swarm Bee API URL format
- Provides cached settings to all components

#### API Layer (`app/main.py` + `app/api/endpoints/`)
- Receives HTTP requests and routes them
- Applies path parameters and validation
- Returns structured JSON responses

#### Service Layer (`app/services/swarm_api.py`)
- Makes HTTP calls to Swarm Bee node
- Handles network errors and timeouts
- Parses and normalizes API responses

#### Model Layer (`app/api/models/stamp.py`)
- Validates response data structure
- Handles optional fields and type conversion
- Formats output for API consumers

### Data Flow

```
1. Client → FastAPI Router → Endpoint Handler
2. Endpoint → Service Layer → External Swarm API
3. Service → Business Logic → Data Processing
4. Response ← Pydantic Model ← Formatted Data
```

### Key Value Propositions

1. **Simplified Interface**: Clean REST API vs complex Swarm protocols
2. **Enhanced Data**: Adds calculated expiration times to raw stamp data
3. **Reliability**: Robust error handling and timeout management
4. **Developer Experience**: Auto-generated docs and type safety
5. **Flexibility**: Configurable for different Swarm node endpoints
