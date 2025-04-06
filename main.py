import asyncio

import handlers

async def main():
    await asyncio.gather(
        handlers.consumer(),
        handlers.sender()
    )

if __name__ == '__main__':
    asyncio.run(main())
