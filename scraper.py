"""
Schengen Visa Appointment Scraper — UK Applicants
Supports: VFS Global (UK), TLScontact (UK), Embassy Direct portals
All URLs point to UK visa application centres.
"""

import logging
import re
from typing import Optional

import httpx
from bs4 import BeautifulSoup

logger = logging.getLogger(__name__)

# ── VFS Global — UK portals ───────────────────────────────────────────────────
VFS_COUNTRY_CONFIG = {
    "AT": {"name": "Austria",        "url": "https://visa.vfsglobal.com/gbr/en/aut"},
    "BE": {"name": "Belgium",        "url": "https://visa.vfsglobal.com/gbr/en/bel"},
    "HR": {"name": "Croatia",        "url": "https://visa.vfsglobal.com/gbr/en/hrv"},
    "CZ": {"name": "Czech Republic", "url": "https://visa.vfsglobal.com/gbr/en/cze"},
    "DK": {"name": "Denmark",        "url": "https://visa.vfsglobal.com/gbr/en/dnk"},
    "EE": {"name": "Estonia",        "url": "https://visa.vfsglobal.com/gbr/en/est"},
    "FI": {"name": "Finland",        "url": "https://visa.vfsglobal.com/gbr/en/fin"},
    "DE": {"name": "Germany",        "url": "https://visa.vfsglobal.com/gbr/en/deu"},
    "GR": {"name": "Greece",         "url": "https://visa.vfsglobal.com/gbr/en/grc"},
    "HU": {"name": "Hungary",        "url": "https://visa.vfsglobal.com/gbr/en/hun"},
    "IT": {"name": "Italy",          "url": "https://visa.vfsglobal.com/gbr/en/ita"},
    "LV": {"name": "Latvia",         "url": "https://visa.vfsglobal.com/gbr/en/lva"},
    "LT": {"name": "Lithuania",      "url": "https://visa.vfsglobal.com/gbr/en/ltu"},
    "MT": {"name": "Malta",          "url": "https://visa.vfsglobal.com/gbr/en/mlt"},
    "NL": {"name": "Netherlands",    "url": "https://visa.vfsglobal.com/gbr/en/nld"},
    "NO": {"name": "Norway",         "url": "https://visa.vfsglobal.com/gbr/en/nor"},
    "PL": {"name": "Poland",         "url": "https://visa.vfsglobal.com/gbr/en/pol"},
    "PT": {"name": "Portugal",       "url": "https://visa.vfsglobal.com/gbr/en/prt"},
    "SK": {"name": "Slovakia",       "url": "https://visa.vfsglobal.com/gbr/en/svk"},
    "SI": {"name": "Slovenia",       "url": "https://visa.vfsglobal.com/gbr/en/svn"},
    "ES": {"name": "Spain",          "url": "https://visa.vfsglobal.com/gbr/en/esp"},
    "SE": {"name": "Sweden",         "url": "https://visa.vfsglobal.com/gbr/en/swe"},
}

# ── TLScontact — UK portals ───────────────────────────────────────────────────
TLS_COUNTRY_CONFIG = {
    "FR": {"name": "France",      "url": "https://fr.tlscontact.com/appointment/gb/gbLON2fr/"},
    "CH": {"name": "Switzerland", "url": "https://ch.tlscontact.com/appointment/gb/gbLON2ch/"},
    "LU": {"name": "Luxembourg",  "url": "https://lu.tlscontact.com/appointment/gb/gbLON2lu/"},
}

# ── Embassy Direct — UK portals ───────────────────────────────────────────────
EMBASSY_COUNTRY_CONFIG = {
    "IS": {
        "name": "Iceland",
        "url":  "https://www.iceland.org/uk/",
        "note": "Apply via the Icelandic Embassy London",
    },
    "LI": {
        "name": "Liechtenstein",
        "url":  "https://ch.tlscontact.com/appointment/gb/gbLON2ch/",
        "note": "Apply via Swiss Embassy (Liechtenstein uses Swiss representation)",
    },
    "BG": {
        "name": "Bulgaria",
        "url":  "https://www.bulgarianembassy-london.org/",
        "note": "Apply via Bulgarian Embassy London",
    },
    "RO": {
        "name": "Romania",
        "url":  "https://londra.mae.ro/en/node/381",
        "note": "Apply via Romanian Embassy London",
    },
}

ALL_COUNTRIES = {
    **{k: {**v, "provider": "VFS"} for k, v in VFS_COUNTRY_CONFIG.items()},
    **{k: {**v, "provider": "TLS"} for k, v in TLS_COUNTRY_CONFIG.items()},
    **{k: {**v, "provider": "EMB"} for k, v in EMBASSY_COUNTRY_CONFIG.items()},
}

HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/124.0.0.0 Safari/537.36"
    ),
    "Accept":          "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
    "Accept-Language": "en-GB,en;q=0.9",
    "Accept-Encoding": "gzip, deflate, br",
    "Connection":      "keep-alive",
}


class SchengenScraper:
    async def check(self, country: str, provider: Optional[str] = None) -> list[dict]:
        cfg = ALL_COUNTRIES.get(country)
        if not cfg:
            logger.warning("Unknown country: %s", country)
            return []
        prov = provider or cfg["provider"]
        try:
            if prov == "VFS":
                return await self._check_vfs(country)
            elif prov == "TLS":
                return await self._check_tls(country)
            elif prov == "EMB":
                return await self._check_embassy(country)
        except Exception as exc:
            logger.error("Scraper error (%s/%s): %s", country, prov, exc)
        return []

    async def _check_vfs(self, country: str) -> list[dict]:
        cfg = VFS_COUNTRY_CONFIG[country]
        base_url  = cfg["url"]
        login_url = f"{base_url}/login"
        slots_url = f"{base_url}/appointment/slots"

        async with httpx.AsyncClient(headers=HEADERS, timeout=20, follow_redirects=True) as client:
            try:
                await client.get(base_url)
            except httpx.HTTPError:
                pass
            try:
                resp = await client.get(login_url)
                resp.raise_for_status()
                slots = self._parse_vfs_html(resp.text, login_url, cfg["name"])
            except httpx.HTTPError as e:
                logger.warning("VFS page error (%s): %s", country, e)
                slots = []
            try:
                api = await client.get(slots_url, headers={**HEADERS, "Accept": "application/json"})
                if api.status_code == 200:
                    slots += self._parse_vfs_api(api.json(), login_url)
            except Exception:
                pass
        return slots

    def _parse_vfs_html(self, html: str, url: str, name: str) -> list[dict]:
        soup = BeautifulSoup(html, "html.parser")
        text = soup.get_text().lower()
        if any(p in text for p in ["no appointment", "no slots", "fully booked", "not available"]):
            return []
        slots = []
        for cell in soup.select(".appointment-date,.slot-date,td.available,.calendar-day.available,[class*='available-slot']"):
            d = cell.get_text(strip=True)
            if re.search(r"\d{4}|\d{1,2}[/-]\d{1,2}", d):
                slots.append({"date": d, "time": "See website", "location": f"VFS Global London — {name}", "url": url})
        if not slots and any(p in text for p in ["book appointment", "select date", "available"]):
            slots.append({"date": "Check website", "time": "Slots may be available", "location": f"VFS Global UK — {name}", "url": url})
        return slots

    def _parse_vfs_api(self, data, url: str) -> list[dict]:
        items = data if isinstance(data, list) else data.get("slots", data.get("appointments", []))
        return [{"date": i.get("date", "?"), "time": i.get("time", "?"), "location": i.get("location", "VFS UK"), "url": url}
                for i in items if isinstance(i, dict)]

    async def _check_tls(self, country: str) -> list[dict]:
        cfg = TLS_COUNTRY_CONFIG[country]
        async with httpx.AsyncClient(headers=HEADERS, timeout=20, follow_redirects=True) as client:
            try:
                resp = await client.get(cfg["url"])
                resp.raise_for_status()
            except httpx.HTTPError as e:
                logger.warning("TLS error (%s): %s", country, e)
                return []
        soup = BeautifulSoup(resp.text, "html.parser")
        text = soup.get_text().lower()
        if any(p in text for p in ["no appointment", "complet", "unavailable", "fully booked"]):
            return []
        return [{"date": d.get("data-date", d.get_text(strip=True)), "time": "Log in to select",
                 "location": f"TLScontact London — {cfg['name']}", "url": cfg["url"]}
                for d in soup.select(".day-available,[data-available='true'],.cal-day.open")]

    async def _check_embassy(self, country: str) -> list[dict]:
        cfg = EMBASSY_COUNTRY_CONFIG.get(country)
        if not cfg:
            return []
        async with httpx.AsyncClient(headers=HEADERS, timeout=20, follow_redirects=True) as client:
            try:
                resp = await client.get(cfg["url"])
                resp.raise_for_status()
            except httpx.HTTPError:
                return []
        text = BeautifulSoup(resp.text, "html.parser").get_text().lower()
        if any(p in text for p in ["no appointment", "fully booked", "unavailable"]):
            return []
        if any(p in text for p in ["book", "available", "appointment", "apply"]):
            return [{"date": "Possible availability", "time": "Check website", "location": cfg["note"], "url": cfg["url"]}]
        return []
