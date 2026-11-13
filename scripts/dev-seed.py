"""The Gaza example of `pixi run dev-up` (ponzi-core CR-093): a watch request for the Major TOM tiles over the Gaza
Strip, tag `gaza`, from 2023-10-07 with no last day, asked for by the dev user and approved by the dev admin, which
makes its area under the development standard `s1-dev`. Done once per PONZI home: a request tagged `gaza` already
there is approved if pending and otherwise left alone.

The tiles and the bursts need the server's boundaries and burst catalog, which a first start builds in the
background, so each step is tried again every 15 seconds (503 while they are being prepared), for up to an hour.

    python dev-seed.py URL ADMIN_KEY_FILE USER_KEY_FILE
"""

from __future__ import annotations

import sys
import time
from pathlib import Path

import httpx

#: The Gaza Strip's box, lon/lat.
GAZA = (34.20, 31.21, 34.57, 31.60)
TAG, START = "gaza", "2023-10-07"
WAIT, TRIES = 15, 240


def main(url: str, admin_file: str, user_file: str) -> int:
    """Seed the request, approve it; 0 when its area exists, 1 when it gave up."""
    admin = {"Authorization": f"Bearer {Path(admin_file).read_text().strip()}"}
    user = {"Authorization": f"Bearer {Path(user_file).read_text().strip()}"}
    with httpx.Client(base_url=f"{url}/v1", timeout=120) as http:
        for attempt in range(TRIES):
            try:
                mine = [w for w in http.get("/watch-requests", headers=admin).raise_for_status().json()
                        if TAG in [t.lower() for t in w["tags"]]]
                if any(w["status"] != "pending" for w in mine):
                    print(f"the {TAG} example is there: {mine[0]['status']}")
                    return 0
                if not mine:
                    cells = http.get("/majortom/cells", params={"bbox": ",".join(map(str, GAZA))},
                                     headers=user).raise_for_status().json()
                    body = {"cells": [c["cell_id"] for c in cells], "tags": [TAG], "start_date": START}
                    mine = [http.post("/watch-requests", json=body, headers=user).raise_for_status().json()]
                    print(f"asked for {len(body['cells'])} tiles over Gaza, tag {TAG}, from {START}")
                done = http.post(f"/watch-requests/{mine[0]['request_id']}/approve", headers=admin)
                if done.status_code == 200:
                    print(f"approved: area {done.json()['area_id']}")
                    return 0
                print(f"not approved yet ({done.status_code}): {done.json().get('detail')}")
            except httpx.HTTPStatusError as e:
                detail = e.response.json().get("detail") if e.response.content else ""
                print(f"waiting ({e.response.status_code}): {detail}")
            except httpx.HTTPError as e:
                print(f"waiting: {e}")
            sys.stdout.flush()
            time.sleep(WAIT)
    print("gave up: the server's boundaries or burst catalog never became ready", file=sys.stderr)
    return 1


if __name__ == "__main__":
    sys.exit(main(*sys.argv[1:]))
