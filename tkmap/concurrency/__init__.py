import queue
import threading
import tkinter as tk
import uuid
from dataclasses import dataclass
from typing import Callable


@dataclass
class Task[T]:
    fn: Callable[..., T]
    task_id: uuid.UUID


@dataclass
class Result[T]:
    result: T | Exception
    task_id: uuid.UUID


class AsyncThreadWorker:
    def __init__(self, max_workers=4):
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

    def _worker_loop(self):
        while not self._shutdown.is_set():
            task: Task = self._input_queue.get()
            try:
                result = task.fn()
            except Exception as e:
                result = e
            self._result_queue.put(Result(result, task.task_id))
            self._input_queue.task_done()

    def submit(self, fn, callback) -> None:
        # Generate a unique ID for this task
        task_id = uuid.uuid4()
        self._callbacks[task_id] = callback
        self._input_queue.put(Task(fn, task_id))

    def process_queue(self):
        try:
            while True:
                result = self._result_queue.get_nowait()

                if result.task_id in self._callbacks:
                    self._callbacks.pop(result.task_id)(result.result)
        except queue.Empty:
            pass

    def start_processing(self, root: tk.Tk, interval_ms: int):
        if not self._processing_started:
            self._processing_started = True
            self._main_thread_callback = lambda cb, res: root.after(0, cb, res)
        self.process_queue()
        root.after(interval_ms, self.start_processing, root, interval_ms)

    def shutdown(self, wait=True):
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
