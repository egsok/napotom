"""Tests for queue slot release on cancellation (no real downloads)."""

import pytest

from core.queue import DownloadQueue, QueueItem, QueueItemStatus


class FakeWorker:
    def __init__(self):
        self.cancel_called = False

    def cancel(self):
        self.cancel_called = True


@pytest.fixture
def queue(qapp):
    return DownloadQueue()


def test_on_cancelled_frees_slot(queue, monkeypatch):
    # A cancelled worker must release its _active_workers slot, otherwise
    # two cancellations permanently stall the queue
    monkeypatch.setattr(queue, "_process_next", lambda: None)
    queue._active_workers["w1"] = FakeWorker()
    queue._on_cancelled("w1")
    assert "w1" not in queue._active_workers


def test_on_cancelled_starts_next_pending(queue, monkeypatch):
    pending = QueueItem(url="http://example.com/a", quality="best", output_path=".")
    queue.items = [pending]
    queue._active_workers["gone"] = FakeWorker()

    started = []
    monkeypatch.setattr(queue, "_start_download", lambda item: started.append(item))

    queue._on_cancelled("gone")
    assert started == [pending]


def test_cancel_all_marks_all_nonterminal_cancelled(queue):
    pending = QueueItem(url="http://example.com/a", status=QueueItemStatus.PENDING)
    active = QueueItem(url="http://example.com/b", status=QueueItemStatus.DOWNLOADING)
    done = QueueItem(url="http://example.com/c", status=QueueItemStatus.COMPLETED)
    queue.items = [pending, active, done]
    worker = FakeWorker()
    queue._active_workers[active.id] = worker

    queue.cancel_all()

    assert pending.status == QueueItemStatus.CANCELLED
    assert active.status == QueueItemStatus.CANCELLED
    assert done.status == QueueItemStatus.COMPLETED
    assert worker.cancel_called
    assert queue._shutting_down


def test_no_new_downloads_during_shutdown(queue, monkeypatch):
    # Cancelling active workers at shutdown must not kick off queued items
    pending = QueueItem(url="http://example.com/a", status=QueueItemStatus.PENDING)
    queue.items = [pending]

    started = []
    monkeypatch.setattr(queue, "_start_download", lambda item: started.append(item))

    queue._shutting_down = True
    queue._on_cancelled("whatever")
    assert started == []
