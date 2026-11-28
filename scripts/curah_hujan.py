#!/usr/bin/env python3
"""Ambil curah hujan per jam terakhir dari SITAJIR Kota Palembang (Pos ARR) -> hujan.json."""
import html, json, re, sys, time, urllib.request

POS = [("Ilir Timur 1", "https://sdakotapalembang.higertech.com/Station/Detail/pos-arr-ilir-timur-1")]


def teks(x):
    return re.sub(r"\s+", " ", html.unescape(re.sub(r"<[^>]+>", " ", x))).strip()


def ambil(url):
    req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0 (cctv-sumsel)"})
    h = urllib.request.urlopen(req, timeout=40).read().decode("utf-8", "replace")
    rows = []
    for tr in re.findall(r"<tr[^>]*>(.*?)</tr>", h, re.S | re.I):
        sel = [teks(td) for td in re.findall(r"<td[^>]*>(.*?)</td>", tr, re.S | re.I)]
        # baris data: [Tanggal, Jam HH:MM, angka mm, Intensitas]
        if len(sel) >= 4 and re.fullmatch(r"\d{1,2}:\d{2}", sel[1]) and re.fullmatch(r"[\d.,]+", sel[2]):
            rows.append({"tanggal": sel[0], "jam": sel[1], "mm": float(sel[2].replace(",", ".")), "intensitas": sel[3]})
    if not rows:
        print("tidak ada baris tabel; ukuran halaman", len(h), file=sys.stderr)
        for m in re.finditer(r"STATION_URL", h):
            print("=====", h[max(0, m.start() - 1500):m.start() + 1500], file=sys.stderr)
    return rows


def main(out):
    hasil = []
    for nama, url in POS:
        try:
            rows = ambil(url)
        except Exception as e:
            print("gagal", nama, e, file=sys.stderr); continue
        if rows:
            r = rows[0]  # tabel diurutkan terbaru di atas
            hasil.append({"pos": nama, **r, "url": url})
            print(nama, r)
    if not hasil:
        sys.exit("tidak ada data curah hujan; hujan.json tidak diubah")
    with open(out, "w", encoding="utf-8") as f:
        json.dump({"updated": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()), "sumber": "SITAJIR PUPR Kota Palembang", "pos": hasil},
                  f, ensure_ascii=False, indent=1)


if __name__ == "__main__":
    main(sys.argv[1] if len(sys.argv) > 1 else "hujan.json")
