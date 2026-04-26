"""
Geocode a US address to lat/long using Nominatim (OpenStreetMap).
No API key required, but requires proper User-Agent and email.
"""
import sys
import urllib.request
import urllib.parse
import json

def geocode(address):
    """Convert address to lat/lon using Nominatim."""
    url = 'https://nominatim.openstreetmap.org/search?' + urllib.parse.urlencode({
        'q': address,
        'format': 'json',
        'limit': 1,
        'countrycodes': 'us',
        'addressdetails': 1
    })
    req = urllib.request.Request(url, headers={
        'User-Agent': 'CoParentingBot/1.0',
        'Accept': 'application/json'
    })
    with urllib.request.urlopen(req, timeout=10) as resp:
        data = json.loads(resp.read().decode())
    if not data:
        return None
    result = {
        'lat': float(data[0]['lat']),
        'lon': float(data[0]['lon']),
        'display': data[0].get('display_name', '')
    }
    addr = data[0].get('address', {})
    result['city'] = addr.get('city', addr.get('town', addr.get('village', '')))
    result['state'] = addr.get('state', '')
    result['county'] = addr.get('county', '')
    return result

if __name__ == '__main__':
    if len(sys.argv) > 1:
        address = ' '.join(sys.argv[1:])
    else:
        address = input("Enter address: ")

    print(f"Geocoding: {address}", flush=True)
    result = geocode(address)
    if result:
        print(f"OK lat={result['lat']:.6f} lon={result['lon']:.6f}")
        print(f"City: {result.get('city', 'N/A')}, State: {result.get('state', 'N/A')}")
        print(f"County: {result.get('county', 'N/A')}")
        print(f"Full: {result['display']}")
    else:
        print("ERROR: address not found")
