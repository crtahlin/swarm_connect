# app/services/swarm_api.py
import requests
from requests.exceptions import RequestException
import logging
from typing import List, Dict, Any, Optional
from urllib.parse import urljoin

from app.core.config import settings

logger = logging.getLogger(__name__)

def get_all_stamps() -> List[Dict[str, Any]]:
    """
    Fetches all postage stamp batches from the configured Swarm Bee node.

    Returns:
        A list of dictionaries, each representing a stamp batch.
        Returns an empty list if the request fails or no stamps are found.

    Raises:
        RequestException: If the HTTP request to the Swarm API fails.
    """
    api_url = urljoin(str(settings.SWARM_BEE_API_URL), "batches")
    try:
        response = requests.get(api_url, timeout=10) # Add a timeout
        response.raise_for_status() # Raise HTTPError for bad responses (4xx or 5xx)

        data = response.json()
        if isinstance(data, dict) and "batches" in data:
            # Handle potential API structure variations, ensure it's a list
            batches = data.get("batches")
            if isinstance(batches, list):
                 return batches
            else:
                logger.warning(f"Swarm API response 'batches' field is not a list: {type(batches)}")
                return []
        elif isinstance(data, list):
             # Handle case where API directly returns a list
             return data
        else:
             logger.warning(f"Unexpected data structure from Swarm API: {type(data)}")
             return []


    except RequestException as e:
        logger.error(f"Error fetching stamps from Swarm API ({api_url}): {e}")
        # Re-raise the exception to be handled by the endpoint,
        # or return empty list/None depending on desired behavior
        raise # Let the endpoint handle it with a 50x error

    except Exception as e:
        # Catch other potential errors like JSON decoding
        logger.error(f"An unexpected error occurred while processing Swarm API response: {e}")
        raise # Propagate unexpected errors


def purchase_postage_stamp(amount: int, depth: int, label: Optional[str] = None) -> str:
    """
    Purchases a new postage stamp from the configured Swarm Bee node.

    Args:
        amount: The amount of the postage stamp in wei
        depth: The depth of the postage stamp
        label: Optional user-defined label for the stamp

    Returns:
        The batchID of the purchased stamp

    Raises:
        RequestException: If the HTTP request to the Swarm API fails
        ValueError: If the response is malformed or missing expected fields
    """
    api_url = urljoin(str(settings.SWARM_BEE_API_URL), f"stamps/{amount}/{depth}")
    headers = {"Content-Type": "application/json"}

    # Prepare request body if label is provided
    request_body = {}
    if label:
        request_body["label"] = label

    try:
        if request_body:
            response = requests.post(api_url, json=request_body, headers=headers, timeout=120)
        else:
            response = requests.post(api_url, headers=headers, timeout=120)

        response.raise_for_status()
        response_json = response.json()

        batch_id = response_json.get("batchID")
        if not batch_id:
            raise ValueError("API Response missing 'batchID' from purchase")

        logger.info(f"Successfully purchased stamp with batch ID: {batch_id}")
        return batch_id

    except requests.exceptions.RequestException as e:
        logger.error(f"Error purchasing stamp from Swarm API ({api_url}): {e}")
        raise
    except (ValueError, KeyError) as e:
        logger.error(f"Error parsing stamp purchase response: {e}")
        raise ValueError(f"Could not parse stamp purchase response: {e}") from e


def extend_postage_stamp(stamp_id: str, amount: int) -> str:
    """
    Extends an existing postage stamp by adding more funds to it.

    Args:
        stamp_id: The batch ID of the stamp to extend
        amount: Additional amount to add to the stamp in wei

    Returns:
        The batchID of the extended stamp (should be same as input stamp_id)

    Raises:
        RequestException: If the HTTP request to the Swarm API fails
        ValueError: If the response is malformed or missing expected fields
    """
    api_url = urljoin(str(settings.SWARM_BEE_API_URL), f"stamps/topup/{stamp_id}/{amount}")
    headers = {"Content-Type": "application/json"}

    try:
        response = requests.patch(api_url, headers=headers, timeout=120)
        response.raise_for_status()

        # The topup endpoint typically returns the updated batch information
        # We'll extract the batchID to confirm the operation
        response_json = response.json()
        batch_id = response_json.get("batchID", stamp_id)  # Fallback to original stamp_id

        logger.info(f"Successfully extended stamp {stamp_id} with amount {amount}")
        return batch_id

    except requests.exceptions.RequestException as e:
        logger.error(f"Error extending stamp {stamp_id} from Swarm API ({api_url}): {e}")
        raise
    except (ValueError, KeyError) as e:
        logger.error(f"Error parsing stamp extension response for {stamp_id}: {e}")
        raise ValueError(f"Could not parse stamp extension response: {e}") from e


def calculate_usable_status(stamp: Dict[str, Any]) -> bool:
    """
    Calculates if a stamp is usable based on available data.
    A stamp is considered usable if:
    1. It has a positive TTL (not expired)
    2. It exists
    3. It's not immutable or has reasonable depth for uploads

    Args:
        stamp: The stamp data from /batches endpoint

    Returns:
        Boolean indicating if the stamp is usable
    """
    try:
        # Check if stamp exists
        if not stamp.get("exists", True):
            return False

        # Check TTL - if TTL is very low, stamp is likely expired or about to expire
        batch_ttl = int(stamp.get("batchTTL", 0))
        if batch_ttl <= 0:
            return False

        # Check if it's immutable - immutable stamps may have restrictions
        is_immutable = stamp.get("immutableFlag", False) or stamp.get("immutable", False)

        # For immutable stamps, require higher TTL threshold for safety
        min_ttl = 3600 if is_immutable else 60  # 1 hour for immutable, 1 minute for regular

        if batch_ttl < min_ttl:
            return False

        # Additional checks could include:
        # - Depth validation (reasonable depth for uploads)
        # - Amount validation (sufficient balance)
        depth = stamp.get("depth", 0)
        if depth < 16 or depth > 32:  # Reasonable depth range
            return False

        return True

    except (ValueError, TypeError) as e:
        logger.warning(f"Error calculating usable status for stamp: {e}")
        return False


def get_all_stamps_processed() -> List[Dict[str, Any]]:
    """
    Fetches all postage stamp batches and processes them with expiration calculations.
    Calculates the usable field based on stamp properties like TTL, depth, and immutability.

    Returns:
        A list of processed stamp dictionaries with calculated expiration times and usable status.

    Raises:
        RequestException: If the HTTP request to the Swarm API fails.
    """
    import datetime

    # Get raw stamps data from /batches endpoint
    all_stamps = get_all_stamps()
    processed_stamps = []

    for stamp in all_stamps:
        try:
            batch_id = stamp.get("batchID")
            if not batch_id:
                logger.warning("Skipping stamp with missing batchID")
                continue

            # Calculate expiration time for each stamp
            batch_ttl = int(stamp.get("batchTTL", 0))
            if batch_ttl < 0:
                logger.warning(f"Stamp {batch_id} has negative TTL: {batch_ttl}. Treating as 0.")
                batch_ttl = 0

            # Calculate expiration based on current time + TTL
            now_utc = datetime.datetime.now(datetime.timezone.utc)
            expiration_time_utc = now_utc + datetime.timedelta(seconds=batch_ttl)
            expiration_str = expiration_time_utc.strftime('%Y-%m-%d-%H-%M')

            # Calculate usable status based on available stamp data
            usable = calculate_usable_status(stamp)

            # Create processed stamp data
            processed_stamp = {
                "batchID": batch_id,
                "utilization": stamp.get("utilization"),
                "usable": usable,
                "label": stamp.get("label"),
                "depth": stamp.get("depth"),
                "amount": str(stamp.get("amount", "")),  # Ensure amount is string
                "bucketDepth": stamp.get("bucketDepth"),
                "blockNumber": stamp.get("blockNumber"),
                "immutableFlag": stamp.get("immutableFlag"),
                "batchTTL": batch_ttl,
                "exists": stamp.get("exists", True),
                "expectedExpiration": expiration_str
            }
            processed_stamps.append(processed_stamp)

        except (ValueError, TypeError, KeyError) as e:
            logger.warning(f"Skipping malformed stamp data: {e}")
            continue

    return processed_stamps


def upload_data_to_swarm(data: bytes, stamp_id: str, content_type: str = "application/json") -> str:
    """
    Uploads data to the Swarm network using the configured Bee node.

    Args:
        data: The data to upload as bytes
        stamp_id: The postage stamp batch ID to use for the upload
        content_type: MIME type of the content

    Returns:
        The Swarm reference hash of the uploaded data

    Raises:
        RequestException: If the HTTP request to the Swarm API fails
        ValueError: If the response is malformed or missing expected fields
    """
    api_url = urljoin(str(settings.SWARM_BEE_API_URL), "bzz")
    headers = {
        "Swarm-Postage-Batch-Id": stamp_id.lower(),
        "Content-Type": content_type
    }

    try:
        response = requests.post(api_url, data=data, headers=headers, timeout=60)
        response.raise_for_status()

        response_json = response.json()
        reference = response_json.get("reference")
        if not reference:
            raise ValueError("API Response missing 'reference' from upload")

        logger.info(f"Successfully uploaded data to Swarm with reference: {reference}")
        return reference

    except requests.exceptions.RequestException as e:
        logger.error(f"Error uploading data to Swarm API ({api_url}): {e}")
        raise
    except (ValueError, KeyError) as e:
        logger.error(f"Error parsing data upload response: {e}")
        raise ValueError(f"Could not parse data upload response: {e}") from e


def download_data_from_swarm(reference: str) -> bytes:
    """
    Downloads data from the Swarm network using a reference hash.

    Args:
        reference: The Swarm reference hash of the data to download

    Returns:
        The downloaded data as bytes

    Raises:
        RequestException: If the HTTP request to the Swarm API fails
        FileNotFoundError: If the data is not found (404)
    """
    api_url = urljoin(str(settings.SWARM_BEE_API_URL), f"bzz/{reference.lower()}")

    try:
        response = requests.get(api_url, timeout=60)

        if response.status_code == 404:
            raise FileNotFoundError(f"Data not found on Swarm at reference {reference}")

        response.raise_for_status()

        logger.info(f"Successfully downloaded {len(response.content)} bytes from Swarm reference: {reference}")
        return response.content

    except requests.exceptions.RequestException as e:
        logger.error(f"Error downloading data from Swarm API ({api_url}): {e}")
        raise
