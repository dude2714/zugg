import hashlib
import zipfile
import xml.etree.ElementTree as ET
from pathlib import Path

root = Path(r"c:\Users\johns\OneDrive\Desktop\empty folder\zugg")
feed = root / "thepromise.addons.xml"
feed_md5 = root / "thepromise.addons.xml.md5"

files = [
    "repository.thepromise-1.0.4.zip",
    "plugin.video.thepromise-22.4.36.zip",
    "script.module.thepromise.magneto-1.0.1.zip",
    "script.module.promisescrapers-22.4.31.zip",
    "script.module.resolveurl-5.1.206.zip",
    "script.module.pyqrcode-1.0.0.zip",
    "script.module.cocoscrapers-1.0.39.zip",
    "script.module.fenomscrapers-2.10.8.zip",
    "script.module.viperscrapers-1.5.1.zip",
    "script.module.certifi-2023.5.7.zip",
    "script.module.chardet-5.1.0.zip",
    "script.module.idna-3.4.0.zip",
    "script.module.requests-2.31.0.zip",
    "script.module.urllib3-1.26.16+matrix.1.zip",
]

addons_root = ET.Element("addons")

for filename in files:
    zpath = root / filename
    if not zpath.exists():
        continue
    with zipfile.ZipFile(zpath, "r") as zf:
        addon_xml = next((n for n in zf.namelist() if n.endswith("addon.xml")), None)
        if not addon_xml:
            continue
        data = zf.read(addon_xml)
        xml_root = ET.fromstring(data)
        if xml_root.tag == "addon":
            addons_root.append(xml_root)
        elif xml_root.tag == "addons":
            for addon in xml_root.findall("addon"):
                addons_root.append(addon)

xml_text = '<?xml version="1.0" encoding="UTF-8" standalone="yes"?>\n' + ET.tostring(addons_root, encoding="unicode") + "\n"
feed.write_text(xml_text, encoding="utf-8")
feed_md5.write_text(hashlib.md5(xml_text.encode("utf-8")).hexdigest(), encoding="utf-8")

print(f"Wrote {feed}")
print(f"Addons in feed: {len(addons_root.findall('addon'))}")
