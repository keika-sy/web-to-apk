#!/usr/bin/env python3
"""Inject build inputs into the WebToAPK template.

Replaces __TOKEN__ placeholders committed in the template. Runs inside
GitHub Actions before the Gradle build; can also be run locally.
"""
import argparse, html, re, sys

FILES = {
    "app/build.gradle": ["__APP_ID__"],
    "app/src/main/res/values/strings.xml": ["__APP_NAME__"],
    "app/src/main/res/values/colors.xml": ["__THEME_COLOR__"],
    "app/src/main/AndroidManifest.xml": ["__ORIENTATION__"],
    "app/src/main/java/com/webtoapk/template/MainActivity.java": [
        "__WEB_URL__", "__THEME_COLOR__", "__FULLSCREEN__", "__SPLASH__", "__ZOOM__"],
}

def java_escape(s):
    return s.replace("\\", "\\\\").replace('"', '\\"')

def as_bool(v, label):
    if isinstance(v, bool): return v
    if str(v).lower() in ("true", "1", "yes", "on"): return True
    if str(v).lower() in ("false", "0", "no", "off"): return False
    sys.exit(f"Nilai {label} tidak valid: {v} (pakai true/false)")

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--url", required=True)
    ap.add_argument("--name", required=True)
    ap.add_argument("--package", required=True)
    ap.add_argument("--color", default="#2563EB")
    ap.add_argument("--fullscreen", default="false")
    ap.add_argument("--splash", default="true")
    ap.add_argument("--orientation", default="unspecified",
                    choices=["unspecified", "portrait", "landscape"])
    ap.add_argument("--zoom", default="true")
    a = ap.parse_args()

    url = a.url.strip()
    if not re.match(r"^https?://", url, re.I):
        url = "https://" + url
    if not re.match(r"^https?://[^\s/$.?#].[^\s]*$", url, re.I):
        sys.exit(f"URL tidak valid: {a.url}")

    name = a.name.strip()
    if not name or len(name) > 50:
        sys.exit("Nama app kosong / terlalu panjang (maks 50)")

    pkg = a.package.strip().lower()
    if not re.match(r"^[a-z][a-z0-9_]*(\.[a-z][a-z0-9_]*)+$", pkg):
        sys.exit(f"Package ID tidak valid: {a.package} (contoh: com.contoh.app)")

    color = a.color.strip()
    if not re.match(r"^#?[0-9a-fA-F]{6}$", color):
        sys.exit(f"Warna tidak valid: {a.color} (contoh: #2563EB)")
    color = "#" + color.lstrip("#").upper()

    values = {
        "__APP_ID__": pkg,
        "__APP_NAME__": html.escape(name, quote=True),
        "__WEB_URL__": java_escape(url),
        "__THEME_COLOR__": color,
        "__ORIENTATION__": a.orientation,
        "__FULLSCREEN__": "true" if as_bool(a.fullscreen, "fullscreen") else "false",
        "__SPLASH__": "true" if as_bool(a.splash, "splash") else "false",
        "__ZOOM__": "true" if as_bool(a.zoom, "zoom") else "false",
    }
    for path, tokens in FILES.items():
        with open(path) as f: text = f.read()
        for t in tokens:
            text = text.replace(t, values[t])
        with open(path, "w") as f: f.write(text)
        print(f"customized {path}: {tokens}")

    with open("build-info.txt", "w") as f:
        for k, v in values.items(): f.write(f"{k}={v}\n")
    print(f"OK -> {name} | {pkg} | {url} | {color} | fs={values['__FULLSCREEN__']} splash={values['__SPLASH__']} orient={a.orientation} zoom={values['__ZOOM__']}")

if __name__ == "__main__":
    main()
