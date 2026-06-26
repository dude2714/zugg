import os
import zipfile

repo_path = r'c:\Users\johns\OneDrive\Desktop\empty folder\zugg\repo_fenjr'

print("Scanning repo_fenjr...\n")

for item in sorted(os.listdir(repo_path)):
    item_path = os.path.join(repo_path, item)
    if os.path.isdir(item_path) and item.startswith('script.module.'):
        print(f"Directory: {item}")
        zips = [f for f in os.listdir(item_path) if f.endswith('.zip')]
        print(f"  Found {len(zips)} zip(s): {zips}")
        if zips:
            zip_path = os.path.join(item_path, zips[-1])  # Get latest
            print(f"  Opening: {zips[-1]}")
            try:
                with zipfile.ZipFile(zip_path, 'r') as z:
                    addon_xmls = [n for n in z.namelist() if n.endswith('addon.xml')]
                    print(f"  Found {len(addon_xmls)} addon.xml file(s): {addon_xmls}")
            except Exception as e:
                print(f"  ERROR: {e}")
        print()
