# my_worker.py
import os
import asyncio
from pyzeebe import ZeebeWorker, create_insecure_channel
import httpx

DELEGATE_URL = os.getenv("DELEGATE_URL", "http://localhost:8081/submodels/dXJuOmV4YW1wbGU6c206b3BzOjE/submodel-elements/hello/invoke")

async def call_delegate(pump_value: int) -> dict:
    async with httpx.AsyncClient(timeout=5.0) as client:
        # Send pumpValue in JSON to the delegated operation
        body_json = {
                    "inputArguments": [
                        { "value": 
                        {"modelType": "Property",
                        "value": f"{pump_value}", 
                        "valueType": "xs:string",
                        "idShort": "ExamplePropertyInput"
                        }}
                    ],
                    "inoutputArguments": [],
                    "outputArguments": []
                    }
        resp = await client.post(DELEGATE_URL, json=body_json)
        resp.raise_for_status()
        return resp.json()

async def main():
    # connect to Zeebe gateway
    channel = create_insecure_channel(hostname="localhost", port=26500)
    worker = ZeebeWorker(channel, name="python-worker")

    # job type must match your BPMN service task type
    @worker.task(task_type="python_task", timeout_ms=30000)
    async def python_task(pumpValue: int):
        print(f"received pumpValue with value={pumpValue}")
        result = await call_delegate(pumpValue)
        print(f"delegate responded: {result}")
        # returning a dict will be added as variables to the process instance (optional)
        return {"delegateResult": result}

    print("Worker started, waiting for jobs...")
    await worker.work()

if __name__ == "__main__":
    asyncio.run(main())
