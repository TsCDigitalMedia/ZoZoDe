import anyio
import pytest
from anyio.abc import SocketAttribute

from zozode.config import UdpConfig
from zozode.udp import send_message_async, serve_async

pytestmark = pytest.mark.anyio


@pytest.fixture
def anyio_backend():
    return "asyncio"


async def test_send_message_async_reaches_anyio_udp_server():
    received = []
    server = await anyio.create_udp_socket(local_host="127.0.0.1", local_port=0)
    host, port = server.extra_attributes[SocketAttribute.local_address]()

    async with anyio.create_task_group() as task_group:
        task_group.start_soon(send_message_async, "hello async", UdpConfig(host=host, port=port))
        with anyio.fail_after(1):
            data, peer = await server.receive()
        received.append((data, peer))
        task_group.cancel_scope.cancel()

    await server.aclose()
    assert received[0][0] == b"hello async"


async def test_serve_async_receives_and_replies_with_anyio_udp():
    ready = anyio.Event()
    received = []

    def handler(data, peer):
        received.append((data, peer))
        return b"pong"

    async def run_server(port):
        ready.set()
        await serve_async(UdpConfig(host="127.0.0.1", port=port), handler)

    listener = await anyio.create_udp_socket(local_host="127.0.0.1", local_port=0)
    host, port = listener.extra_attributes[SocketAttribute.local_address]()
    await listener.aclose()

    async with anyio.create_task_group() as task_group:
        task_group.start_soon(run_server, port)
        await ready.wait()
        await anyio.sleep(0)
        client = await anyio.create_udp_socket(local_host="127.0.0.1")
        await client.sendto(b"ping", host, port)
        with anyio.fail_after(1):
            data, peer = await client.receive()
        await client.aclose()
        task_group.cancel_scope.cancel()

    assert data == b"pong"
    assert received[0][0] == b"ping"
