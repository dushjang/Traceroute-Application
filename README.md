# 🛰️ Visual Traceroute Pro: Real-Time Global Network Path Visualizer

[![Python Version](https://img.shields.io/badge/Python-3.10%2B-blue?logo=python&logoColor=white)](https://www.python.org/)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.100%2B-009688?logo=fastapi&logoColor=white)](https://fastapi.tiangolo.com/)
[![Leaflet](https://img.shields.io/badge/Leaflet-1.9.4-199900?logo=leaflet&logoColor=white)](https://leafletjs.com/)
[![Google Maps Satellite](https://img.shields.io/badge/Imagery-Google_Satellite_Hybrid-4285F4?logo=google-maps&logoColor=white)](https://maps.google.com)
[![License](https://img.shields.io/badge/License-MIT-green.svg)](LICENSE)
[![Zero API Key](https://img.shields.io/badge/API_Keys-0_Required-brightgreen)](https://github.com)

**Visual Traceroute Pro** is an interactive, real-time cybersecurity and networking tool that traces, geolocates, and visualizes internet packet hops across the globe. Built with a high-performance **FastAPI** backend and an interactive **Leaflet** map featuring **Google Maps Satellite Hybrid** imagery, it maps network traffic from your local machine (Hop 0) through intermediate backbones and ISPs straight to the destination server.

---

## 📸 Overview

```text
 [Your Location] ──────> [ISP Gateway] ──────> [Underwater Cables / Backbones] ──────> [Destination Server]
      (Delhi)             (Regional Router)             (Frankfurt / Tokyo)                   (Google / Cloudflare)
```

Instead of staring at dry terminal text from `tracert` or `traceroute`, Visual Traceroute renders:
- Live streaming packet discovery via **Server-Sent Events (SSE)**.
- High-resolution **Google Maps Satellite Hybrid** imagery showing streets, highways, borders, and landmarks.
- Detailed network telemetry: round-trip time (RTT latency), ISP, ASN, city, and geodesic distance.

---

## ✨ Key Features

- 🛰️ **Google Maps Detailed Satellite Hybrid Imagery**:
  - Photorealistic satellite photography overlaid with roads, highway badges, street names, airports, and city labels.
  - Seamless zoom down to street and building level (up to zoom level 20).
  - Multi-layer toggle: **Google Satellite Hybrid**, **Pure Satellite**, **Terrain/Relief**, and **Dark Cyber (NOC mode)**.

- ⚡ **Real-Time Live Streaming (SSE)**:
  - Utilizes Server-Sent Events (`/api/trace/stream`) so hops drop onto the map and sidebar timeline progressively as each router responds. No frozen screens or 40-second blank waits.

- 🔑 **Zero API Key Requirement (100% Free & Unlimited)**:
  - Built-in resilient 3-tier fallback chain (`ip-api` → `ipwho.is` → `freeipapi`) with in-memory caching.
  - No credit cards, API registration, or rate-limit blocks.

- 🟢 **Origin Hop Detection (Hop 0)**:
  - Automatically identifies and plots your local public IP location as Hop 0 so network journeys originate from your real-world city.

- 🔍 **Geosatellite Inspector with Multi-Level Zoom**:
  - Click any hop in the timeline to view a dedicated satellite snapshot.
  - Toggle between **11x (Region)**, **13x (City)**, and **15x (Neighborhood/Street)** zoom.
  - Includes a direct **"🌐 Google Maps"** deep link to launch full 3D satellite and Google Street View.

- 📊 **Network Analytics & KPI Dashboard**:
  - Total hops count & geocoded node counter.
  - Average round-trip latency (color-coded: green < 35ms, yellow 35-90ms, red > 90ms).
  - Geodesic distance calculation across the globe using the Haversine formula.

- 💾 **Export Telemetry**:
  - One-click JSON export for reporting, analysis, or network documentation.

---

## 🛠️ Tech Stack

| Component | Technologies |
| :--- | :--- |
| **Backend** | Python 3, FastAPI, Uvicorn, Requests, Starlette |
| **Frontend** | Vanilla HTML5, Modern CSS (Glassmorphism & Cyber Aesthetics), Vanilla JavaScript |
| **Mapping Engine** | Leaflet.js, Google Maps Hybrid Tiles (`lyrs=y`, `lyrs=s`, `lyrs=p`), CartoDB Dark Matter |
| **Networking & Telemetry** | Native OS `tracert` (Windows) / `traceroute` (Linux/macOS), `ipaddress` validation |
| **Geolocation** | Multi-Provider Fallback (ip-api, ipwho.is, freeipapi) |

---

## 🚀 Quick Start

### 1. Prerequisites
- **Python 3.10+** installed on your system.

### 2. Clone the Repository
```bash
git clone https://github.com/your-username/visual-traceroute.git
cd visual-traceroute
```

### 3. Install Dependencies
```bash
pip install fastapi uvicorn requests
```

### 4. Run the Application
```bash
python TracerouteProject.py
```

### 5. Open in Browser
Navigate to:
```text
http://localhost:8000
```

---

## 🎯 How It Works

1. **Target Input**: Enter any hostname (e.g., `google.com`, `github.com`) or IP address (e.g., `1.1.1.1`), or select a quick preset.
2. **Native Trace Execution**: The backend executes an optimized OS-level traceroute with a 1000ms probe timeout (`-w 1000`) to prevent long hangs on unresponsive hops.
3. **Regex & Line-by-Line Parsing**: Each hop number, IP, and round-trip time (RTT) is extracted cleanly while discarding private/internal subnets (`192.168.x.x`, `10.x.x.x`, `127.x.x.x`).
4. **Geolocation Enrichment**: Public IP addresses are resolved against geocoding endpoints, returning coordinates, city, country, and ISP.
5. **SSE Streaming to Leaflet**: Each resolved node streams over HTTP to the frontend, instantly dropping a pulsing marker, rendering high-detail Google satellite tiles, and drawing animated glowing route polylines across the map.

---

## 📁 Project Structure

```text
├── TracerouteProject.py     # FastAPI backend server & traceroute stream engine
├── index.html               # Frontend dashboard, Google Satellite map & UI
├── README.md                # Project documentation
└── LICENSE                  # MIT License
```

---

## 🛡️ License

Distributed under the **MIT License**. See `LICENSE` for more information.

---

## 👨‍💻 Authors & Acknowledgments

- Developed as an Advanced Networking & Visualization Minor Project.
- Mapping powered by **Leaflet** & **Google Maps**.
- Geolocation telemetry powered by open community providers.
