"""Time formatting and helpers shared by the clock display.

Kept dependency-free (no external date libraries exist in MicroPython)
so it works the same on-device and in the CPython unit tests.
"""

WEEKDAYS = ("Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday")
MONTHS = (
    "January", "February", "March", "April", "May", "June",
    "July", "August", "September", "October", "November", "December",
)


def local_time(now_seconds, utc_offset_hours, time_module):
    """Return a UTC time tuple shifted by a fixed manual UTC offset.

    MicroPython has no timezone database - `time.localtime()` on every
    port except Unix is identical to `time.gmtime()` and always reflects
    UTC. We therefore start from `gmtime()` and apply the user's manual
    offset ourselves, which also keeps this deterministic when unit
    tested against CPython (whose `localtime()` would otherwise apply
    the *host machine's* timezone instead).

    `time_module` is passed in (rather than imported) so this can be unit
    tested against CPython's `time` module as well as MicroPython's.
    """
    return time_module.gmtime(now_seconds + int(utc_offset_hours * 3600))


def format_time(hour, minute, second, use_24_hour, show_seconds):
    if use_24_hour:
        display_hour = hour
        suffix = ""
    else:
        display_hour = hour % 12
        if display_hour == 0:
            display_hour = 12
        suffix = " AM" if hour < 12 else " PM"

    if show_seconds:
        return "{:02d}:{:02d}:{:02d}{}".format(display_hour, minute, second, suffix)
    return "{:02d}:{:02d}{}".format(display_hour, minute, suffix)


def format_date(year, month, day, weekday):
    return "{}, {} {}".format(WEEKDAYS[weekday], MONTHS[month - 1], day)


def is_night(hour, night_start_hour, night_end_hour):
    """Whether `hour` falls within a night window that may wrap past midnight."""
    if night_start_hour == night_end_hour:
        return False
    if night_start_hour < night_end_hour:
        return night_start_hour <= hour < night_end_hour
    return hour >= night_start_hour or hour < night_end_hour
