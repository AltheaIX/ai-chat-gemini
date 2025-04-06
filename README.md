# AI Chat Processor with RabbitMQ & Gemini
A concurrent message processing pipeline using RabbitMQ, Google Gemini AI, and asyncio. Supports short-term memory with history buffering and strict message order for output.

## Features
✅ RabbitMQ Communication
Message-based architecture using raw_message and processed_message queues.

✅ Short-Term Memory Buffer
Simple context-awareness using history buffer (non-persistent memory).

✅ Concurrent Processing
Uses asyncio.create_task() to process messages concurrently.

✅ Order-Based Response Sender
Ensures messages are sent in order using a buffer + next_seq tracking.

## Expected Input Format
Send a JSON message to the raw_message queue:
```
{
  "jid": "user_identifier",
  "message": "your message here"
}
```

## TODO
- [ ] Add retry mechanism for failed message handling.
- [ ] Add schema validation for incoming message format.
