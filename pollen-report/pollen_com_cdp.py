#!/usr/bin/env python3
"""
pollen_com_cdp.py - Fetch species-level pollen data from pollen.com via Chrome CDP.
Extracts top allergens (Hickory, Willow, Oak, etc.) for Austin 78750 via Angular CDP.

Usage:
    python3 pollen_com_cdp.py
    # prints JSON to stdout on success, "null" on failure
"""

import asyncio
import websockets
import json
import subprocess
import sys
import time
import urllib.request

CHROME_PORT = 9223
CHROME_USER_DATA = "/tmp/pollen_com_chrome"


def start_chrome():
    subprocess.run(["pkill", "-f", CHROME_USER_DATA], stderr=subprocess.DEVNULL)
    time.sleep(1)
    subprocess.Popen(
        ["/snap/bin/chromium", "--headless=new", "--no-sandbox", "--disable-gpu",
         "--remote-debugging-port=" + str(CHROME_PORT),
         "--user-data-dir=" + CHROME_USER_DATA,
         "--incognito", "--noerrdialogs", "--no-first-run",
         "--ozone-platform=headless", "--ozone-override-screen-size=800,600"],
        stderr=subprocess.DEVNULL, stdout=subprocess.DEVNULL
    )
    time.sleep(3)


def get_page_id(port):
    """Get the first page target ID via HTTP JSON endpoint."""
    req = urllib.request.Request(
        f"http://localhost:{port}/json",
        headers={"User-Agent": "curl/7.68.0"}
    )
    with urllib.request.urlopen(req, timeout=5) as resp:
        targets = json.loads(resp.read())
    return targets[0]["id"] if targets else None


async def fetch_species():
    """
    Navigate to pollen.com for ZIP 78750, extract species-level data via Angular CDP.
    Returns dict or None on failure.
    """
    tab_id = get_page_id(CHROME_PORT)
    if not tab_id:
        return None

    page_ws_url = f"ws://localhost:{CHROME_PORT}/devtools/page/{tab_id}"
    async with websockets.connect(page_ws_url, max_size=10*1024*1024) as ws:
        cmd_id = [0]

        async def send(method, params):
            nonlocal ws
            cmd_id[0] += 1
            await ws.send(json.dumps({"id": cmd_id[0], "method": method, "params": params}))
            for _ in range(50):
                resp = await asyncio.wait_for(ws.recv(), timeout=5)
                data = json.loads(resp)
                if data.get("id") == cmd_id[0]:
                    return data

        await send("Page.navigate", {"url": "https://www.pollen.com/forecast/current/pollen/78750"})
        await asyncio.sleep(6)

        r = await send("Runtime.evaluate", {
            "expression": """
                (function() {
                    var el = document.querySelector('.forecast-day');
                    if (!el) return null;
                    var scope = angular && angular.element && angular.element(el).scope();
                    if (!scope) return null;
                    var days = scope.days || [];
                    var today = days.filter(function(d){ return d.Type==='Today'; })[0]
                             || days[1] || days[0];
                    if (!today) return null;
                    return JSON.stringify({
                        overall_index: today.Index,
                        overall_label: today.label,
                        top_allergens: (today.Triggers || []).map(function(t) {
                            return {name: t.Name, genus: t.Genus, plantType: t.PlantType};
                        }),
                        yesterday: {
                            index: days[0] ? days[0].Index : null,
                            label:  days[0] ? days[0].label : null,
                            names:  (days[0] && days[0].Triggers) ? days[0].Triggers.map(function(t){return t.Name;}) : []
                        },
                        tomorrow: {
                            index: days[2] ? days[2].Index : null,
                            label:  days[2] ? days[2].label : null,
                            names:  (days[2] && days[2].Triggers) ? days[2].Triggers.map(function(t){return t.Name;}) : []
                        }
                    });
                })()
            """
        })

        raw = r.get("result", {}).get("result", {}).get("value", "")
        if raw and raw not in ("null", "no forecast-day", "no scope", "no today"):
            return json.loads(raw)
        return None


async def main():
    start_chrome()
    try:
        data = await fetch_species()
        if data:
            print(json.dumps(data))
        else:
            print("null")
    finally:
        subprocess.run(["pkill", "-f", CHROME_USER_DATA], stderr=subprocess.DEVNULL)


if __name__ == "__main__":
    asyncio.run(main())
