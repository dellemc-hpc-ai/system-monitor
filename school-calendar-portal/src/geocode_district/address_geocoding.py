import json, os, urllib.request, urllib.parse
from dataclasses import dataclass
CACHE_FILE = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), 'config', 'district_mapping_cache.json')
@dataclass
class GeoResult:
    lat: float; lon: float; display: str; city: str; state: str; county: str
def geocode(address):
    url = 'https://nominatim.openstreetmap.org/search?' + urllib.parse.urlencode({'q': address, 'format': 'json', 'limit': 1, 'countrycodes': 'us', 'addressdetails': 1})
    req = urllib.request.Request(url, headers={'User-Agent': 'CoParentingBot/1.0', 'Accept': 'application/json'})
    try:
        with urllib.request.urlopen(req, timeout=10) as resp:
            data = json.loads(resp.read().decode())
    except:
        return None
    if not data: return None
    addr = data[0].get('address', {})
    return GeoResult(lat=float(data[0]['lat']), lon=float(data[0]['lon']), display=data[0].get('display_name', ''), city=addr.get('city', addr.get('town', addr.get('village', ''))), state=addr.get('state', ''), county=addr.get('county', ''))
def load_cache():
    if os.path.exists(CACHE_FILE):
        with open(CACHE_FILE) as f: return json.load(f)
    return {'version': '1.0', 'mappings': {}}
def save_cache(cache):
    os.makedirs(os.path.dirname(CACHE_FILE), exist_ok=True)
    with open(CACHE_FILE, 'w') as f: json.dump(cache, f, indent=2)
def get_cached_district(address):
    return load_cache().get('mappings', {}).get(address, {}).get('district')
def cache_district(address, district, calendar_url=''):
    cache = load_cache()
    cache.setdefault('mappings', {})[address] = {'district': district, 'calendar_url': calendar_url}
    save_cache(cache)
