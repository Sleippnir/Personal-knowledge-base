import yaml

def construct_frontmatter_string(metadata: dict) -> str:
    """
    Constructs a well-formatted YAML frontmatter string from a dictionary.
    """
    # Ensure tags are a list and sorted for consistency
    if 'tags' in metadata and isinstance(metadata['tags'], list):
        metadata['tags'] = sorted(list(set(metadata['tags'])))

    yaml_string = yaml.dump(metadata, sort_keys=False, default_flow_style=False)
    return f"---\n{yaml_string}---\n"

def validate_and_normalize_metadata(metadata: dict) -> dict:
    """
    Validates and normalizes the metadata dictionary, setting defaults if necessary.
    """
    # Define default values
    defaults = {
        'status': 'triage',
        'priority': 'P3',
        'type': 'unknown',
        'tags': [],
        'source': '',
        'entities': [],
        'confidence_score': 0.0,
        'title': 'Untitled'
    }

    # Apply defaults
    for key, default_value in defaults.items():
        if key not in metadata or metadata[key] is None:
            metadata[key] = default_value

    # Ensure tags is a list
    if not isinstance(metadata.get('tags'), list):
        metadata['tags'] = []

    return metadata
