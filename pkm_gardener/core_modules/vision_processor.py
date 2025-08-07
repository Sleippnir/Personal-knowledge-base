from pkm_gardener.orchestrator import ProcessingJob

def process(job: ProcessingJob) -> ProcessingJob:
    """
    Placeholder for processing vision-based files.
    """
    job.status = "failure"
    job.error_message = "Vision processing is not yet implemented."
    return job
