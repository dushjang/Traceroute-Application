import sys
import os
import re
import json
import time
import math
import platform
import subprocess
import ipaddress
import requests
from typing import Optional, List, Dict, Any, Generator

from fastapi import FastAPI, Query, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, HTMLResponse, StreamingResponse

app = FastAPI(title="Visual Traceroute API", version="2.2")

# Enable CORS for frontend communication
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# In-memory cache for geolocation to speed up lookups and eliminate rate limits
geo_cache: Dict[str, Dict[str, Any]] = {}
origin_cache: Optional[Dict[str, Any]] = None

HTML_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "index.html")

def is_public_ip(ip_str: str) -> bool:
    """Validate whether an IP address is a routable public IPv4/IPv6 address."""
    if not ip_str:
        return False
    try:
        ip = ipaddress.ip_address(ip_str.strip())
        return not (
            ip.is_private
            or ip.is_loopback
            or ip.is_reserved
            or ip.is_link_local
            or ip.is_multicast
            or ip.is_unspecified
        )
    except ValueError:
        return False

def compute_satellite_tile_url(lat: float, lon: float, zoom: int = 13) -> str:
    """Generate high-detail Google Maps Satellite Hybrid tile URL (Satellite + Roads + Labels)."""
    try:
        x = int((lon + 180.0) / 360.0 * (1 << zoom))
        lat_rad = math.radians(lat)
        y = int((1.0 - math.asinh(math.tan(lat_rad)) / math.pi) / 2.0 * (1 << zoom))
        return f"https://mt1.google.com/vt/lyrs=y&x={x}&y={y}&z={zoom}"
    except Exception:
        return ""

def get_geolocation(ip: str) -> Optional[Dict[str, Any]]:
    """Lookup geolocation for a public IP using multi-provider free endpoints (No API Key Required)."""
    if not ip or not is_public_ip(ip):
        return None

    if ip in geo_cache:
        return geo_cache[ip]

    geo = None

    # Tier 1: ip-api.com
    try:
        url = f"http://ip-api.com/json/{ip}?fields=status,message,country,countryCode,regionName,city,lat,lon,isp,org,as,query"
        response = requests.get(url, timeout=3.0)
        if response.status_code == 200:
            data = response.json()
            if data.get("status") == "success":
                lat = float(data.get("lat"))
                lon = float(data.get("lon"))
                geo = {
                    "ip": ip,
                    "lat": lat,
                    "lon": lon,
                    "city": data.get("city") or "Unknown City",
                    "region": data.get("regionName") or "",
                    "country": data.get("country") or "Unknown Country",
                    "countryCode": data.get("countryCode") or "",
                    "isp": data.get("isp") or "",
                    "org": data.get("org") or data.get("as") or "",
                    "satellite_image": compute_satellite_tile_url(lat, lon, 13),
                    "google_maps_url": f"https://www.google.com/maps/search/?api=1&query={lat},{lon}",
                    "provider": "ip-api"
                }
    except Exception:
        pass

    # Tier 2 Fallback: ipwho.is
    if not geo:
        try:
            url = f"https://ipwho.is/{ip}"
            response = requests.get(url, timeout=3.0)
            if response.status_code == 200:
                data = response.json()
                if data.get("success"):
                    lat = float(data.get("latitude"))
                    lon = float(data.get("longitude"))
                    conn = data.get("connection") or {}
                    geo = {
                        "ip": ip,
                        "lat": lat,
                        "lon": lon,
                        "city": data.get("city") or "Unknown City",
                        "region": data.get("region") or "",
                        "country": data.get("country") or "Unknown Country",
                        "countryCode": data.get("country_code") or "",
                        "isp": conn.get("isp") or "",
                        "org": conn.get("org") or "",
                        "satellite_image": compute_satellite_tile_url(lat, lon, 13),
                        "google_maps_url": f"https://www.google.com/maps/search/?api=1&query={lat},{lon}",
                        "provider": "ipwhois"
                    }
        except Exception:
            pass

    # Tier 3 Fallback: freeipapi.com
    if not geo:
        try:
            url = f"https://freeipapi.com/api/json/{ip}"
            response = requests.get(url, timeout=3.0)
            if response.status_code == 200:
                data = response.json()
                lat = float(data.get("latitude"))
                lon = float(data.get("longitude"))
                geo = {
                    "ip": ip,
                    "lat": lat,
                    "lon": lon,
                    "city": data.get("cityName") or "Unknown City",
                    "region": data.get("regionName") or "",
                    "country": data.get("countryName") or "Unknown Country",
                    "countryCode": data.get("countryCode") or "",
                    "isp": "",
                    "org": "",
                    "satellite_image": compute_satellite_tile_url(lat, lon, 13),
                    "google_maps_url": f"https://www.google.com/maps/search/?api=1&query={lat},{lon}",
                    "provider": "freeipapi"
                }
        except Exception:
            pass

    if geo:
        geo_cache[ip] = geo
        return geo
    return None

def get_origin_geolocation() -> Optional[Dict[str, Any]]:
    """Fetch the public geolocation of the current client / machine (Hop 0)."""
    global origin_cache
    if origin_cache:
        return origin_cache

    try:
        url = "http://ip-api.com/json/?fields=status,message,country,countryCode,regionName,city,lat,lon,isp,org,as,query"
        response = requests.get(url, timeout=4.0)
        if response.status_code == 200:
            data = response.json()
            if data.get("status") == "success":
                lat = float(data.get("lat"))
                lon = float(data.get("lon"))
                origin_cache = {
                    "ip": data.get("query"),
                    "lat": lat,
                    "lon": lon,
                    "city": data.get("city") or "Your Location",
                    "region": data.get("regionName") or "",
                    "country": data.get("country") or "",
                    "countryCode": data.get("countryCode") or "",
                    "isp": data.get("isp") or "Local Network",
                    "org": data.get("org") or "",
                    "satellite_image": compute_satellite_tile_url(lat, lon, 13),
                    "google_maps_url": f"https://www.google.com/maps/search/?api=1&query={lat},{lon}"
                }
                return origin_cache
    except Exception:
        pass

    try:
        response = requests.get("https://ipwho.is/", timeout=4.0)
        if response.status_code == 200:
            data = response.json()
            if data.get("success"):
                lat = float(data.get("latitude"))
                lon = float(data.get("longitude"))
                conn = data.get("connection") or {}
                origin_cache = {
                    "ip": data.get("ip"),
                    "lat": lat,
                    "lon": lon,
                    "city": data.get("city") or "Your Location",
                    "region": data.get("region") or "",
                    "country": data.get("country") or "",
                    "countryCode": data.get("country_code") or "",
                    "isp": conn.get("isp") or "Local Network",
                    "org": conn.get("org") or "",
                    "satellite_image": compute_satellite_tile_url(lat, lon, 13),
                    "google_maps_url": f"https://www.google.com/maps/search/?api=1&query={lat},{lon}"
                }
                return origin_cache
    except Exception:
        pass

    return None

def sanitize_target(target: str) -> str:
    """Sanitize target host/domain to prevent command injection."""
    cleaned = target.strip()
    cleaned = re.sub(r"^https?://", "", cleaned)
    cleaned = cleaned.split("/")[0].split(":")[0]
    if not re.match(r"^[a-zA-Z0-9.\-_]+$", cleaned):
        raise HTTPException(status_code=400, detail="Invalid target format. Please enter a valid domain or IP address.")
    return cleaned

def parse_rtts(rtt_matches: List[str]) -> Optional[float]:
    """Parse list of RTT strings into average round-trip time in milliseconds."""
    nums = []
    for r in rtt_matches:
        r = r.strip().lower()
        if "<1" in r:
            nums.append(0.5)
        else:
            m = re.search(r"(\d+(?:\.\d+)?)", r)
            if m:
                nums.append(float(m.group(1)))
    return round(sum(nums) / len(nums), 1) if nums else None

@app.get("/")
def serve_home():
    """Serve index.html at root url."""
    if os.path.exists(HTML_PATH):
        return FileResponse(HTML_PATH, media_type="text/html")
    return HTMLResponse("<h2>index.html not found in the project directory.</h2>", status_code=404)

@app.get("/index.html")
def serve_index_alias():
    return serve_home()

@app.get("/api/origin")
def get_origin():
    """Return local client geolocation (Hop 0)."""
    origin = get_origin_geolocation()
    return {"origin": origin}

@app.get("/api/satellite-tile")
def get_satellite_tile(lat: float, lon: float, zoom: int = 13):
    """Direct helper to get Google Maps satellite hybrid tile URL for any coordinates."""
    url = compute_satellite_tile_url(lat, lon, zoom)
    return {
        "satellite_url": url,
        "lat": lat,
        "lon": lon,
        "zoom": zoom,
        "google_maps_url": f"https://www.google.com/maps/search/?api=1&query={lat},{lon}"
    }

@app.get("/api/trace")
def trace_route(target: str = "google.com", max_hops: int = 15):
    """Execute complete traceroute and return all parsed hops."""
    target = sanitize_target(target)
    max_hops = max(1, min(max_hops, 30))

    is_win = platform.system() == "Windows"
    cmd = ["tracert", "-d", "-h", str(max_hops), "-w", "1000", target] if is_win else ["traceroute", "-n", "-m", str(max_hops), "-w", "1", target]

    try:
        proc = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True, timeout=120)
        output_lines = proc.stdout.splitlines()
    except subprocess.TimeoutExpired:
        raise HTTPException(status_code=504, detail="Traceroute command timed out")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

    origin = get_origin_geolocation()
    hops = []

    for line in output_lines:
        line = line.strip()
        if not line:
            continue

        m = re.match(r"^(\d+)\s+(.+)$", line)
        if not m:
            continue

        hop_num = int(m.group(1))
        rest = m.group(2)

        rtts = re.findall(r"(?:<1|\d+(?:\.\d+)?)\s*ms|\*", rest)
        avg_rtt = parse_rtts(rtts)
        timed_out = "Request timed out" in rest or (avg_rtt is None and "*" in rest)

        ip_match = re.search(r"\b(?:\d{1,3}\.){3}\d{1,3}\b", rest)
        ip = ip_match.group(0) if ip_match else None

        geo = None
        if ip and is_public_ip(ip):
            geo = get_geolocation(ip)

        hops.append({
            "hop": hop_num,
            "ip": ip,
            "rtt": avg_rtt,
            "timed_out": timed_out,
            "geo": geo
        })

    return {
        "target": target,
        "origin": origin,
        "hops": hops,
        "total_hops": len(hops)
    }

@app.get("/api/trace/stream")
def trace_route_stream(target: str = "google.com", max_hops: int = 15):
    """Stream hops in real-time as Server-Sent Events (SSE)."""
    target = sanitize_target(target)
    max_hops = max(1, min(max_hops, 30))

    def event_generator() -> Generator[str, None, None]:
        origin = get_origin_geolocation()
        yield f"data: {json.dumps({'type': 'origin', 'data': origin})}\n\n"

        is_win = platform.system() == "Windows"
        cmd = ["tracert", "-d", "-h", str(max_hops), "-w", "1000", target] if is_win else ["traceroute", "-n", "-m", str(max_hops), "-w", "1", target]

        proc = subprocess.Popen(
            cmd,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
            bufsize=1
        )

        hop_count = 0

        for raw_line in iter(proc.stdout.readline, ''):
            line = raw_line.strip()
            if not line:
                continue

            m = re.match(r"^(\d+)\s+(.+)$", line)
            if m:
                hop_num = int(m.group(1))
                rest = m.group(2)
                hop_count += 1

                rtts = re.findall(r"(?:<1|\d+(?:\.\d+)?)\s*ms|\*", rest)
                avg_rtt = parse_rtts(rtts)
                timed_out = "Request timed out" in rest or (avg_rtt is None and "*" in rest)

                ip_match = re.search(r"\b(?:\d{1,3}\.){3}\d{1,3}\b", rest)
                ip = ip_match.group(0) if ip_match else None

                geo = None
                if ip and is_public_ip(ip):
                    geo = get_geolocation(ip)

                hop_data = {
                    "hop": hop_num,
                    "ip": ip,
                    "rtt": avg_rtt,
                    "timed_out": timed_out,
                    "geo": geo
                }
                yield f"data: {json.dumps({'type': 'hop', 'data': hop_data})}\n\n"

        proc.stdout.close()
        proc.wait()

        yield f"data: {json.dumps({'type': 'done', 'target': target, 'total_hops': hop_count})}\n\n"

    return StreamingResponse(event_generator(), media_type="text/event-stream")

if __name__ == "__main__":
    import uvicorn
    print("\n" + "=" * 60)
    print(" [*] Visual Traceroute Server v2.2 Starting...")
    print(" [+] Google Maps Detailed Satellite Hybrid Integration")
    print(" [+] Zero API Key Required - Multi-Provider Fallback")
    print(" [+] Web UI:  http://localhost:8000")
    print(" [+] API Doc: http://localhost:8000/docs")
    print("=" * 60 + "\n")
    uvicorn.run(app, host="127.0.0.1", port=8000)
