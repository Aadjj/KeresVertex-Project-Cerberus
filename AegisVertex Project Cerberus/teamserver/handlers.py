import asyncio
from logger import logger


async def handle_tcp_client(reader: asyncio.StreamReader, writer: asyncio.StreamWriter, plugins: list):
    addr = writer.get_extra_info('peername')
    logger.info(f"[*] New TCP connection from {addr}")

    try:
        while True:
            data = await reader.read(4096)
            if not data:
                logger.info(f"[-] Client {addr} initiated graceful close.")
                break

            try:
                message = data.decode('utf-8').strip()
                logger.debug(f"Raw data from {addr}: {message[:50]}...")

                response = await process_message(message, addr, plugins)

                if response:
                    writer.write(response.encode('utf-8'))
                    await writer.drain()

            except UnicodeDecodeError:
                logger.warning(f"[!] Received non-UTF8 data from {addr}.")
                await process_raw_bytes(data, addr, plugins)

    except asyncio.CancelledError:
        logger.warning(f"[!] Session with {addr} cancelled.")
    except Exception as e:
        logger.error(f"Error handling TCP client {addr}: {type(e).__name__}: {e}")
    finally:
        writer.close()
        try:
            await writer.wait_closed()
        except:
            pass
        logger.info(f"[*] Connection finalized for {addr}")


async def handle_udp_message(data: bytes, addr: tuple, transport: asyncio.DatagramTransport, plugins: list):
    try:
        message = data.decode('utf-8').strip()
        logger.info(f"[*] UDP Check-in from {addr}")

        response = await process_message(message, addr, plugins)
        if response and transport:
            transport.sendto(response.encode('utf-8'), addr)

    except Exception as e:
        logger.error(f"UDP Error from {addr}: {e}")


async def process_message(message: str, addr: tuple, plugins: list) -> str:
    response_payload = ""

    for plugin in plugins:
        try:
            result = await plugin.handle_event(message, addr)
            if result:
                response_payload += result
        except Exception as e:
            logger.error(f"Plugin failure during message processing: {e}")

    return response_payload if response_payload else "IDLE"


async def process_raw_bytes(data: bytes, addr: tuple, plugins: list):
    for plugin in plugins:
        if hasattr(plugin, 'handle_raw'):
            await plugin.handle_raw(data, addr)