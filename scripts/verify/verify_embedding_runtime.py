import sys
from pathlib import Path

ROOT = Path("/root/it-bidding-copilot")
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from api.routers import config_v2


if __name__ == "__main__":
    import asyncio

    result = asyncio.run(config_v2.test_connection())
    print(result)
