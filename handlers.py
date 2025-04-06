import json

import aio_pika
import asyncio
from google import genai
from google.genai import types
from google.genai.types import Tool, GoogleSearch

from rabbitmq import message_buffer, message_event, next_seq
import rabbitmq

history_buffer = []

#client = genai.Client(api_key="")

async def history_to_prompt(history):
    lines = []
    for msg in history:
        user = msg["user"]
        content = msg["message"]
        prefix = user
        lines.append(f"{prefix}: {content}")
    return "\n".join(lines)

async def process(message, seq):
    msg_json = message.body.decode()
    msg = json.loads(msg_json)
    history_buffer.append({"user": msg["jid"], "message": msg["data"]})
    formatted_history = await history_to_prompt(history_buffer)

    google_search_tool = Tool(
        google_search=GoogleSearch()
    )

    response = client.models.generate_content(
        model='gemini-2.0-flash',
        contents=types.Part.from_text(text=formatted_history),
        config=types.GenerateContentConfig(
            tools=[google_search_tool],
            response_modalities=["TEXT"],
            temperature=0.9,
            top_p=0.95,
            presence_penalty=0.4,
            frequency_penalty=0.8,
            safety_settings=[
                types.SafetySetting(
                    category='HARM_CATEGORY_HATE_SPEECH',
                    threshold='BLOCK_MEDIUM_AND_ABOVE'
                ),
                types.SafetySetting(
                    category='HARM_CATEGORY_HARASSMENT',
                    threshold='BLOCK_MEDIUM_AND_ABOVE'
                ),
                types.SafetySetting(
                    category='HARM_CATEGORY_SEXUALLY_EXPLICIT',
                    threshold='BLOCK_ONLY_HIGH'
                ),
                types.SafetySetting(
                    category='HARM_CATEGORY_DANGEROUS_CONTENT',
                    threshold='BLOCK_ONLY_HIGH'
                ),
                types.SafetySetting(
                    category='HARM_CATEGORY_CIVIC_INTEGRITY',
                    threshold='BLOCK_ONLY_HIGH'
                )
            ]
        )
    )

    await message.ack()
    print("[X] Processing ", response.text)

    payload = {
        "jid": msg["jid"],
        "data": response.text,
    }

    history_buffer.append({"user": "ai", "message": response.text})

    await rabbitmq.add_buffer(seq, payload)

async def consumer():
    connection = await aio_pika.connect_robust("amqp://guest:guest@localhost:5672/")
    channel = await connection.channel()

    queue = await channel.declare_queue('raw_message', durable=True)

    async with queue.iterator() as queue_iter:
        seq = 0
        async for message in queue_iter:
            asyncio.create_task(process(message, seq))
            print("[X] Receiving ", message.body.decode())
            seq += 1

async def sender():
    global next_seq

    while True:
        await message_event.wait()

        while next_seq in message_buffer:
            result = message_buffer.pop(next_seq)
            print(result)
            await producer(result)
            next_seq += 1

        message_event.clear()
async def producer(msg):
    connection = await aio_pika.connect_robust("amqp://guest:guest@localhost:5672/")
    channel = await connection.channel()

    await channel.declare_queue('processed_message', durable=True)

    await channel.default_exchange.publish(
        aio_pika.Message(
            body=msg.encode()
        ),
        routing_key='processed_message'
    )

    await connection.close()
    print(" [x] Sent Processed Message")
