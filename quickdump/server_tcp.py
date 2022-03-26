import asyncio
from asyncio import StreamReader, StreamWriter
from datetime import datetime

from structlog.stdlib import get_logger

from quickdump import QuickDumper

qd = QuickDumper(label="tcp_dump")
logger = get_logger()


async def handle_echo(reader: StreamReader, writer: StreamWriter):
    peer_name = writer.get_extra_info("peername")
    logger.info(f"Got connection from {peer_name}")
    data = await reader.read()

    qd.dump((data, peer_name, datetime.now()))
    writer.close()
    logger.info(f"Dumped {len(data)} bytes from {peer_name}")


async def run_server():
    server = await asyncio.start_server(handle_echo, "0.0.0.0", 4411)
    addresses = ', '.join(str(sock.getsockname()) for sock in server.sockets)
    logger.info(f'Serving on {addresses}')
    async with server:
        await server.serve_forever()


def main():
    asyncio.run(run_server())


if __name__ == "__main__":
    main()
