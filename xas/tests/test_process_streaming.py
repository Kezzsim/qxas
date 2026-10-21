import unittest
from types import SimpleNamespace
from unittest.mock import Mock, patch

from xas.process import wait_for_tiled_run


class TestWaitForTiledRun(unittest.TestCase):
    def setUp(self):
        self.uid = "scan-uid"
        self.run = Mock()
        self.run.start = {"uid": self.uid}
        self.run.metadata = {"start": self.run.start}
        self.finished = SimpleNamespace(
            metadata={"start": self.run.start, "stop": {"run_start": self.uid}}
        )
        self.subscription = Mock()
        self.subscription.__enter__ = Mock(return_value=self.subscription)
        self.subscription.__exit__ = Mock(return_value=False)
        self.parent = self.run.parent
        self.parent.subscribe.return_value = self.subscription
        reader = patch("xas.process.from_context", return_value=self.run)
        self.read_run = reader.start()
        self.addCleanup(reader.stop)

    def emit(self, uid=None, metadata=None):
        callback = (
            self.subscription.child_metadata_updated.add_callback.call_args.args[0]
        )
        callback(SimpleNamespace(
            key=self.uid if uid is None else uid,
            metadata=self.finished.metadata if metadata is None else metadata,
        ))

    def test_historical_run_needs_no_subscription(self):
        self.run.metadata = self.finished.metadata
        self.assertIs(wait_for_tiled_run(self.run), self.run)
        self.parent.subscribe.assert_not_called()

    def test_processes_stop_notification_with_fresh_client(self):
        def read_run(*args, **kwargs):
            if self.read_run.call_count == 1:
                self.emit()
                return self.run
            return self.finished

        self.read_run.side_effect = read_run
        self.assertIs(wait_for_tiled_run(self.run, timeout=0), self.finished)
        self.subscription.__exit__.assert_called_once()
        self.run.refresh.assert_not_called()

    def test_stop_during_connection_is_not_missed(self):
        def connect():
            self.read_run.return_value = self.finished

        self.subscription.start_in_thread.side_effect = connect
        self.assertIs(wait_for_tiled_run(self.run, timeout=0), self.finished)
        self.subscription.__exit__.assert_called_once()

    def test_unrelated_updates_do_not_start_processing(self):
        def connect():
            self.emit(uid="another-scan")
            self.emit(metadata={"start": self.run.start})

        self.subscription.start_in_thread.side_effect = connect
        with self.assertRaisesRegex(TimeoutError, self.uid):
            wait_for_tiled_run(self.run, timeout=0)
        self.subscription.__exit__.assert_called_once()

    def test_read_failure_disconnects_subscription(self):
        self.read_run.side_effect = RuntimeError("read failed")
        with self.assertRaisesRegex(RuntimeError, "read failed"):
            wait_for_tiled_run(self.run, timeout=0)
        self.subscription.__exit__.assert_called_once()


if __name__ == "__main__":
    unittest.main()
