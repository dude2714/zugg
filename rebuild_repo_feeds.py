import hashlib
import os
import re
import zipfile
import xml.etree.ElementTree as ET
from pathlib import Path

REPOS = [
    r"c:\Users\johns\OneDrive\Desktop\empty folder\zugg\repo_utopia",
    r"c:\Users\johns\OneDrive\Desktop\empty folder\zugg\repo_fenjr",
    r"c:\Users\johns\OneDrive\Desktop\empty folder\zugg\repository.thepromise",
    r"c:\Users\johns\OneDrive\Desktop\empty folder\utopia_publish",
]


def version_key(v: str):
    parts = re.split(r"([0-9]+)", v)
    key = []
    for p in parts:
        if not p:
            continue
        if p.isdigit():
            key.append((0, int(p)))
        else:
            key.append((1, p.lower()))
    return key


def extract_addon_element_from_zip(zip_path: Path):
    try:
        with zipfile.ZipFile(zip_path, "r") as zf:
            addon_xml_name = None
            for name in zf.namelist():
                if name.endswith("addon.xml"):
                    addon_xml_name = name
                    break
            if not addon_xml_name:
                return None
            data = zf.read(addon_xml_name)
            root = ET.fromstring(data)
            if root.tag == "addon":
                return root
            if root.tag == "addons":
                first = root.find("addon")
                return first
    except Exception:
        return None
    return None


def rebuild_repo(repo_path: Path):
    zip_files = list(repo_path.rglob("*.zip"))
    by_id = {}

    for zf in zip_files:
        addon_elem = extract_addon_element_from_zip(zf)
        if addon_elem is None:
            continue
        addon_id = addon_elem.attrib.get("id", "")
        addon_ver = addon_elem.attrib.get("version", "0")
        if not addon_id:
            continue

        current = by_id.get(addon_id)
        if current is None or version_key(addon_ver) > version_key(current[0]):
            by_id[addon_id] = (addon_ver, addon_elem)

    addons_root = ET.Element("addons")
    for addon_id in sorted(by_id.keys()):
        addons_root.append(by_id[addon_id][1])

    xml_body = ET.tostring(addons_root, encoding="unicode")
    xml_text = '<?xml version="1.0" encoding="UTF-8" standalone="yes"?>\n' + xml_body + "\n"

    addons_xml = repo_path / "addons.xml"
    addons_md5 = repo_path / "addons.xml.md5"
    addons_xml.write_text(xml_text, encoding="utf-8")
    addons_md5.write_text(hashlib.md5(xml_text.encode("utf-8")).hexdigest(), encoding="utf-8")

    print(f"{repo_path.name}: {len(by_id)} addons in feed")
    for addon_id in sorted(by_id.keys()):
        print(f"  - {addon_id} {by_id[addon_id][0]}")


if __name__ == "__main__":
    for repo in REPOS:
        rp = Path(repo)
        if rp.exists():
            rebuild_repo(rp)
