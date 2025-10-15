from datetime import datetime, timedelta


def add_minutes_to_time_string(time_str: str, minutes: int) -> str:
    """
    Add minutes to a time string and return the result as a time string.
    
    Args:
        time_str: Time in HH:MM format
        minutes: Number of minutes to add
        
    Returns:
        Time string in HH:MM format
    """
    # Parse the time string
    time_obj = datetime.strptime(time_str, "%H:%M")
    
    # Add the minutes
    new_time = time_obj + timedelta(minutes=minutes)
    
    # Return as time string
    return new_time.strftime("%H:%M")
