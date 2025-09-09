# my_worker.py
import asyncio
from pyzeebe import ZeebeWorker, create_insecure_channel

async def main():
    # connect to Zeebe gateway
    channel = create_insecure_channel(hostname="localhost", port=26500)  # use "zeebe" if running inside Docker network
    worker = ZeebeWorker(channel, name="python-worker")

    # job type must match your BPMN service task type
    @worker.task(task_type="python_task", timeout_ms=30000)
    async def python_task(name: str):
        print(f"🛠️ received job with name={name}")
        return {"result": name}

    print("✅ Worker started, waiting for jobs...")
    await worker.work()

if __name__ == "__main__":
    asyncio.run(main())
