"""Make one QR code per cafe, pointing at the live site with ?cafe= set.

Usage: python -m scripts.make_qr https://<your-site>.onrender.com

These are static codes: the link is inside the image itself, so scanning
never passes through a QR company's redirect server (which would log IPs).
"""
import sys
from pathlib import Path

import qrcode
import qrcode.image.svg

from backend.cafes import CAFES

QR_DIR = Path(__file__).resolve().parent.parent / "qr"


def cafe_links(site_url):
    base = site_url.rstrip("/")
    return {slug: f"{base}/?cafe={slug}" for slug in CAFES}


def write_qr_codes(site_url, out_dir=QR_DIR):
    out_dir = Path(out_dir)
    out_dir.mkdir(exist_ok=True)
    for slug, link in cafe_links(site_url).items():
        qrcode.make(link, image_factory=qrcode.image.svg.SvgPathImage).save(out_dir / f"{slug}.svg")
        print(f"{slug}: {link}")


if __name__ == "__main__":
    write_qr_codes(sys.argv[1])
