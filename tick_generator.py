# Test script that creates synthetic ticks to be aggregated

import json
import random
import datetime
import os
import time

symbols = ["a", "b", "c", "d", "e"]
num_files = 1000

for i in range(num_files):
    time.sleep(1)
    file_path = os.path.join("tick_data", f"tick_data_{i}.json")
    with open(file_path, "w") as f:
        num_ticks_per_file = random.randint(0, 100)
        for _ in range(num_ticks_per_file):
            tick = {
                "symbol": random.choice(symbols),
                "timestamp": (datetime.datetime.now() - datetime.timedelta(milliseconds=random.randint(0, 1000))).isoformat(),
                "price": round(random.uniform(100, 1500), 2)
            }
            f.write(json.dumps(tick) + "\n")