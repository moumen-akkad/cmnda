# python_client.py
import asyncio
from pyzeebe import ZeebeClient, create_insecure_channel

# Adjust these to your setup
BPMN_PATH = r"diagram.bpmn"
PROCESS_ID = "python_process"  # must match <bpmn:process id="my_process" ...> inside the BPMN

async def main():
    # Create channel & client inside the same event loop
    channel = create_insecure_channel(hostname="localhost", port=26500)  # or "zeebe" if running inside Docker network
    client = ZeebeClient(channel)

    # 1) Deploy the model (do this before starting instances)
    await client.deploy_process(BPMN_PATH)
    print("Deployed:", BPMN_PATH)

    # 2) Start a process instance
    result = await client.run_process(PROCESS_ID)
    print("Started instance:", result)

    # 3) (Optional) Publish a message – only if your BPMN is waiting for it
    #    Ensure your model has a message catch event with name "messageName"
    await client.publish_message(name="messageName", correlation_key="correlationKey")
    print("Message published")

    # Cleanly close the channel
    await channel.close()

if __name__ == "__main__":
    asyncio.run(main())
