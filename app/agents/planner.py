async def plan_task(user_input: str):
    """
    Converts user request into a task plan.
    (Later powered by LLM reasoning)
    """

    if "haircut" in user_input.lower():
        return [
            "check_calendar",
            "search_salons",
            "call_salon",
            "confirm_booking",
            "add_to_calendar",
        ]

    return ["unknown_task"]