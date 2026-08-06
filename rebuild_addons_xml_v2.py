#!/usr/bin/env python3
import os
import zipfile
import xml.etree.ElementTree as ET
import hashlib

def extract_addon_xml_from_zip(zip_path):
    """Extract addon.xml content from a zip file"""
    try:
        with zipfile.ZipFile(zip_path, 'r') as z:
            for name in z.namelist():
                if name.endswith('addon.xml'):
                    with z.open(name) as f:
                        return f.read().decode('utf-8')
    except Exception as e:
        pass
    return None

def rebuild_addons_xml(repo_path):
    """Rebuild addons.xml for a repository"""
    print(f"\nRebuilding: {os.path.basename(repo_path)}")
    
    addon_list = []
    
    for item in sorted(os.listdir(repo_path)):
        item_path = os.path.join(repo_path, item)
        if os.path.isdir(item_path) and (
            item.startswith('script.module.') or 
            item.startswith('plugin.') or
            item.startswith('repository.') or
            item.startswith('metadata.')
        ):
            zips = sorted([f for f in os.listdir(item_path) if f.endswith('.zip')], reverse=True)
            if zips:
                zip_path = os.path.join(item_path, zips[0])
                addon_xml_str = extract_addon_xml_from_zip(zip_path)
                if addon_xml_str:
                    try:
                        root = ET.fromstring(addon_xml_str)
                        if root.tag == 'addon':
                            addon_id = root.get('id')
                            addon_version = root.get('version')
                            addon_list.append(root)
                            print(f"  ✓ {addon_id} v{addon_version}")
                        else:
                            for addon_elem in root.findall('addon'):
                                addon_id = addon_elem.get('id')
                                addon_version = addon_elem.get('version')
                                addon_list.append(addon_elem)
                                print(f"  ✓ {addon_id} v{addon_version}")
                    except Exception as e:
                        print(f"  ✗ Parse error {item}: {e}")
    
    # Build final XML
    root = ET.Element('addons')
    for elem in addon_list:
        root.append(elem)
    
    # Convert to string with proper formatting
    xml_str = '<?xml version="1.0" encoding="UTF-8" standalone="yes"?>\n'
    xml_str += ET.tostring(root, encoding='unicode')
    
    # Write files
    addons_xml_path = os.path.join(repo_path, 'addons.xml')
    with open(addons_xml_path, 'w', encoding='utf-8') as f:
        f.write(xml_str)
    
    md5_hash = hashlib.md5(xml_str.encode()).hexdigest()
    with open(os.path.join(repo_path, 'addons.xml.md5'), 'w', encoding='utf-8') as f:
        f.write(md5_hash)
    
    print(f"  Wrote {len(addon_list)} addons (MD5: {md5_hash[:8]}...)")

# Main
repos = [
    r'c:\Users\johns\OneDrive\Desktop\empty folder\zugg\repo_utopia',
    r'c:\Users\johns\OneDrive\Desktop\empty folder\zugg\repo_fenjr',
    r'c:\Users\johns\OneDrive\Desktop\empty folder\zugg\repository.thepromise'
]

for repo in repos:
    if os.path.isdir(repo):
        rebuild_addons_xml(repo)

print("\nDone!")
