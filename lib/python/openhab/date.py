"""
Date/time utilities for converting between the several different types
used by openHAB.
"""
import datetime
from org.joda.time import DateTime
from java.util import Calendar, Date
from java.text import SimpleDateFormat
from org.openhab.core.library.types import DateTimeType

date_formatter = SimpleDateFormat("yyyy-MM-dd'T'HH:mm:ss")

def to_python_datetime(value):
    if isinstance(value, Date):
        calendar = Calendar.getInstance()
        calendar.time = value
        value = calendar

    if isinstance(value, DateTimeType):
        value = value.calendar

    if isinstance(value, DateTime):
        value = value.toGregorianCalendar()

    if isinstance(value, Calendar):
        return datetime.datetime(
            value.get(Calendar.YEAR),
            value.get(Calendar.MONTH) + 1,
            value.get(Calendar.DAY_OF_MONTH),
            value.get(Calendar.HOUR_OF_DAY),
            value.get(Calendar.MINUTE),
            value.get(Calendar.SECOND),
            value.get(Calendar.MILLISECOND) * 1000,
        )

    raise Exception("Invalid conversion: " + value)


def to_java_calendar(value):
    if isinstance(value, datetime.datetime):
        c = Calendar.getInstance()
        c.set(Calendar.YEAR, value.year)
        c.set(Calendar.MONTH, value.month - 1)
        c.set(Calendar.DAY_OF_MONTH, value.day)
        c.set(Calendar.HOUR_OF_DAY, value.hour)
        c.set(Calendar.MINUTE, value.minute)
        c.set(Calendar.SECOND, value.second)
        c.set(Calendar.MILLISECOND, value.microsecond / 1000)
        return c

    raise Exception("Invalid conversion: " + value)


def to_joda_datetime(value):
    return DateTime(
        value.year, value.month, value.day, value.hour,
        value.minute, value.second, value.microsecond / 1000)
