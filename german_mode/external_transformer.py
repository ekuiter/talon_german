from __future__ import annotations
import subprocess
import threading
from typing import List, Optional


class ExternalTransformer:
    """
    Wraps a long‑running external program that communicates via stdin/stdout.
    Lazily starts the process on first use and restarts it if it dies.
    """

    def __init__(self, cmd: List[str]) -> None:
        self.cmd: List[str] = cmd
        self.process: Optional[subprocess.Popen[str]] = None
        self.lock = threading.Lock()

    def _start_process(self) -> None:
        """
        Start the external program if it isn't running, or restart it if it died.
        """
        # Case 1: No process has been started yet
        if self.process is None:
            self._launch_new_process()
            return

        # Case 2: Process exists but has terminated
        if self.process.poll() is not None:
            # Clean up the old process object
            self.process = None
            self._launch_new_process()

    def _launch_new_process(self) -> None:
        """Launch a fresh instance of the external program."""
        self.process = subprocess.Popen(
            self.cmd,
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            bufsize=1,
        )
        # Verify the process started and its I/O streams are available.
        # If the process terminated immediately, notify and clear the reference.

        if self.process.poll() is not None:
            returncode = self.process.poll()
            print(f"Failed to start process {self.cmd!r}; terminated immediately (returncode={returncode})")

            # clear so future calls will try to relaunch
            self.process = None
            return

        # Check stdin/stdout availability
        if self.process.stdin is None or self.process.stdout is None:
            print(f"Process started (pid={getattr(self.process, 'pid', None)}) but I/O streams are not available.")
        else:
            print(f"Started external process {self.cmd!r} (pid={self.process.pid})")

    def transform(self, text: str) -> str:
        """
        Send text to the external program and return its output.
        """
        with self.lock:
            self._start_process()
            assert self.process is not None

            if self.process.stdin is None or self.process.stdout is None:
                raise RuntimeError("Process I/O streams are not available.")

            self.process.stdin.write(text + "\n")
            self.process.stdin.flush()

            response: str = self.process.stdout.readline().rstrip("\n")
            return response

    def close(self) -> None:
        """Terminate the external process cleanly."""
        if self.process is not None:
            self.process.terminate()
            self.process = None

    def __del__(self) -> None:
        self.close()

