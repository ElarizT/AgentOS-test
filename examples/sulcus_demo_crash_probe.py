from kernel.process import AgentProcess


class SulcusDemoCrashProbe(AgentProcess):
    name = "SulcusDemoCrashProbe"
    capabilities = ("demo-crash-probe",)

    async def on_message(self, message) -> None:
        if message.type == "control" and message.payload.get("cmd") == "crash":
            raise RuntimeError("intentional Sulcus self-healing demo crash")
        if message.type == "task_request" and message.payload.get("cmd") == "health":
            self.reply(message, {"ok": True, "pid": self.pid, "status": "restarted"})
