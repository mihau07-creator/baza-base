import os
import urllib.request

libs_dir = r"c:/Users/moled/Antigravity/Baza Base/backend/static/libs"
os.makedirs(libs_dir, exist_ok=True)

urls = {
    "react.js": "https://unpkg.com/react@18/umd/react.production.min.js",
    "react-dom.js": "https://unpkg.com/react-dom@18/umd/react-dom.production.min.js",
    "babel.js": "https://unpkg.com/@babel/standalone/babel.min.js",
    "prop-types.js": "https://unpkg.com/prop-types@15.8.1/prop-types.min.js",
    # Try generic @2 tag which usually points to latest stable 2.x UMD
    "recharts.js": "https://unpkg.com/recharts@2/umd/Recharts.min.js" 
}

for name, url in urls.items():
    dest = os.path.join(libs_dir, name)
    print(f"Downloading {name} from {url}...")
    try:
        urllib.request.urlretrieve(url, dest)
        size = os.path.getsize(dest)
        print(f" -> OK ({size} bytes)")
    except Exception as e:
        print(f" -> ERROR: {e}")
        # Fallback for Recharts if first fails
        if name == "recharts.js":
            fallback = "https://cdn.jsdelivr.net/npm/recharts@2/umd/Recharts.min.js"
            print(f" -> Retrying with {fallback}...")
            try:
                urllib.request.urlretrieve(fallback, dest)
                size = os.path.getsize(dest)
                print(f" -> OK ({size} bytes)")
            except Exception as e2:
                print(f" -> ERROR 2: {e2}")
