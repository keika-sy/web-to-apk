# Web to APK

Ubah website apa pun jadi aplikasi Android (APK) dari form web. Build-nya
dikerjakan **GitHub Actions** — server web tidak perlu compile apa pun.

## Cara kerja

```
Form web  ->  Cloudflare Worker (backend tipis, pegang token)
          ->  GitHub Actions: workflow_dispatch
          ->  customize.py menyuntik URL/nama/package/warna ke template WebView
          ->  Gradle build release APK (di-sign keystore tetap dari Secrets)
          ->  APK diterbitkan ke GitHub Releases -> user download
```

## Pakai sekarang juga (tanpa web, trigger manual)

1. Buka tab **Actions** repo ini → workflow **Build APK** → **Run workflow**
2. Isi: URL website, nama app, package ID, (opsional) URL icon + warna tema
3. Tunggu ±3–6 menit → APK muncul di tab **Releases** repo ini, siap download & install

## Aktifkan form web-nya

Web statis ada di folder `docs/` (bisa di-host GitHub Pages: Settings → Pages →
branch `main`, folder `/docs`). Form butuh backend kecil supaya token GitHub
tidak bocor ke browser:

1. `cd backend && npx wrangler deploy`
2. `npx wrangler secret put GH_TOKEN` — fine-grained PAT khusus repo ini,
   permission **Actions: Read and write**
3. Salin URL Worker ke `docs/index.html` → `const BACKEND_URL = "..."`

Selama `BACKEND_URL` kosong, form menampilkan tombol trigger manual ke
halaman Actions (tetap berfungsi untuk pemilik repo).

## Template APK

- WebView: JavaScript + DOM storage aktif, progress bar
- **Splash screen** warna tema + nama app (bisa dimatikan)
- **Mode fullscreen** (status bar disembunyikan), **orientasi** otomatis/potret/lanskap,
  **pinch-zoom** bisa diatur
- Link non-http (WhatsApp, telp, email, Maps) dibuka di aplikasi aslinya
- Upload file dari halaman web didukung, download dibuka via sistem
- Halaman error offline custom + tombol coba lagi, tombol Back mengikuti history
- Icon: default globe; kalau URL icon diisi, digenerate ke semua density
  (termasuk versi bulat) saat build

## Fitur web-nya

- Pratinjau HP langsung (nama, favicon, warna, splash, status bar ikut berubah)
- Mode gelap, 8 warna preset + color picker, package ID otomatis dari nama app
  (+ tombol acak), validasi langsung
- Preset situs contoh, riwayat build di browser (klik untuk pakai lagi)
- Export / import konfigurasi JSON, salin ringkasan build
- Bisa di-install sebagai PWA (manifest + service worker)

## Signing

Workflow men-decode keystore dari secret `KEYSTORE_BASE64` (+ password di
`KEYSTORE_PASSWORD`) supaya signature **konsisten antar build** — APK hasil
build berikutnya bisa di-install menimpa versi sebelumnya. Tanpa secret itu,
build otomatis jatuh ke debug key.

Membuat / memperbarui secret:

```bash
keytool -genkeypair -keystore webtoapk.jks -alias webtoapk -keyalg RSA \
  -keysize 2048 -validity 10000 -dname "CN=WebToAPK, O=WebToAPK, C=ID"
base64 -w0 webtoapk.jks | gh secret set KEYSTORE_BASE64 --repo keika-sy/web-to-apk
gh secret set KEYSTORE_PASSWORD --repo keika-sy/web-to-apk
```

## Build lokal (opsional)

```bash
python3 scripts/customize.py --url https://contoh.com --name "App Saya" \
  --package com.contoh.app --color "#2563EB"
./gradlew assembleRelease
```

## Batasan v1

- Satu build = satu antrian Actions (±3–6 menit per APK)
- Icon hanya via URL (upload file langsung = rencana v2)
- Keystore v1 adalah keystore aplikasi mandiri, bukan Play App Signing —
  APK ini untuk distribusi langsung (sideload), bukan Play Store

Workflow Actions aktif di `.github/workflows/build-apk.yml` (salinan sumber juga ada di `ci/`).
