#!/usr/bin/env python3
"""Ambil curah hujan per jam terakhir dari SITAJIR Kota Palembang (Pos ARR) -> hujan.json.
Halaman memuat tabel lewat POST /Station/DataTableDetailStation (stationId, deviceId, filterDate, selectedTime=hour, stationType)."""
import http.cookiejar, json, re, sys, time, urllib.parse, urllib.request

BASE = "https://sdakotapalembang.higertech.com"
POS = [("Palembang", "pos-arr-ilir-timur-1")]
LABEL = {0: "Tidak Ada Hujan", 1: "Hujan Ringan", 2: "Hujan Sedang", 3: "Hujan Lebat", 4: "Hujan Sangat Lebat"}
UA = {"User-Agent": "Mozilla/5.0 (cctv-sumsel)"}


def label(v):
    try:
        k = int(v)
        if 0 <= k <= 4:
            return LABEL[k]
    except Exception:
        pass
    return str(v or "").strip() or "-"


def ambil(slug):
    op = urllib.request.build_opener(urllib.request.HTTPCookieProcessor(http.cookiejar.CookieJar()))
    h = op.open(urllib.request.Request(f"{BASE}/Station/Detail/{slug}", headers=UA), timeout=40).read().decode("utf-8", "replace")
    g = lambda k: (re.search(k + r"\s*=\s*'([^']+)'", h) or [None, None])[1]
    sid, dev, typ = g("stationId"), g("deviceId"), g("stationType") or "ARR"
    token = (re.search(r'name="__RequestVerificationToken"[^>]*value="([^"]+)"', h) or [None, None])[1]
    if not sid or not dev:
        raise RuntimeError("stationId/deviceId tidak ditemukan")
    wib = time.gmtime(time.time() + 7 * 3600)
    rows = []
    for hari in (time.strftime("%Y-%m-%d", wib), time.strftime("%Y-%m-%d", time.gmtime(time.time() + 7 * 3600 - 86400))):
        form = {"draw": "1", "start": "0", "length": "-1", "stationId": sid, "deviceId": dev, "filterDate": hari,
                "selectedTime": "hour", "stationType": typ}
        if token:
            form["__RequestVerificationToken"] = token
        req = urllib.request.Request(f"{BASE}/Station/DataTableDetailStation", data=urllib.parse.urlencode(form).encode(),
                                     headers={**UA, "X-Requested-With": "XMLHttpRequest", "Referer": f"{BASE}/Station/Detail/{slug}",
                                              "Content-Type": "application/x-www-form-urlencoded; charset=UTF-8"})
        j = json.loads(op.open(req, timeout=40).read().decode("utf-8", "replace"))
        data = j.get("data") if isinstance(j, dict) else j
        for d in data or []:
            waktu = d.get("readingHour") or d.get("readingAt") or d.get("readingDate")
            mm = d.get("rainfall")
            if waktu and mm is not None:
                rows.append({"waktu": waktu, "mm": float(mm), "intensitas": label(d.get("intensity"))})
        if rows:
            break
        print("kosong untuk", hari, str(j)[:300], file=sys.stderr)
    rows.sort(key=lambda r: r["waktu"], reverse=True)
    return rows


def main(out):
    hasil = []
    for nama, slug in POS:
        try:
            rows = ambil(slug)
        except Exception as e:
            print("gagal", nama, e, file=sys.stderr); continue
        if rows:
            r = rows[0]
            m = re.search(r"T(\d{2}):(\d{2})", r["waktu"])
            hasil.append({"pos": nama, "jam": f"{m[1]}.{m[2]}" if m else r["waktu"], **r, "url": f"{BASE}/Station/Detail/{slug}"})
            print(nama, hasil[-1])
    if not hasil:
        sys.exit("tidak ada data curah hujan; hujan.json tidak diubah")
    with open(out, "w", encoding="utf-8") as f:
        json.dump({"updated": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()), "sumber": "SITAJIR PUPR Kota Palembang", "pos": hasil},
                  f, ensure_ascii=False, indent=1)


if __name__ == "__main__":
    main(sys.argv[1] if len(sys.argv) > 1 else "hujan.json")
