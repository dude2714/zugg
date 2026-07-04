from json import loads
import re
from urllib.parse import quote
from urllib.request import Request, urlopen




class source:
    timeout = 8
    priority = 2
    pack_capable = False
    hasMovies = True
    hasEpisodes = True

    def __init__(self):
        self.language = ["en"]
        self.base_link = "https://apibay.org"

    def sources(self, data, hostDict):
        results = []
        if not data:
            return results

        try:
            if "tvshowtitle" in data:
                title = data.get("tvshowtitle", "")
                season = int(data.get("season", 0))
                episode = int(data.get("episode", 0))
                term = f"{title} S{season:02d}E{episode:02d}"
            else:
                title = data.get("title", "")
                year = data.get("year", "")
                term = f"{title} {year}".strip()

            q = re.sub(r"[^A-Za-z0-9\s\.-]+", "", term).strip()
            url = f"{self.base_link}/q.php?q={quote(q)}&cat=0"
            req = Request(url, headers={"User-Agent": "Mozilla/5.0"})
            payload = urlopen(req, timeout=self.timeout).read().decode("utf-8", "ignore")
            files = loads(payload)
        except Exception:
            return results

        for item in files:
            try:
                name = (item.get("name") or "").strip()
                info_hash = (item.get("info_hash") or "").lower()
                if not name or not info_hash:
                    continue
                magnet = f"magnet:?xt=urn:btih:{info_hash}&dn={name}"

                seeders = int(item.get("seeders") or 0)
                try:
                    size_bytes = float(item.get("size") or 0)
                    size_gb = round(size_bytes / (1024.0 ** 3), 3)
                except Exception:
                    size_gb = 0.0

                results.append({
                    "provider": "piratebay",
                    "source": "torrent",
                    "language": "en",
                    "direct": False,
                    "debridonly": True,
                    "hash": info_hash,
                    "url": magnet,
                    "name": name,
                    "name_info": name,
                    "size": size_gb,
                    "seeders": seeders,
                })
            except Exception:
                continue

        return results
