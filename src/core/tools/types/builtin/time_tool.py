"""
Time tool implementation

Provides time and timezone conversion functionality.
"""

import time
from datetime import datetime
from typing import Dict, Any
import pytz


def get_current_time(timezone: str = "UTC") -> Dict[str, Any]:
    """Get current time in a specific timezone
    
    Args:
        timezone: IANA timezone name (e.g., 'America/New_York', 'Europe/London'). 
            Defaults to 'UTC' if no timezone provided.
    
    Returns:
        Dict[str, Any]: Time information including timezone, datetime, and DST status
        
    Raises:
        ValueError: When timezone is invalid
    """
    try:
        # Load timezone location
        tz = pytz.timezone(timezone)
        
        # Get current time in the specified timezone
        current_time = datetime.now(tz)
        
        # Determine if DST is in effect
        dst_delta = current_time.dst()
        is_dst = dst_delta is not None and dst_delta.total_seconds() > 0
        
        return {
            "timezone": timezone,
            "datetime": current_time.isoformat(),
            "is_dst": is_dst,
            "formatted": current_time.strftime("%Y-%m-%d %H:%M:%S %Z")
        }
        
    except pytz.exceptions.UnknownTimeZoneError:
        raise ValueError(f"Invalid timezone: {timezone}")
    except Exception as e:
        raise ValueError(f"Failed to get current time: {str(e)}")


def convert_time(source_timezone: str, time_str: str, target_timezone: str) -> Dict[str, Any]:
    """Convert time between timezones
    
    Args:
        source_timezone: Source IANA timezone name (e.g., 'America/New_York', 'Europe/London')
        time_str: Time to convert in 24-hour format (HH:MM)
        target_timezone: Target IANA timezone name (e.g., 'Asia/Tokyo', 'America/San_Francisco')
    
    Returns:
        Dict[str, Any]: Conversion result with source and target time information
        
    Raises:
        ValueError: When timezone is invalid or time format is incorrect
    """
    try:
        # Validate time format
        if not time_str or ":" not in time_str:
            raise ValueError("Invalid time format: expected HH:MM [24-hour format]")
            
        time_parts = time_str.split(":")
        if len(time_parts) != 2:
            raise ValueError("Invalid time format: expected HH:MM [24-hour format]")
            
        hour = int(time_parts[0])
        minute = int(time_parts[1])
        
        if hour < 0 or hour > 23:
            raise ValueError("Invalid hour: expected 0-23")
        if minute < 0 or minute > 59:
            raise ValueError("Invalid minute: expected 0-59")
        
        # Load timezone locations
        source_tz = pytz.timezone(source_timezone)
        target_tz = pytz.timezone(target_timezone)
        
        # Create time in source timezone (using today's date)
        now = datetime.now()
        source_time = source_tz.localize(datetime(now.year, now.month, now.day, hour, minute))
        
        # Convert to target timezone
        target_time = source_time.astimezone(target_tz)
        
        # Calculate time difference in hours
        source_offset = source_time.utcoffset()
        target_offset = target_time.utcoffset()
        if source_offset is None or target_offset is None:
            raise ValueError("Unable to calculate timezone offset")
        time_diff = (target_offset.total_seconds() - source_offset.total_seconds()) / 3600

        # Determine DST status for both timezones
        source_dst_delta = source_time.dst()
        source_is_dst = source_dst_delta is not None and source_dst_delta.total_seconds() > 0
        target_dst_delta = target_time.dst()
        target_is_dst = target_dst_delta is not None and target_dst_delta.total_seconds() > 0
        
        # Format time difference string
        if time_diff == int(time_diff):
            time_diff_str = f"{time_diff:+.1f}h"
        else:
            time_diff_str = f"{time_diff:+.2f}h"
            # Remove trailing zeros
            time_diff_str = time_diff_str.rstrip('0').rstrip('.')
        
        return {
            "source": {
                "timezone": source_timezone,
                "datetime": source_time.isoformat(),
                "is_dst": source_is_dst,
                "formatted": source_time.strftime("%Y-%m-%d %H:%M:%S %Z")
            },
            "target": {
                "timezone": target_timezone,
                "datetime": target_time.isoformat(),
                "is_dst": target_is_dst,
                "formatted": target_time.strftime("%Y-%m-%d %H:%M:%S %Z")
            },
            "time_difference": time_diff_str,
            "conversion_note": f"Time converted from {source_timezone} to {target_timezone}"
        }
        
    except pytz.exceptions.UnknownTimeZoneError as e:
        raise ValueError(f"Invalid timezone: {str(e)}")
    except ValueError as e:
        raise e
    except Exception as e:
        raise ValueError(f"Time conversion failed: {str(e)}")


def list_timezones() -> Dict[str, Any]:
    """List all available timezones
    
    Returns:
        Dict[str, Any]: List of all available IANA timezones
    """
    all_timezones = pytz.all_timezones
    
    return {
        "timezones": all_timezones,
        "count": len(all_timezones),
        "common_timezones": [
            "UTC", "America/New_York", "America/Los_Angeles", 
            "Europe/London", "Europe/Paris", "Asia/Tokyo", 
            "Asia/Shanghai", "Australia/Sydney"
        ]
    }


# Example usage
if __name__ == "__main__":
    # Test get current time
    print("Testing get_current_time:")
    result = get_current_time("America/New_York")
    print(f"Current time in New York: {result['formatted']}")
    
    # Test time conversion
    print("\nTesting convert_time:")
    conversion = convert_time("America/New_York", "14:30", "Asia/Tokyo")
    print(f"14:30 in New York is {conversion['target']['formatted']} in Tokyo")
    print(f"Time difference: {conversion['time_difference']}")
    
    # Test list timezones
    print("\nTesting list_timezones:")
    tz_info = list_timezones()
    print(f"Total timezones available: {tz_info['count']}")
    print(f"Common timezones: {', '.join(tz_info['common_timezones'])}")