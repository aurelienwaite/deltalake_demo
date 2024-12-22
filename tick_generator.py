# Test script that creates synthetic ticks to be aggregated

import json
import random
from datetime import datetime, timezone
import os
import time

symbols = ["a", "b", "c", "d", "e"]
num_files = 1000

for i in range(num_files):
    time.sleep(0.01)
    if random.randint(0,9) == 0:
        file_path = os.path.join("tick_data", f"tick_data_{i}.json")
        with open(file_path, "w") as f:
            num_ticks_per_file = random.randint(0, 10)
            for _ in range(num_ticks_per_file):
                tick = {
                    "symbol": random.choice(symbols),
                    "timestamp": datetime.now(tz=timezone.utc).isoformat(timespec="milliseconds"),
                    "price": round(random.uniform(100, 1500), 2)
                }
                f.write(json.dumps(tick) + "\n")
