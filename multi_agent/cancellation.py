"""Signal-based cancellation handling for CLI runs."""

from __future__ import annotations

import signal
import sys
from typing import Callable


class CancellationHandler:
    """Graceful cancellation on Ctrl+C."""

    def __init__(self, on_cancel: Callable[[], None]) -> None:
        """Store the cancel callback and initialize signal state."""
        self.on_cancel = on_cancel
        self.cancelled = False
        self._original_handler = None

    def __enter__(self):
        """Register the SIGINT handler and return the context."""
        self._original_handler = signal.signal(signal.SIGINT, self._handler)
        return self

    def __exit__(self, *args) -> None:
        """Restore the original SIGINT handler."""
        if self._original_handler is not None:
            signal.signal(signal.SIGINT, self._original_handler)

    def _handler(self, signum, frame) -> None:
        """Handle Ctrl+C with graceful cancel, then force quit on repeat."""
        if self.cancelled:
            print("\n\nForce quit (state not saved)")
            sys.exit(1)
        self.cancelled = True
        print("\n\nCancelling... (Press Ctrl+C again to force quit)")
        self.on_cancel()
