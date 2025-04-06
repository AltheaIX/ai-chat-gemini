
import asyncio
import json

message_buffer = {}
message_event = asyncio.Event()
next_seq = 0

async def add_buffer(seq, payload):
    message_buffer[seq] = json.dumps(payload)
    message_event.set()