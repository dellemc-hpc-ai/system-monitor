#!/usr/bin/env python3
"""
pollen_com_pw.py - Fetch species-level pollen data from pollen.com via Playwright.
Extracts top allergens (Hickory, Willow, Oak, etc.) for the given ZIP code.

Usage:
    python3 pollen_com_pw.py [zipcode]
    # prints JSON to stdout on success, "null" on failure
"""

import asyncio
import json
import sys
from playwright.async_api import async_playwright

ZIP = sys.argv[1] if len(sys.argv) > 1 else "78750"
POLLEN_URL = f"https://www.pollen.com/forecast/current/pollen/{ZIP}"
DEBUG = False


async def fetch_species():
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        page = await browser.new_page()

        errors = []
        page.on("pageerror", lambda e: errors.append(f"PAGE ERROR: {e}"))
        page.on("console", lambda m: errors.append(f"CONSOLE ERROR: {m.text}") if m.type == "error" else None)

        try:
            await page.goto(POLLEN_URL, wait_until="domcontentloaded", timeout=30000)
            await page.wait_for_timeout(5000)

            # Try Angular scope approach first (same data as CDP version)
            data = await page.evaluate("""
                () => {
                    try {
                        var el = document.querySelector('.forecast-day');
                        if (!el) return { method: 'css-selector', error: 'no forecast-day' };
                        var scope = window.angular && window.angular.element && window.angular.element(el).scope();
                        if (!scope) return { method: 'angular', error: 'no scope' };
                        var days = scope.days || [];
                        var today = days.filter(d => d.Type === 'Today')[0]
                                  || days[1] || days[0];
                        if (!today) return { method: 'angular', error: 'no today' };
                        return {
                            method: 'angular',
                            overall_index: today.Index,
                            overall_label: today.label,
                            top_allergens: (today.Triggers || []).map(t => ({
                                name: t.Name,
                                genus: t.Genus,
                                plantType: t.PlantType
                            })),
                            yesterday: {
                                index: days[0] ? days[0].Index : null,
                                label:  days[0] ? days[0].label : null,
                                names:  (days[0] && days[0].Triggers) ? days[0].Triggers.map(t => t.Name) : []
                            },
                            tomorrow: {
                                index: days[2] ? days[2].Index : null,
                                label:  days[2] ? days[2].label : null,
                                names:  (days[2] && days[2].Triggers) ? days[2].Triggers.map(t => t.Name) : []
                            }
                        };
                    } catch(e) { return { method: 'angular', error: e.message }; }
                }
            """)

            if DEBUG:
                print(f"Angular method result: {json.dumps(data, indent=2)}", file=sys.stderr)

            # If Angular approach failed, fall back to page text parsing
            if data.get("error") or not data.get("top_allergens"):
                if DEBUG:
                    print(f"Trying text parse fallback: {data.get('error')}", file=sys.stderr)
                text = await page.inner_text("body")
                top_allergens = []
                # Look for allergen patterns in text
                lines = text.split("\n")
                for line in lines:
                    line = line.strip()
                    for pt in ["Tree", "Grass", "Weed"]:
                        if pt + " -" in line or pt + ":" in line:
                            rest = line.split(pt)[-1].strip(" -:")
                            parts = rest.split()
                            if parts:
                                name = parts[0].strip("(),")
                                genus = parts[1].strip("(),") if len(parts) > 1 else ""
                                if name:
                                    top_allergens.append({
                                        "name": name,
                                        "genus": genus,
                                        "plantType": pt
                                    })
                if top_allergens:
                    data = {
                        "method": "text-fallback",
                        "top_allergens": top_allergens[:8],
                        "overall_index": None,
                        "overall_label": "See page"
                    }

            # If still no data, grab raw text snapshot for debugging
            if not data.get("top_allergens"):
                text = await page.inner_text("body")
                if DEBUG:
                    print("RAW PAGE TEXT:", file=sys.stderr)
                    print(text[:3000], file=sys.stderr)
                data = {
                    "method": "raw-text",
                    "error": "no allergens extracted",
                    "page_snippet": text[:2000]
                }

            return data

        finally:
            await browser.close()


async def main(zip_code):
    try:
        data = await fetch_species()
        if data and data.get("top_allergens"):
            print(json.dumps(data))
        elif data and not data.get("top_allergens"):
            # Partial data better than nothing
            print(json.dumps(data))
        else:
            print("null")
    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        print("null")


if __name__ == "__main__":
    asyncio.run(main(ZIP))
