import os

# --- Paths ---
PKM_ROOT = "."
INBOX_PATH = os.path.join(PKM_ROOT, "00_Inbox")
RESOURCES_PATH = os.path.join(PKM_ROOT, "03_Resources")
AREAS_PATH = os.path.join(PKM_ROOT, "02_Areas")
PROJECTS_PATH = os.path.join(PKM_ROOT, "01_Projects") # Added for completeness

# --- Gemini API Configuration ---
# The application will first try to load the API key from the `GEMINI_API_KEY` environment variable.
# If it's not found, it will fall back to importing it from the `pkm_gardener/api.py` file.
# This file is git-ignored for security. See `pkm_gardener/api.py` for more details.
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
if not GEMINI_API_KEY:
    try:
        from .api import GEMINI_API_KEY as key_from_file
        GEMINI_API_KEY = key_from_file
    except (ImportError, AttributeError):
        pass # Will be handled below

if not GEMINI_API_KEY:
    raise ValueError("GEMINI_API_KEY is not set. Please set it as an environment variable or in `pkm_gardener/api.py`.")

GEMINI_MODEL_NAME = "gemini-1.5-flash-latest"

# --- Processing Settings ---
DRY_RUN = False # Set to True to simulate file operations without actually moving/modifying files
