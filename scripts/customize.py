#!/usr/bin/env python3
"""Inject build inputs (URL, app name, package id, theme color) into the template.

Replaces the __TOKEN__ placeholders committed in the template. Runs inside
GitHub Actions before the Gradle build; can also be run locally for a test build.
"""
import argparse, html, re, sys

FILES = {
    "app/build.gradle": ["__APP_ID__"],
    "app/src/main/res/values/strings.xml": ["__APP_NAME__"],
    "app/src/main/res/values/colors.xml": ["__THEME_COLOR__"],
    "app/src/main/java/com/webtoapk/template/MainActivity.java": ["__WEB_URL__", "__THEME_COLOR__"],
}

def java_escape(s):
    return s.replace("\\", "\\\\").replace('"', '\\"')

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--url", required=True)
    ap.add_argument("--name", required=True)
    ap.add_argument("--package", required=True)
    ap.add_argument("--color", default="#2563EB")
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
    }
    # strings.xml gets the XML-escaped name; MainActivity gets plain values.
    for path, tokens in FILES.items():
        with open(path) as f: text = f.read()
        for t in tokens:
            v = values[t]
            if path.endswith("MainActivity.java") and t == "__APP_NAME__":
                v = java_escape(name)
            text = text.replace(t, v)
        with open(path, "w") as f: f.write(text)
        print(f"customized {path}: {tokens}")

    with open("build-info.txt", "w") as f:
        f.write(f"url={url}\nname={name}\npackage={pkg}\ncolor={color}\n")
    print(f"OK -> {name} | {pkg} | {url} | {color}")

if __name__ == "__main__":
    main()
