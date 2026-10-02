import time
import json
import traceback
from core.db import db
from core.jobs import claim_next_job, update_job
from graphs.orchestrator import run_task

def process_single_job(job: dict) -> None:
    job_id = job["id"]
    job_type = job["job_type"]
    payload = job.get("payload", {})
    
    print(f"[WORKER] Starting Job #{job_id} ({job_type})...")
    update_job(job_id, "running", 10, f"Executing {job_type}...")

    try:
        # Build initial state from payload
        state = {
            "task": job_type,
            "process_id": payload.get("process_id", 1),
            "engagement_id": payload.get("engagement_id", 1),
            "source_id": payload.get("source_id"),
            "user_id": job.get("created_by"),
            "test_request": payload.get("test_request", {}),
            "task_input": payload.get("task_input", "")
        }

        update_job(job_id, "running", 35, "Running AI agent graph nodes...")
        result = run_task(job_type, state)

        update_job(job_id, "running", 85, "Saving output deliverables...")
        update_job(job_id, "done", 100, f"Completed {job_type} successfully.")
        print(f"[WORKER] Successfully completed Job #{job_id}.")

    except Exception as e:
        err_msg = f"Job failed: {str(e)}"
        print(f"[WORKER] Error in Job #{job_id}: {err_msg}")
        traceback.print_exc()
        update_job(job_id, "failed", 0, err_msg)

def worker_loop(poll_interval: float = 2.0, max_iterations: int = 0) -> None:
    """
    Main worker loop. Continually polls database for queued jobs.
    If max_iterations > 0, stops after that many cycles (useful for testing).
    """
    print("[WORKER] FieldAI Background Worker started. Waiting for jobs...")
    db.init_db()
    
    cycles = 0
    while True:
        cycles += 1
        job = claim_next_job()
        if job:
            process_single_job(job)
        else:
            time.sleep(poll_interval)
            
        if max_iterations > 0 and cycles >= max_iterations:
            break

if __name__ == "__main__":
    worker_loop()
