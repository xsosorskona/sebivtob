import time
import asyncio

joined = 0
messages = 0

async def update_stats():
    await client.wait_until_ready()
    global messages, joined
    client.loop.create_task(update_stats())

@client.event
async def on_message(message):
    global messages # ADD TO TOP OF THIS FUNCTION
    messages += 1 # ADD TO TOP OF THIS FUNCTION
    ...
@client.event
async def on_member_join(member):
    global joined # ADD TO TOP OF THIS FUNCTION
    joined += 1 # ADD TO TOP OF THIS FUNCTION