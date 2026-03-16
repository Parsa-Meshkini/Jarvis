async def execute_plan(plan: list):
    results = []

    for step in plan:
        results.append(f"Executed: {step}")

    return results