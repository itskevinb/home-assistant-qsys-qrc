import asyncio

import pytest

from custom_components.qsys_qrc.qsys.qrc import QRCError
from custom_components.qsys_qrc.sensor import run_engine_status_loop


class FakeSensor:
    def __init__(self):
        self.events = []

    def on_status(self, status):
        self.events.append(("status", status))

    def on_unavailable(self):
        self.events.append(("unavailable", None))


class FakeCore:
    def __init__(self, results):
        self._results = list(results)
        self.calls = 0

    async def status_get(self):
        self.calls += 1
        if self._results:
            r = self._results.pop(0)
            if isinstance(r, BaseException):
                raise r
            return r
        await asyncio.Event().wait()  # block forever after script


@pytest.mark.asyncio
async def test_engine_status_survives_qrc_error_then_recovers():
    ok1 = {"result": {"Status": {"Code": 0}}}
    ok2 = {"result": {"Status": {"Code": 0, "String": "OK"}}}
    disconnected = QRCError({"code": -1, "message": "disconnected"})
    core = FakeCore([ok1, disconnected, ConnectionResetError(), ok2])
    sensor = FakeSensor()

    task = asyncio.create_task(
        run_engine_status_loop(core, sensor, "core", interval=0, retry_delay=0)
    )
    for _ in range(50):
        await asyncio.sleep(0)
        if core.calls >= 5:
            break
    assert not task.done()  # loop survived the errors

    # unavailable reported once for the run of consecutive failures
    assert sensor.events == [
        ("status", ok1),
        ("unavailable", None),
        ("status", ok2),
    ]

    task.cancel()
    with pytest.raises(asyncio.CancelledError):
        await task
    assert sensor.events[-1] == ("unavailable", None)
