def test_run_worker_imports_without_env():
    # Importing the entrypoint must not require env vars (build_worker_settings
    # is only called inside main(), never at import time).
    import contentauto.pipeline.run_worker as rw

    assert callable(rw.main)
