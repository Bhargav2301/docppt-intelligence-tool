from fastapi import APIRouter
from runtime.registry import registry

router = APIRouter(prefix="/api/models", tags=["models"])

@router.get("/status")
def get_model_status():
    """
    Returns the current configuration mode and the list of models currently loaded in memory.
    """
    return registry.get_loaded_models_status()
