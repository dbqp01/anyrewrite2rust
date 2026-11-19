# Dependency triage: Dopamine (case study, not ported)

Source: github.com/digimezzo/dopamine @ 19bd0ab (2026-11-16). Electron + Angular music player, ~90k lines TS, 482 non-test TS files.
Inventory produced with `scripts/depmap.py` (files that import each runtime dep and the names they use). Crate versions checked with `cargo search` on 2026-11-19.

## Tier A: direct equivalent crate (swap, then diff-test the call sites)
| npm | used for | crate | note |
|---|---|---|---|
| better-sqlite3 | library DB (2 files, 7 `prepare(` sites) | rusqlite | same SQLite, same SQL; the DB file itself is the contract |
| uuid (`v4`) | ids | uuid | |
| md5-typescript | hashes | md-5 | output must match byte for byte (cache keys on disk) |
| fast-xml-parser | XML | quick-xml | parser options decide shape; diff-test the parsed objects |
| node-fetch | HTTP | reqwest | |
| cheerio, node-html-parser | scraping | scraper | selector semantics differ at the edges |
| fs-extra | file ops | std::fs (+ `fs_extra` if needed) | |
| electron-log | logs | tracing | log format is not a contract; no diff-test |
| sanitize-filename | file names | sanitize-filename (0.8 beta) | small: port it yourself if the beta worries you |

## Tier B: equivalent exists but behaves differently (diff-test the library itself)
| npm | crate | risk |
|---|---|---|
| @digimezzo/node-taglib-sharp | lofty | different tag reader: tolerance to malformed tags, frame names, rating (POPM) mapping. The app also **patches** this lib at install (`patch-taglib-sharp.js`: malformed TXXX frames crash `find`). That patch is behavior the port must keep. |
| moment | chrono | formatting tokens and locale output differ |
| node-vibrant | kmeans_colors / palette | different algorithm: the extracted colors will not match. Accept the divergence or port the algorithm |
| tinycolor2 | csscolorparser + own helpers | only parsing overlaps; lighten/darken math must be checked |
| jimp, @jimp/core | image | resize filters differ: compare by tolerance, not bytes |
| fast-sort | `sort_by` | JS sort is stable, `sort_by` is too; locale-aware string order is not the same |
| discord-rpc | discord-rich-presence | the app **patches** this lib too (`patch-discord-rpc.js` adds `type`). Check the crate sends it |

## Tier C: no library to swap; it is the platform
| what | used in | options |
|---|---|---|
| Angular, @angular/material, @angular/cdk, @angular/animations, angular-split (61 files) | all UI | keep the frontend as is inside Tauri, or rewrite the UI (Leptos/Dioxus/Slint): that is a new app, not a port |
| `new Audio`, `AudioContext`, `createAnalyser` (Chromium) | playback, spectrum | inside Tauri the webview still plays; native means rodio + symphonia, plus an FFT for the analyser |
| `navigator.mediaSession`, Tray, BrowserWindow, ipc | OS integration | souvlaki (media keys), Tauri tray/window/commands |
| @electron/remote | renderer calling main | no equivalent by design; becomes explicit Tauri commands |

## What this means for Dopamine
The cheap, realistic path is **Tauri with the Angular frontend kept**: port the Electron main process and the Node-side services (DB, tags, files, HTTP) to Rust behind Tauri commands, one service at a time, with each service diff-tested through a JSON-lines harness on both sides. A full Rust UI is a rewrite of the product.
