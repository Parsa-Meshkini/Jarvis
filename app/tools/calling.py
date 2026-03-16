async def call_business(params: dict = {}) -> dict:
    name = params.get("name", "the business")
    return {
        "status": "success",
        "message": f"Calling {name}..."
    }