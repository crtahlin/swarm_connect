# app/api/models/stamp.py
from pydantic import BaseModel, Field
from typing import Optional

class StampDetails(BaseModel):
    """
    Pydantic model representing the processed stamp information served by our API.
    """
    batchID: str
    utilization: int
    usable: bool
    label: Optional[str] = None # Use Optional for fields that might be null/missing
    depth: int
    amount: str # Keep as string if the API returns large numbers as strings
    bucketDepth: int
    blockNumber: int
    immutableFlag: bool
    batchTTL: int = Field(..., description="Original Time-To-Live in seconds")
    exists: bool = Field(..., description="Indicates if the batch exists on the node") # Added based on example response
    expectedExpiration: str = Field(..., description="Calculated expiration timestamp (YYYY-MM-DD-HH-MM UTC)")

    class Config:
        # Optional: If you want to allow creating models from dicts
        # that have extra fields not defined here (they will be ignored)
        # extra = "ignore"

        # Optional: Example for generating OpenAPI schema
        schema_extra = {
            "example": {
                "batchID": "a1b2c3d4e5f6...",
                "utilization": 4,
                "usable": True,
                "label": "my-label",
                "depth": 20,
                "amount": "100000000000000000",
                "bucketDepth": 16,
                "blockNumber": 1234567,
                "immutableFlag": False,
                "batchTTL": 31536000,
                "exists": True,
                "expectedExpiration": "2024-12-31-23-59"
            }
        }
