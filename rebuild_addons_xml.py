#!/usr/bin/env python3
import os
import zipfile
import xml.etree.ElementTree as ET
import hashlib
from pathlib import Path

def extract_addon_xml_from_zip(zip_path):
    """Extract addon.xml content from a zip file"""
    try:
        with zipfile.ZipFile(zip_path, 'r') as z:
            # Find addon.xml in the zip - usually in a single subdirectory or at root
            for name in z.namelist():
                if name.endswith('addon.xml'):
                    with z.open(name) as f:
                        content = f.read().decode('utf-8')
                        return content
    except Exception as e:
        print(f"    EXTRACTION ERROR reading {os.path.basename(zip_path)}: {e}")
    return None

def rebuild_addons_xml(repo_path):
    """Rebuild addons.xml for a repository"""
    print(f"\nRebuilding addons.xml for: {os.path.basename(repo_path)}")
    
    addons_xml_root = ET.Element('addons')
    addon_elements = []
    
    # Find all module directories
    all_items = sorted(os.listdir(repo_path))
    print(f"  Total items in repo: {len(all_items)}")
    
    for item in all_items:
        item_path = os.path.join(repo_path, item)
        is_dir = os.path.isdir(item_path)
        starts_with = (
            item.startswith('script.module.') or 
            item.startswith('plugin.') or
            item.startswith('repository.') or
            item.startswith('metadata.')
        )
        if is_dir and starts_with:
            print(f"  Processing: {item}")
            # Find the latest zip file in this directory
            zips = sorted([f for f in os.listdir(item_path) if f.endswith('.zip')], reverse=True)
            print(f"    Found {len(zips)} zips: {zips[:1]}")
            if zips:
                zip_path = os.path.join(item_path, zips[0])
                addon_xml = extract_addon_xml_from_zip(zip_path)
                if addon_xml:
                    try:
                        # Parse the addon.xml and extract addon elements
                        root = ET.fromstring(addon_xml)
                        for addon_elem in root.findall('addon'):
                            addon_id = addon_elem.get('id')
                            addon_version = addon_elem.get('version')
                            addon_elements.append((addon_id, addon_version, addon_elem))
                            print(f"      Added: {addon_id} v{addon_version}")
                    except Exception as e:
                        print(f"      Error parsing: {e}")
                else:
                    print(f"    addon_xml was None")
    
    # Add all addon elements to root
    for addon_id, addon_version, elem in addon_elements:
        addons_xml_root.append(elem)
    
    # Pretty print XML
    ET.indent(addons_xml_root, space="  ")
    addons_xml_str = '<?xml version="1.0" encoding="UTF-8" standalone="yes"?>\n' + ET.tostring(addons_xml_root, encoding='unicode')
    
    # Write addons.xml
    addons_xml_path = os.path.join(repo_path, 'addons.xml')
    with open(addons_xml_path, 'w', encoding='utf-8') as f:
        f.write(addons_xml_str)
    
    print(f"  Wrote: addons.xml ({len(addon_elements)} addons)")
    
    # Generate MD5
    md5_hash = hashlib.md5(addons_xml_str.encode()).hexdigest()
    
    addons_md5_path = os.path.join(repo_path, 'addons.xml.md5')
    with open(addons_md5_path, 'w', encoding='utf-8') as f:
        f.write(md5_hash)
    
    print(f"  Generated MD5: {md5_hash}")

# Main
repos = [
    'c:\\Users\\johns\\OneDrive\\Desktop\\empty folder\\zugg\\repo_utopia',
    'c:\\Users\\johns\\OneDrive\\Desktop\\empty folder\\zugg\\repo_fenjr',
    'c:\\Users\\johns\\OneDrive\\Desktop\\empty folder\\zugg\\repository.thepromise'
]

for repo in repos:
    if os.path.isdir(repo):
        rebuild_addons_xml(repo)
    else:
        print(f"Repo not found: {repo}")

print("\nDone!")
