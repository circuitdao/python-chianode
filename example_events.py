import asyncio
from chianode.mojoclient import MojoClient


async def main():
    
    NUM_EVENTS_TO_READ = 10 # Number of events to read. Set to 0 to read events indefinitely
    
    mojonode = MojoClient()
    
    stream = mojonode.events()
    stream_id = await anext(stream) # If you are running a Python version < 3.10, use stream.__anext__() instead
    print(f"CONNECTING TO STREAM ID {stream_id}")
    
    c = 0
    async for e in stream:
        print(e) # Print event data to console
        c += 1
        
        # Close stream once the specified number of events has been read
        if c == NUM_EVENTS_TO_READ:
            await mojonode.close_stream(stream_id)


if __name__ == "__main__":
    asyncio.run(main())
