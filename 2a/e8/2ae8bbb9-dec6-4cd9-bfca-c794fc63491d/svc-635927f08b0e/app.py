from __future__ import annotations
import json
import re
import urllib.error
import urllib.parse
import urllib.request

from flask import Flask, jsonify, request

app = Flask(__name__)


_IPV4_RE_SOURCE = "^(?:(?:25[0-5]|2[0-4]\d|[01]?\d\d?)\.){3}(?:25[0-5]|2[0-4]\d|[01]?\d\d?)$"
_IPV6_HEX_RE_SOURCE = "^[0-9a-fA-F:]+$"
_IP_API_BASE = "http://ip-api.com/json"
_IP_API_FIELDS = (
    "status,message,country,regionName,city,district,zip,lat,lon,"
    "timezone,isp,org,as,query"
)


def _is_valid_query(q: str) -> bool:
    q = q.strip()
    if not q or len(q) > 253:
        return False
    if re.match(_IPV4_RE_SOURCE, q):
        return True
    if ":" in q and re.match(_IPV6_HEX_RE_SOURCE, q) and q.count(":") >= 2:
        return True
    if any(c.isspace() or c in "/\\?#" for c in q):
        return False
    if "." not in q:
        return False
    return True


def _lookup_external(q: str) -> dict:
    safe_q = urllib.parse.quote(q, safe="")
    url = "{}/{}?fields={}".format(_IP_API_BASE, safe_q, _IP_API_FIELDS)
    req = urllib.request.Request(url, headers={"User-Agent": "ip-geo-app/1.0"}, method="GET")
    try:
        with urllib.request.urlopen(req, timeout=8) as resp:
            body = resp.read().decode("utf-8", errors="replace")
            return json.loads(body)
    except urllib.error.HTTPError as exc:
        return {"status": "fail", "message": "upstream http {}".format(exc.code)}
    except urllib.error.URLError as exc:
        return {"status": "fail", "message": "upstream unreachable: {}".format(exc.reason)}
    except (TimeoutError, json.JSONDecodeError) as exc:
        return {"status": "fail", "message": "upstream error: {}".format(exc)}


def _safe_float(value):
    if value is None:
        return None
    try:
        return float(value)
    except (TypeError, ValueError):
        return None


def _normalize(payload: dict, raw_query: str) -> dict:
    ok = payload.get("status") == "success"
    country = payload.get("country") or ""
    region = payload.get("regionName") or ""
    city = payload.get("city") or ""
    district = payload.get("district") or ""
    location_parts = [p for p in (country, region, city) if p]
    location = " · ".join(location_parts) or "—"
    lat_num = _safe_float(payload.get("lat"))
    lon_num = _safe_float(payload.get("lon"))
    isp = payload.get("isp") or ""
    org = payload.get("org") or ""
    asn = payload.get("as") or ""
    carrier = " / ".join([p for p in (isp, org) if p]) or "—"
    return {
        "ok": ok,
        "query": raw_query,
        "resolvedIp": payload.get("query") or raw_query,
        "country": country,
        "region": region,
        "city": city,
        "district": district,
        "location": location,
        "isp": isp,
        "org": org,
        "asn": asn,
        "carrier": carrier,
        "timezone": payload.get("timezone") or "",
        "zip": payload.get("zip") or "",
        "lat": lat_num,
        "lon": lon_num,
        "mapUrl": (
            "https://www.openstreetmap.org/?mlat={}&mlon={}#map=10/{}/{}".format(
                lat_num, lon_num, lat_num, lon_num
            )
            if lat_num is not None and lon_num is not None
            else ""
        ),
        "error": "" if ok else (payload.get("message") or "查询失败"),
    }


def _do_lookup():
    raw = (
        request.args.get("q")
        or request.args.get("query")
        or request.args.get("ip")
        or ""
    ).strip()
    if not raw and request.is_json:
        body = request.get_json(silent=True) or {}
        raw = (
            body.get("q")
            or body.get("query")
            or body.get("ip")
            or body.get("domain")
            or ""
        ).strip()
    if not raw:
        return jsonify(
            ok=False,
            query="",
            error="缺少查询参数（请提供 q / query / ip / domain）",
        ), 400
    if not _is_valid_query(raw):
        return jsonify(
            ok=False,
            query=raw,
            error="查询字符串格式不合法（不是有效的 IP 或域名）",
        ), 400
    payload = _lookup_external(raw)
    result = _normalize(payload, raw)
    return jsonify(result), (200 if result["ok"] else 502)


@app.get("/lookup")
def lookup_get():
    return _do_lookup()


@app.post("/lookup")
def lookup_post():
    return _do_lookup()
