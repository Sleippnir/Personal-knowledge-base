from dataclasses import dataclass, field
from typing import Optional, Dict, Any

@dataclass
class ProcessingJob:
    original_filepath: str
    original_filename: str
    content: str | bytes
    file_type: str
    metadata: Dict[str, Any] = field(default_factory=dict)
    metadata_str: Optional[str] = None # To store the YAML string from LLM
    suggested_filename: Optional[str] = None
    suggested_folder_path: Optional[str] = None
    summary: Optional[str] = None
    status: str = "pending"  # 'pending', 'success', 'failure', 'needs_review'
    error_message: Optional[str] = None
