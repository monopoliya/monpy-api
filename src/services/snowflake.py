import time
import threading


class Snowflake:
    # snowflake-like ID generator
    # (epoch set to Jan 1, 2025 UTC)

    _sequence = 0
    _epoch = 1735689600000  # milliseconds since epoch

    _last_timestamp = -1
    _lock = threading.Lock()

    @classmethod
    def _timestamp(cls) -> int:
        return int(time.time() * 1000)

    @classmethod
    def generate(cls) -> int:
        with cls._lock:
            timestamp = cls._timestamp()
            if timestamp == cls._last_timestamp:
                cls._sequence = (cls._sequence + 1) & 0xFFF  # 12 bits sequence
                if cls._sequence == 0:
                    # wait next ms
                    while timestamp <= cls._last_timestamp:
                        timestamp = cls._timestamp()
            else:
                cls._sequence = 0

            cls._last_timestamp = timestamp
            # construct 64-bit id: 41 bits timestamp, 12 bits sequence
            snowflake = ((timestamp - cls._epoch) << 12) | cls._sequence
            return snowflake
