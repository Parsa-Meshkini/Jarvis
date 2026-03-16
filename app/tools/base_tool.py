from abc import ABC, abstractmethod


class BaseTool(ABC):
    name: str
    description: str

    @abstractmethod
    async def run(self, params: dict) -> dict:
        ...

    def require(self, params: dict, *keys: str) -> None:
        missing = [k for k in keys if k not in params or params[k] is None]
        if missing:
            raise ValueError(f"[{self.name}] Missing required params: {missing}")