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
