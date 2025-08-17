import os

# --- Paths ---
def find_pkm_root():
    """
    Finds the root of the PKM vault by searching upwards from the current directory
    for a `.obsidian` folder.
    """
    current_dir = os.getcwd()
    while True:
        if ".obsidian" in os.listdir(current_dir):
            return current_dir
        parent_dir = os.path.dirname(current_dir)
        if parent_dir == current_dir:
            # Reached the filesystem root
            raise FileNotFoundError("Could not find PKM root. No '.obsidian' directory found in any parent folder.")
        current_dir = parent_dir

MAX_DOCUMENT_SIZE_FOR_PROCESSING = 1000
PKM_ROOT = find_pkm_root()
INBOX_PATH = os.path.join(PKM_ROOT, "00_Inbox")
RESOURCES_PATH = os.path.join(PKM_ROOT, "03_Resources")
AREAS_PATH = os.path.join(PKM_ROOT, "02_Areas")
PROJECTS_PATH = os.path.join(PKM_ROOT, "01_Projects")

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

GEMINI_MODEL_NAME = "gemini-pro"

# --- Processing Settings ---
DRY_RUN = False # Set to True to simulate file operations without actually moving/modifying files
