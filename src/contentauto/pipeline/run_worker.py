"""Worker launch entrypoint: `python -m contentauto.pipeline.run_worker`.

Uses arq's programmatic API with the lazily-built WorkerSettings so that
importing this module needs no env vars, but running main() resolves config.
"""
from __future__ import annotations


def main() -> None:
    from arq import run_worker

    from contentauto.pipeline.worker import build_worker_settings

    run_worker(build_worker_settings())


if __name__ == "__main__":
    main()
