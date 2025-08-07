# SOP: PKM Gardener System Implementation

## 1. Objective & Guiding Principles

### Objective

To refactor the provided monolithic Python script (llm_gardener.py) into a modular, scalable, and maintainable application named `pkm_gardener`. This document outlines the final architecture, the responsibilities of each module, and the data flow between them. The initial script should be used as the primary reference for the core logic.

### Guiding Principles

- **Clarity of Purpose**: Each module handles a clearly defined responsibility with no overlap.
    
- **Composability**: Each module should be independently testable and replaceable.
    
- **Extensibility**: Future features (e.g., vision processing, backlinking) should require minimal refactoring of the core pipeline.
    
- **Obsidian Compatibility**: All output must respect Obsidian’s file conventions and YAML frontmatter expectations.
    

## 2. Project Structure

The final application should adhere to the following file and directory structure:

```
/pkm_gardener/
|
├── main.py             # Minimal entry point to execute the pipeline.
├── orchestrator.py     # Contains the primary `run_pipeline` function.
├── config.py           # Configuration: API keys, paths, global constants.
├── requirements.txt    # Project dependencies.
|
├── core_modules/       # The main processing stages
│   ├── __init__.py
│   ├── ingestor.py
│   ├── text_processor.py
│   ├── vision_processor.py  # (For future expansion)
│   ├── indexer.py
│   └── router.py
|
└── utils/              # Shared helper utilities
    ├── __init__.py
    ├── llm.py
    ├── frontmatter.py
    └── filename.py

```

## 3. Core Data Structure

To ensure consistent data flow between modules, a central data object should be used. A Python `dataclass` is recommended for type safety.

**`ProcessingJob` Data Object:**

- `original_filepath`: (str) The absolute path to the file in the inbox.
    
- `original_filename`: (str) The original name of the file.
    
- `content`: (str or bytes) The raw content of the file.
    
- `file_type`: (str) e.g., 'text', 'image', 'pdf'.
    
- `metadata`: (dict) The YAML frontmatter, once generated.
    
- `suggested_filename`: (str) The new filename suggested by the LLM.
    
- `suggested_folder_path`: (str) The absolute destination path.
    
- `summary`: (str) A one-sentence summary of the note. (For `indexer`)
    
- `status`: (str) 'pending', 'success', 'failure', 'needs_review'.
    
- `error_message`: (str) Details of any error that occurred.
    

## 4. Module Implementation Guidelines

### 4.1. `main.py` and `orchestrator.py`

- **`main.py`**:
    
    - **Purpose**: To be the clean, executable entry point of the application.
        
    - **Implementation**: It should be minimal. Its only job is to import `run_pipeline` from `orchestrator.py` and execute it within an `if __name__ == "__main__":` block.
        
- **`orchestrator.py`**:
    
    - **Purpose**: To manage the overall workflow of the application.
        
    - **Core Responsibilities**:
        
        1. Initialize any necessary configurations from `config.py`.
            
        2. Call the `ingestor` to get a list of jobs to process.
            
        3. Loop through each `ProcessingJob`.
            
        4. Based on `job.file_type`, direct the job to the appropriate processor (`text_processor` or `vision_processor`).
            
        5. If processing is successful, pass the job to the `indexer`.
            
        6. Finally, pass the job to the `router` to move the file.
            
        7. Implement robust logging to track the status and outcome of each job.
            

### 4.2. Utility Modules (`/utils/`)

- **`llm.py`**:
    
    - **Purpose**: To abstract all direct interactions with the Gemini API.
        
    - **Core Responsibilities**:
        
        1. Contain a function, e.g., `get_suggestions(content, file_type)`, that takes file content and returns the structured output (metadata, filename, path, summary).
            
        2. The logic for constructing the detailed prompt and parsing the AI's response from the original script should be moved here.
            
        3. Handle API-related errors gracefully.
            
- **`frontmatter.py`**:
    
    - **Purpose**: To handle the creation and validation of YAML frontmatter.
        
    - **Core Responsibilities**:
        
        1. A function to construct the final, well-formatted YAML string from a dictionary.
            
        2. Logic for validating and normalizing the metadata dictionary (e.g., setting defaults, sorting tags).
            
- **`filename.py`**:
    
    - **Purpose**: To handle all filename-related logic.
        
    - **Core Responsibilities**:
        
        1. Contain the `sanitize_filename` function.
            
        2. Include logic to check for and resolve filename conflicts in the destination directory (e.g., by appending a number).
            

### 4.3. Core Modules (`/core_modules/`)

- **`ingestor.py`**:
    
    - **Purpose**: To scan the inbox and create processing jobs.
        
    - **Core Responsibilities**:
        
        1. A function, e.g., `find_new_files()`, that scans the `INBOX_PATH`.
            
        2. For each file found, it should determine the `file_type` and read its content.
            
        3. It should return a list of `ProcessingJob` objects, ready for the `orchestrator`.
            
- **`text_processor.py`**:
    
    - **Purpose**: To orchestrate the processing of text-based files.
        
    - **Core Responsibilities**:
        
        1. A main function, e.g., `process(job)`, that takes a `ProcessingJob` object.
            
        2. It calls `utils.llm.get_suggestions` with the job's content.
            
        3. It populates the `metadata`, `suggested_filename`, `suggested_folder_path`, and `summary` fields of the `ProcessingJob` object.
            
        4. It should return the updated `ProcessingJob` object.
            
- **`indexer.py`**:
    
    - **Purpose**: To maintain a central index of all processed notes.
        
    - **Core Responsibilities**:
        
        1. A function, e.g., `update_index(job)`, that takes a successfully processed `ProcessingJob`.
            
        2. It should open a master index file (e.g., `_index.md` or `index.csv`).
            
        3. It should append a new line to this file containing the key information from the job (e.g., new file path, priority, type, summary).
            
- **`router.py`**:
    
    - **Purpose**: To handle the final file system operations.
        
    - **Core Responsibilities**:
        
        1. A function, e.g., `file_note(job)`, that takes a fully processed `ProcessingJob`.
            
        2. It should prepend the final YAML frontmatter to the original file content.
            
        3. It should move the modified file from its original location in the inbox to the final destination path (`job.suggested_folder_path`), using the new filename (`job.suggested_filename`).
            
        4. It should handle the `DRY_RUN` configuration, logging actions without performing them.
            

## 5. Error Handling

The system should be resilient. The `orchestrator` should wrap its main processing loop in a `try...except` block. If any module fails while processing a job, the job's `status` should be updated to 'failure' with an `error_message`, and the file should be left in the inbox, perhaps with a `.failed` extension, for manual review.

## 6. Sample Flow Summary

This pseudo-code illustrates the high-level logic managed by the `orchestrator`.

```
main.py
  └── orchestrator.run_pipeline()
        ├── jobs = ingestor.find_new_files()
        ├── for job in jobs:
        │     ├── processor = select_processor_by_type(job.file_type)
        │     ├── processed_job = processor.process(job)
        │     ├── if processed_job.status == 'success':
        │     │     ├── indexer.update_index(processed_job)
        │     │     └── router.file_note(processed_job)
        │     └── else:
        │           └── log_error(processed_job)
        └── end_pipeline()
```