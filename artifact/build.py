"""Embeds fonts (as base64 data URIs) and the trimmed data JSON into template.html
to produce a single self-contained HTML file with no external dependencies.

Fonts are not vendored in this repo (binary assets); download the OFL-licensed
families this template expects - Big Shoulders, Work Sans, Red Hat Mono - from
Google Fonts, or point FONT_DIR at any folder containing:
  BigShoulders-Bold.ttf, WorkSans-Regular.ttf, WorkSans-Bold.ttf, RedHatMono-Regular.ttf

Usage: FONT_DIR=/path/to/fonts python build.py <data.json> <output.html>
"""
import base64
import os
import sys

FONT_DIR = os.environ.get("FONT_DIR", os.path.join(os.path.dirname(__file__), "fonts"))


def b64(path):
    with open(path, "rb") as f:
        return base64.b64encode(f.read()).decode("ascii")


def main():
    data_path, out_path = sys.argv[1], sys.argv[2]
    script_dir = os.path.dirname(os.path.abspath(__file__))

    template = open(os.path.join(script_dir, "template.html"), encoding="utf-8").read()
    data_json = open(data_path, encoding="utf-8").read()

    # guard against a literal "</script>" breaking the containing script tag
    data_json_safe = data_json.replace("</script", "<\\/script")

    replacements = {
        "__FONT_BS_BOLD__": b64(f"{FONT_DIR}/BigShoulders-Bold.ttf"),
        "__FONT_WS_REG__": b64(f"{FONT_DIR}/WorkSans-Regular.ttf"),
        "__FONT_WS_BOLD__": b64(f"{FONT_DIR}/WorkSans-Bold.ttf"),
        "__FONT_RHM_REG__": b64(f"{FONT_DIR}/RedHatMono-Regular.ttf"),
        "__APP_DATA_JSON__": data_json_safe,
    }

    out = template
    for k, v in replacements.items():
        out = out.replace(k, v)

    with open(out_path, "w", encoding="utf-8") as f:
        f.write(out)

    print(f"wrote {out_path} ({len(out) / 1024 / 1024:.2f} MB)")


if __name__ == "__main__":
    main()
