import asyncio

from websockets.asyncio.server import serve

from server.server_ import Server


async def main():
    server = Server()
    async with serve(server.ws_handler, "localhost", 8080):
        await asyncio.Future()  # run forever


if __name__ == "__main__":
    asyncio.run(main())
