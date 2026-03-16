memory_store = {}

async def save_preference(user_id: str, key: str, value: str):
    if user_id not in memory_store:
        memory_store[user_id] = {}

    memory_store[user_id][key] = value


async def get_preferences(user_id: str):
    return memory_store.get(user_id, {})