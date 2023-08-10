import asyncio
from chianode.mojoclient import MojoClient

async def main():

    NUM_EVENTS_TO_READ = 10
    
    mojonodemojo = MojoClient()
    
    stream = mojonodemojo.events()
    stream_id = await anext(stream)
    print(f"CONNECTING TO STREAM ID {stream_id}")
    
    c = 0
    async for e in stream:
        print(e)
        c += 1
        
        # Close stream after reading some events
        if c == NUM_EVENTS_TO_READ:
            await mojonodemojo.close_stream(stream_id)


if __name__ == "__main__":
    asyncio.run(main())
