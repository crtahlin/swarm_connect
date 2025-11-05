# app/api/models/wallet.py
from pydantic import BaseModel
from typing import Optional


class WalletResponse(BaseModel):
    """
    Response model for wallet endpoint with address and balance information.
    """
    walletAddress: str
    bzzBalance: Optional[str] = None  # BZZ balance in wei as string


class ChequebookResponse(BaseModel):
    """
    Response model for chequebook endpoint with address and balance information.
    """
    chequebookAddress: str
    availableBalance: Optional[str] = None  # Available balance in wei as string
    totalBalance: Optional[str] = None  # Total balance in wei as string