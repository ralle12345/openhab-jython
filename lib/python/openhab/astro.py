from openhab.globals import oh
from openhab.date import to_java_calendar
import datetime
import java.util

_astro = oh.getAction("Astro")

if _astro:

    _SunCalcClass = _astro.classLoader.loadClass(
        "org.openhab.binding.astro.internal.calc.SunCalc")
    
    _SunCalc = _SunCalcClass()
    
    def get_sun_info(lat, lon, timestamp=datetime.datetime.now()):
        return _SunCalc.getSunInfo(to_java_calendar(timestamp), lat, lon)



