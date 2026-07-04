from json import loads
import re
from urllib.request import Request, urlopen




class source:
    timeout = 8
    priority = 1
    pack_capable = False
    hasMovies = True
    hasEpisodes = True

    def __init__(self):
        self.language = ["en"]
        self.base_link = "https://torrentio.strem.fun"

    def sources(self, data, hostDict):
        results = []
        imdb = (data or {}).get("imdb")
        if not imdb:
            return results

        try:
            if "tvshowtitle" in data:
                season = data.get("season")
                episode = data.get("episode")
                url = f"{self.base_link}/stream/series/{imdb}:{season}:{episode}.json"
            else:
                url = f"{self.base_link}/stream/movie/{imdb}.json"
            req = Request(url, headers={"User-Agent": "Mozilla/5.0"})
            payload = urlopen(req, timeout=self.timeout).read().decode("utf-8", "ignore")
            streams = loads(payload).get("streams", [])
        except Exception:
            return results

        for item in streams:
            try:
                title_lines = (item.get("title") or "").split("\n")
                name = title_lines[0].strip() if title_lines else "torrentio"
                info_hash = (item.get("infoHash") or "").lower()
                if not info_hash:
                    continue
                magnet = f"magnet:?xt=urn:btih:{info_hash}&dn={name}"

                seeders = 0
                size_gb = 0.0
                for line in title_lines:
                    if "👤" in line:
                        match = re.search(r"(\d+)", line)
                        if match:
                            seeders = int(match.group(1))
                    size_match = re.search(r"((?:\d+[\.,]?\d*)\s*(?:GB|GiB|MB|MiB))", line, re.I)
                    if size_match:
                        raw = size_match.group(1).upper().replace(",", ".")
                        num = float(re.search(r"\d+(?:\.\d+)?", raw).group(0))
                        size_gb = num / 1024.0 if "MB" in raw or "MIB" in raw else num

                results.append({
                    "provider": "torrentio",
                    "source": "torrent",
                    "language": "en",
                    "direct": False,
                    "debridonly": True,
                    "hash": info_hash,
                    "url": magnet,
                    "name": name,
                    "name_info": name,
                    "size": round(size_gb, 3),
                    "seeders": seeders,
                })
            except Exception:
                continue

        return results
