# Prepare accrual_raw and usages_raw
from datetime import datetime

accrual_raw = [
    (datetime(2025, 1, 23).date(), '2025.03.09', 25111),
    (datetime(2025, 2, 5).date(), '2025.03.09', 5218),
    (datetime(2025, 2, 7).date(), '2025.03.09', 49987),
    (datetime(2025, 2, 8).date(), '2027.02.08', 11850),
    (datetime(2025, 2, 20).date(), '2027.02.08', 13545),
    (datetime(2025, 3, 20).date(), '2025.04.19', 59520),
    (datetime(2025, 3, 26).date(), '2025.04.25', 71083),
    (datetime(2025, 4, 3).date(), '2027.04.03', 2370),
    (datetime(2025, 4, 3).date(), '2027.04.03', 2370),
    (datetime(2025, 4, 3).date(), '2027.04.03', 7110),
    (datetime(2025, 4, 3).date(), '2025.05.03', 86062),
    (datetime(2025, 4, 4).date(), '2025.04.19', 59520),
    (datetime(2025, 4, 9).date(), '2025.05.09', 54962),
    (datetime(2025, 4, 16).date(), '2025.05.16', 5394)
]

usages_raw = [
    (datetime(2025, 2, 7).date(), -49987),
    (datetime(2025, 2, 25).date(), -75382),
    (datetime(2025, 3, 6).date(), -10000),
    (datetime(2025, 3, 6).date(), -5000),
    (datetime(2025, 3, 13).date(), -5000),
    (datetime(2025, 3, 20).date(), -89923),
    (datetime(2025, 4, 1).date(), -99807),
    (datetime(2025, 4, 3).date(), -59520),
    (datetime(2025, 4, 17).date(), -130603)
]

# Apply usages
for usage_date, usage_amount in usages_raw:
    usage_amount = -usage_amount  # convert to positive

    while usage_amount > 0 and accrual_raw:
        date, expire, amount = accrual_raw[0]

        if amount <= usage_amount:
            usage_amount -= amount
            accrual_raw.pop(0)
        else:
            accrual_raw[0] = (date, expire, amount - usage_amount)
            usage_amount = 0
