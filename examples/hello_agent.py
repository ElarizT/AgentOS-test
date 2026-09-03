from sulcus import AgentProcess


class HelloAgent(AgentProcess):
    name = "HelloAgent"

    async def on_start(self) -> None:
        self.remember({"message": "Hello from Sulcus"}, tags=["hello"])
