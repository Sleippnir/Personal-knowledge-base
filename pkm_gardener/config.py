import os

# --- Paths ---
PKM_ROOT = r"D:\PKM"
INBOX_PATH = os.path.join(PKM_ROOT, "00_Inbox")
RESOURCES_PATH = os.path.join(PKM_ROOT, "03_Resources")
AREAS_PATH = os.path.join(PKM_ROOT, "02_Areas")
PROJECTS_PATH = os.path.join(PKM_ROOT, "01_Projects") # Added for completeness

# --- Gemini API Configuration ---
# IMPORTANT: For production, load API_KEY from environment variables for security.
# Example: GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
from .api import GEMINI_API_KEY
GEMINI_MODEL_NAME = "gemini-pro"

# --- Processing Settings ---
DRY_RUN = False # Set to True to simulate file operations without actually moving/modifying files
