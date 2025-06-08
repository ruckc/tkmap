"""Concurrency utilities for tkmap: async thread worker and task/result dataclasses."""

import queue
import threading
import tkinter as tk
import uuid
from collections.abc import Callable
from dataclasses import dataclass


@dataclass
class Task[T]:
    """A task to be executed asynchronously, with a function and unique ID."""

    fn: Callable[..., T]
    task_id: uuid.UUID


@dataclass
class Result[T]:
    """Result of an asynchronous task.

    Contains the result or exception and the task ID.
    """

    result: T | Exception
    task_id: uuid.UUID


class AsyncThreadWorker:
    """A simple thread pool for running background tasks.

    Posts results to the main thread for callback processing.
    """

    def __init__(self, max_workers: int = 4) -> None:
        """Initialize the thread worker pool.

        Args:
            max_workers: Number of worker threads to start.

        """
        self._input_queue = queue.Queue()
        self._result_queue = queue.Queue()
        self._processing_started = False
        self._main_thread_callback = None
        self._callbacks = {}
        self._threads = []
        self._shutdown = threading.Event()
        for _ in range(max_workers):
            t = threading.Thread(target=self._worker_loop, daemon=True)
            t.start()
            self._threads.append(t)

    def _worker_loop(self) -> None:
        """Worker thread loop: fetches and executes tasks from the input queue."""
        while not self._shutdown.is_set():
            task: Task = self._input_queue.get()
            try:
                result = task.fn()
            except Exception as e:  # noqa: BLE001 - we want to catch all exceptions here, so it doesn't kill the thread
                result = e
            self._result_queue.put(Result(result, task.task_id))
            self._input_queue.task_done()

    def submit(self, fn: Callable, callback: Callable) -> None:
        """Submit a function to be executed in the background.

        The callback will be called with the result.
        """
        # Generate a unique ID for this task
        task_id = uuid.uuid4()
        self._callbacks[task_id] = callback
        self._input_queue.put(Task(fn, task_id))

    def process_queue(self) -> None:
        """Process completed results and invoke their callbacks."""
        try:
            while True:
                result = self._result_queue.get_nowait()

                if result.task_id in self._callbacks:
                    self._callbacks.pop(result.task_id)(result.result)
        except queue.Empty:
            pass

    def start_processing(self, root: tk.Tk | tk.Toplevel, interval_ms: int) -> None:
        """Start polling for results and posting them to the main thread.

        Args:
            root: The Tkinter root or toplevel window.
            interval_ms: Polling interval in milliseconds.

        """
        if not self._processing_started:
            self._processing_started = True
            self._main_thread_callback = lambda cb, res: root.after(0, cb, res)
        self.process_queue()
        root.after(interval_ms, self.start_processing, root, interval_ms)

    def shutdown(self, wait: bool = True) -> None:  # noqa: FBT001, FBT002 - wait can only be bool
        """Shut down the worker pool and clean up resources.

        Args:
            wait: Whether to wait for all threads to finish.

        """
        self._processing_started = False
        self._shutdown.set()
        # Drain the input queue to prevent new tasks from being submitted
        try:
            while True:
                self._input_queue.get_nowait()
        except queue.Empty:
            pass
        if wait:
            for t in self._threads:
                t.join()
        self._main_thread_callback = None
        self._callbacks.clear()
