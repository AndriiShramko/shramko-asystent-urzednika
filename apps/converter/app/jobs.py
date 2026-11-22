"""Jobs: a conversion that is taken at once, waits its turn in a bounded queue and tells where it is (wave 11, FLOW).

    POST   /v1/jobs              the file -> 202 {id, state: "queued", position, ...}; 429 QUEUE_FULL when no room
    GET    /v1/jobs/{id}         {state, position, stage{name, step, page, pages}, units{done, total}, ...}
    GET    /v1/jobs/{id}/result  the answer of /v1/forms/convert for the same file (200), or the job's problem
    DELETE /v1/jobs/{id}         a waiting job leaves the queue; a running one is given up (its thread ends alone)

Why this shape: one request per file that answers only at the end cannot tell how far it is, and twenty of them at
once were refused with 429 BUSY. A status address polled by the page is the smallest honest design: no new
dependency, no stream to keep open through a proxy, and a script uses it with two plain calls.

The work itself is unchanged: `run_one` of the shell (guard, then `pipeline.run_limited`), under the SAME slots as
the synchronous endpoints (`gate`), so never more than CONCURRENCY conversions run, whatever the number of files.
Waiting jobs hold only their bytes; their number and their bytes are bounded (`QueueLimits`). Finished jobs keep
their result (JSON, small) for `KEEP_S` seconds, the newest `KEEP_MAX` of them.

Nothing here is written to disk and nothing of a file reaches a log: a job is its random id, its size and its state.
"""
from __future__ import annotations

import asyncio
import time
import uuid
from dataclasses import dataclass, field
from typing import Any, Awaitable, Callable

from app import progress
from app.guard import ProblemError

KEEP_S = 1800          # a finished job answers for this long
KEEP_MAX = 60          # and at most this many finished jobs are kept
ID_LENGTH = 32

QUEUED, RUNNING, DONE, ERROR, CANCELLED = "queued", "running", "done", "error", "cancelled"


@dataclass(frozen=True)
class QueueLimits:
    """How much may wait. Decided from the measured run on 2 CPU and 2 GB (report FLOW, wave 11): twenty files of
    the task sets wait as about 30 MB of bytes; the cap of bytes is five single-file limits, as for a batch."""

    waiting: int = 20
    waiting_bytes: int = 5 * 20971520

    @classmethod
    def of(cls, settings: Any) -> "QueueLimits":
        return cls(waiting=20, waiting_bytes=5 * int(getattr(settings, "max_upload_bytes", 20971520)))


@dataclass
class Job:
    id: str
    name: str | None
    declared: str | None
    data: bytes | None
    size: int
    tracker: progress.Tracker
    state: str = QUEUED
    created: float = field(default_factory=time.monotonic)
    started: float | None = None
    finished: float | None = None
    outcome: Any = None                 # what `run_one` returned
    error: ProblemError | None = None
    task: asyncio.Task | None = None


class JobQueue:
    """The jobs of one running service. Every method runs on the event loop; only `work` runs in a thread."""

    def __init__(self, gate: asyncio.Semaphore, limits: QueueLimits, work: Callable[[Job], Awaitable[Any]],
                 model: Callable[[], bool] = lambda: False) -> None:
        self._gate = gate
        self.limits = limits
        self._work = work
        self._model = model
        self._jobs: dict[str, Job] = {}

    # ---- counting ---------------------------------------------------------------------------------------------

    def _waiting(self) -> list[Job]:
        return [j for j in self._jobs.values() if j.state == QUEUED]   # dicts keep the order of arrival

    def counts(self) -> dict[str, int]:
        waiting = self._waiting()
        return {"running": sum(1 for j in self._jobs.values() if j.state == RUNNING), "waiting": len(waiting),
                "waiting_max": self.limits.waiting}

    def _sweep(self) -> None:
        now = time.monotonic()
        ended = [j for j in self._jobs.values() if j.state in (DONE, ERROR, CANCELLED)]
        gone = {j.id for j in ended if j.finished is not None and now - j.finished > KEEP_S}
        kept = [j for j in ended if j.id not in gone]
        gone |= {j.id for j in kept[: max(0, len(kept) - KEEP_MAX)]}
        for jid in gone:
            del self._jobs[jid]

    # ---- the four calls ---------------------------------------------------------------------------------------

    def submit(self, name: str | None, data: bytes, declared: str | None) -> Job:
        self._sweep()
        waiting = self._waiting()
        if len(waiting) >= self.limits.waiting or sum(j.size for j in waiting) + len(data) > self.limits.waiting_bytes:
            raise ProblemError("QUEUE_FULL", f"W kolejce czeka już {len(waiting)} plików; limit to {self.limits.waiting} "
                               "plików. Ten plik nie został przyjęty: wyślij go ponownie za chwilę.",
                               limits={"waiting_max": self.limits.waiting, "waiting_bytes_max": self.limits.waiting_bytes},
                               headers={"Retry-After": "10"})
        job = Job(id=uuid.uuid4().hex[:ID_LENGTH], name=name, declared=declared, data=data, size=len(data),
                  tracker=progress.Tracker(model=bool(self._model())))
        self._jobs[job.id] = job
        job.task = asyncio.get_running_loop().create_task(self._run(job))
        return job

    def get(self, job_id: str) -> Job:
        job = self._jobs.get(job_id) if len(job_id) == ID_LENGTH else None
        if job is None or job.state == CANCELLED:
            raise ProblemError("NOT_FOUND", "Nie ma takiego zadania: nie istnieje, zostało przerwane albo jego wynik już wygasł.")
        return job

    def cancel(self, job_id: str) -> Job:
        job = self.get(job_id)
        if job.state in (QUEUED, RUNNING):
            # A waiting job never starts. A running one cannot be stopped (a thread is not killed): it ends by
            # itself within the time limit and its result is dropped.
            job.state, job.finished, job.data = CANCELLED, time.monotonic(), None
        return job

    async def _run(self, job: Job) -> None:
        async with self._gate:   # first come, first served; the synchronous endpoints share these slots
            if job.state != QUEUED:
                return
            job.state, job.started = RUNNING, time.monotonic()
            token = progress.bind(job.tracker)
            try:
                outcome = await self._work(job)
            except ProblemError as exc:
                error: ProblemError | None = exc
                outcome = None
            except Exception:  # noqa: BLE001 - one job must never take the queue down; no text of the exception
                error, outcome = ProblemError("GATE_FAILED", "Błąd wewnętrzny usługi."), None
            else:
                error = None
            finally:
                progress.unbind(token)
            job.data = None   # the bytes are not needed any more, whatever the end
            if job.state != RUNNING:   # given up while it ran
                return
            job.finished = time.monotonic()
            if error is None:
                job.tracker.finish()
                job.outcome, job.state = outcome, DONE
            else:
                job.error, job.state = error, ERROR

    # ---- what a caller is told --------------------------------------------------------------------------------

    def status(self, job: Job) -> dict[str, Any]:
        now = time.monotonic()
        out: dict[str, Any] = {"id": job.id, "state": job.state, "size_bytes": job.size, "queue": self.counts()}
        if job.state == QUEUED:
            waiting = self._waiting()
            out["position"] = next(i for i, j in enumerate(waiting, 1) if j.id == job.id)   # 1 = the next to start
            out["waited_s"] = round(now - job.created, 1)
            out["units"] = {"done": 0, "total": progress.TOTAL}
            return out
        out["waited_s"] = round((job.started or job.created) - job.created, 1)
        out["elapsed_s"] = round((job.finished or now) - (job.started or job.created), 1)
        out.update({k: v for k, v in job.tracker.snapshot().items() if k != "reports"})
        if job.state == ERROR and job.error is not None:
            out["error"] = job.error.body()
        return out
