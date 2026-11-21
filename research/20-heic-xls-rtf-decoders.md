# 20 - HEIC, XLS and RTF decoders (licence and packaging facts)

Date of research: 2026-11-21. Labels: VERIFIED = I read the page named; SECONDARY = a search result or a mirror; UNVERIFIED = not opened. No legal advice.

## TL;DR for builders

- Debian trixie route: `apt-get install --no-install-recommends libheif-examples libheif-plugin-libde265` (libheif 1.23.6-2~deb13u1). By the package metadata I read, no GPL package is in the closure. `libheif1` Recommends the x265 plugin (GPL), so `--no-install-recommends` is required. VERIFIED (not run: no shell here, install not tested).
- Licences on that route: libheif library LGPL-3+, libde265 library LGPL-3+, libheif `heif-dec` sample apps MIT/Expat, dav1d plugin path BSD (dav1d licence UNVERIFIED). LGPL is not GPL but is a copyleft-family licence (see Q6); the owner decides whether the task card's "copyleft (AGPL, GPL)" wording admits LGPL.
- Alpine 3.24 route (python:3.14-alpine): `apk add libheif libheif-tools`. libheif 1.23.7-r0; x265 is a separate plugin package `libheif-x265`, auto-installed only if `x265-libs` is present. Closure of libheif itself NOT fully read (pkgs.alpinelinux.org detail pages returned 404). Hard dependencies: `libheif-dav1d` and `libheif-libde265` VERIFIED from APKBUILD.
- pi-heif is DISCONTINUED: 1.4.0 (2026-06-10) is final and bundles libheif 1.23.0, hit by CVE-2026-84383 (CVSS 9.8, heap overflow on crafted HEIC; fixed in libheif 1.23.2). Do not use it for untrusted files. Use pillow-heif 1.8.1 (2026-10-11) or the system libheif. Whether pi-heif wheels contain x265: UNVERIFIED (could not open a wheel). pillow-heif's own bundled-licence file lists x265 GPLv2.
- xlrd 2.0.2 (2025-06-14), BSD, .xls only. Python 3.14 officially: not declared (classifiers stop at 3.9). RTF: striprtf 0.0.35 (2026-10-24), BSD-3-Clause.

## Verdict table

| # | Question | Verdict | Label |
|---|---|---|---|
| 1 | Debian trixie HEIC without GPL | libheif-examples + plugin-libde265 pulls no GPL package by metadata; heif-dec exists | VERIFIED (metadata only, not run) |
| 2 | Alpine HEIC | x265 is a split plugin package; libheif depends on dav1d + libde265 plugins | VERIFIED (APKBUILD) |
| 3 | pi-heif | discontinued, final 1.4.0, cp314 wheels exist, vulnerable bundled libheif; bundled libs not verified | VERIFIED / UNVERIFIED (libs) |
| 3b | pillow-heif | 1.8.1, BSD-3-Clause package, cp314 wheels exist, bundled x265 GPLv2 listed | VERIFIED |
| 4 | xlrd | 2.0.2, BSD, .xls only, no 3.14 classifier, no CVE found | VERIFIED / SECONDARY |
| 5 | RTF reader | striprtf 0.0.35, BSD-3-Clause | VERIFIED (cells: UNVERIFIED) |
| 6 | LGPL classification | copyleft family (weak/lesser); two sources partly indirect | SECONDARY |

## 1. Debian trixie

- libheif-examples 1.23.6-2~deb13u1, section video. Depends: libc6, libgcc-s1, libheif1 (= same version), libjpeg62-turbo, libpng16-16t64, libstdc++6, libtiff6, libwebp7, libwebpmux3. VERIFIED https://packages.debian.org/trixie/libheif-examples (2026-11-21).
- Files: /usr/bin/heif-convert, heif-dec, heif-enc, heif-info. VERIFIED https://packages.debian.org/trixie/amd64/libheif-examples/filelist (2026-11-21).
- libheif1 1.23.6-2~deb13u1. Depends: libbrotli1, libc6, libgcc-s1, (libheif-plugin-dav1d OR libheif-plugin-aomdec), libheif-plugin-libde265, libsharpyuv0, libstdc++6, zlib1g. Recommends: libheif-plugin-aomenc, libheif-plugin-x265. Suggests: ffmpegdec, j2k, jpeg, kvazaar, rav1e, svtenc plugins. VERIFIED https://packages.debian.org/trixie/libheif1 (2026-11-21).
  - Consequence: with `--no-install-recommends` the x265 plugin is not installed. Without that flag it is (GPL).
  - The "dav1d OR aomdec" alternative resolves to the first, dav1d, in apt normally (apt behaviour, UNVERIFIED here).
- libheif-plugin-dav1d depends: libdav1d7, libheif1, libc6, libgcc-s1, libstdc++6. VERIFIED https://packages.debian.org/trixie/libheif-plugin-dav1d (2026-11-21).
- libheif-plugin-libde265 depends: libde265-0 (>= 1.0.7), libheif1, libc6, libgcc-s1, libstdc++6. No recommends/suggests. VERIFIED https://packages.debian.org/trixie/libheif-plugin-libde265 (2026-11-21).
- libtiff6 4.7.0-3+deb13u3 depends: libdeflate0, libjbig0, libjpeg62-turbo, liblerc4, liblzma5, libwebp7, libzstd1, zlib1g; no recommends. VERIFIED https://packages.debian.org/trixie/libtiff6 (2026-11-21). I did not open the licence of these small libraries (libjbig0 is GPL-2+ in some distributions: UNVERIFIED, CHECK before claiming a GPL-free closure; libjbig0 is pulled in by libtiff6 via libheif-examples).
  - Request: the lead should run `apt-get install -s --no-install-recommends ...` and `dpkg-query -W -f='${Package} ${License}'`/read /usr/share/doc/*/copyright in the image build to confirm, and check libjbig0 and liblerc4 explicitly.
- Licences (Debian copyright file of libheif, unstable at the time read): library `*` LGPL-3+; `examples/*` (except benchmark) and tests: Expat (MIT); the file states "only the sample applications are MIT/Expat licensed while the decoding library itself is licensed as LGPL-3+"; debian/* and scripts/* GPL-3+ (packaging and scripts, not shipped binaries); extra/getopt* BSD-4-Clause-UC. VERIFIED https://metadata.ftp-master.debian.org/changelogs/main/libh/libheif/unstable_copyright (2026-11-21). The copyright file is for unstable, not exactly 1.23.6-2~deb13u1: SECONDARY for trixie.
- libde265 (unstable copyright): library LGPL-3+; ARM assembly LGPL-2.1+; sample apps (dec265, sherlock265) Expat; bundled getopt BSD-4-clause-UC. No GPL part listed. VERIFIED https://metadata.ftp-master.debian.org/changelogs/main/libd/libde265/unstable_copyright (2026-11-21).
- `heif-dec` from only the libde265 (+dav1d) plugins to PNG/JPEG: heif-dec/heif-convert exist and are the sample decoder/converter; the PNG/JPEG output uses libpng and libjpeg, which are in the Depends of libheif-examples. That it converts a HEVC .heic with only the libde265 plugin is expected (libde265 is the HEVC decoder) but I did not run it: UNVERIFIED. Test in CI with a synthetic HEIC.
- Security: the libheif GHSA below affects v1.22.0 to v1.23.1; trixie 1.23.6 is above the fix (1.23.2). Debian may carry later patches; not checked.

## 2. Alpine (python:3.14-alpine)

- `python:3.14-alpine` currently equals `3.14-alpine3.24` (Alpine 3.24). VERIFIED https://hub.docker.com/_/python (2026-11-21).
- Alpine 3.24 community repo, x86_64: libheif 1.23.7-r0, libheif-tools, plugin packages libheif-aom, -dav1d, -ffmpeg, -jpeg, -libde265, -openh264, -openjpeg, -rav1e, -svtenc, -x264, -x265, metapackage libheif-plugins-all; every one listed as LGPL-3.0-or-later. VERIFIED https://pkgs.alpinelinux.org/packages?name=libheif*&branch=v3.24&repo=&arch=x86_64 (2026-11-21).
- APKBUILD (master, pkgver 1.23.7): `depends="$pkgname-dav1d $pkgname-libde265"`; plugin loading ON; x265 and libde265 built as plugins (`WITH_X265_PLUGIN=ON`, `WITH_LIBDE265_PLUGIN=ON`); each plugin package depends on libheif and carries one .so; x265 plugin `install_if="libheif=... x265-libs"` (installs itself only if x265-libs is already present); dav1d and libde265 have no install_if (hard dependencies of libheif); libheif-tools holds usr/bin and depends on heif-thumbnailer. VERIFIED https://raw.githubusercontent.com/alpinelinux/aports/master/community/libheif/APKBUILD (2026-11-21). This is master, not the 3.24 branch tag: SECONDARY for 3.24 exactly.
- So `apk add libheif libheif-tools` does not link x265 into libheif; x265 enters only if x265-libs is installed by something else (then the plugin auto-installs). Minimal closure of the other libraries (dav1d-libs, libde265, etc.): not read (package detail pages 404). UNVERIFIED. Avoid `libheif-plugins-all`.
- Licences: libheif LGPL-3.0-or-later (Alpine metadata); libde265 LGPL-3 (Debian copyright, above); x265 is GPL-2 (see bundled-licence file below; Alpine x265 licence not read).

## 3. pi-heif and pillow-heif (PyPI)

- pi-heif 1.4.0, released 2026-06-10, package licence `BSD-3-Clause` in metadata, but a classifier says LGPLv3; files LICENSE.txt and LICENSES_bundled.txt. VERIFIED https://pypi.org/pypi/pi-heif/1.4.0/json and https://pypi.org/project/pi-heif/ (2026-11-21).
- Description: "includes only HEIF decoder and does not support save operations"; "a light version of Pillow-Heif with more permissive license for binary wheels". VERIFIED https://pypi.org/project/pi-heif/.
- Wheels (all uploaded 2026-06-10): `pi_heif-1.4.0-cp314-cp314-manylinux_2_27_x86_64.manylinux_2_28_x86_64.whl`, `pi_heif-1.4.0-cp314-cp314-musllinux_1_2_x86_64.whl` (also cp314t variants). VERIFIED https://pypi.org/pypi/pi-heif/1.4.0/json.
- Discontinued: "Version 1.4.0 is its final release"; wheels bundle libheif 1.23.0, affected by CVE-2026-84383 (GHSA-g89c-p67h-r497). VERIFIED https://github.com/bigcat88/pillow_heif/blob/master/README.md and https://raw.githubusercontent.com/bigcat88/pillow_heif/master/README.md (2026-11-21).
- GHSA: affects libheif v1.22.0 to v1.23.1, patched 1.23.2, published 2026-08-25, CVSS 9.8, crafted HEIC/HEIF/AVIF; any app calling heif_decode_image is affected. VERIFIED https://github.com/strukturag/libheif/security/advisories/GHSA-g89c-p67h-r497.
- Bundled libraries in pi-heif wheels and whether x265 is absent: UNVERIFIED. I could not open a wheel (no shell). Indirect: pi-heif is "decoder only" and sold as more permissive, which suggests no x265, but that is an inference. Check by `unzip -l` on the wheel (`pi_heif.libs/`) and its LICENSES_bundled.txt.
- pillow-heif 1.8.1, released 2026-10-11, licence BSD-3-Clause, requires Python >= 3.10; wheels `pillow_heif-1.8.1-cp314-cp314-manylinux_2_27_x86_64.manylinux_2_28_x86_64.whl` and `pillow_heif-1.8.1-cp314-cp314-musllinux_1_2_x86_64.whl`. VERIFIED https://pypi.org/pypi/pillow-heif/1.8.1/json.
- pillow-heif `LICENSES_bundled.txt` (master): wheels bundle libheif LGPLv3, libde265 LGPLv3, x265 GPLv2; says the binary wheels are "GPLv2, due to base library licenses". dav1d, aom not mentioned. VERIFIED https://raw.githubusercontent.com/bigcat88/pillow_heif/master/LICENSES_bundled.txt (2026-11-21). So pillow-heif wheels contain GPL code (x265): do not use them in the image.
- The same README says pillow-heif wheels carry a fixed libheif; not named which version.

## 4. xlrd

- 2.0.2, released 2025-06-14, licence BSD, summary "extract data from Microsoft Excel (tm) .xls spreadsheet files". VERIFIED https://pypi.org/pypi/xlrd/json (2026-11-21).
- Classifiers list Python 2.7 and 3.6-3.9; requires_python `>=2.7` (excluding some 3.x). No 3.14 classifier; pure Python, so it likely works, but "supports 3.14" is UNVERIFIED (test in CI). VERIFIED metadata, https://pypi.org/project/xlrd/.
- "will no longer read anything other than .xls files" (the xlsx reader was removed in 2.0). VERIFIED https://pypi.org/project/xlrd/. Same page: password-protected files unsupported; macros/VBA/embedded objects ignored.
- Changelog: 2.0.2 (14 June 2025) fixes reading sheets with invalid formulae; no security fix mentioned for 2.0.x; older notes concern XML (xlsx) risks and defusedxml. VERIFIED https://github.com/python-excel/xlrd/blob/master/CHANGELOG.rst.
- Security of parsing untrusted .xls: a web search found no CVE for the Python xlrd; the CVEs found are for other libraries (libxls, C). SECONDARY (absence in a search is not proof). Pure Python: memory corruption unlikely; risks are exceptions, huge-allocation and CPU use on crafted files, so wrap with limits and timeouts (my engineering note, not a source).

## 5. RTF

- striprtf 0.0.35, uploaded 2026-10-24, BSD-3-Clause (license_expression), requires_python >=3.8; "convert RTF to plain text", `rtf_to_text(rtf, encoding="cp1252", errors=...)`. VERIFIED https://pypi.org/pypi/striprtf/json (2026-11-21).
- Table cells: not verified in the source (plain-text conversion; whether cell boundaries are kept unknown). UNVERIFIED; test with a synthetic RTF table.

## 6. Is LGPL "copyleft"?

- OSI page for LGPL-3.0 (does not use the word "copyleft"): the licence "incorporates the terms and conditions of version 3 of the GNU General Public License" plus extra permissions; a Combined Work may be conveyed under terms of your choice only if modification of the Library portions is not restricted. VERIFIED https://opensource.org/licenses/lgpl-3.0 (2026-11-21).
- FSF: the licence-list page said that the GNU GPL is "a free, copyleft license"; the LGPL is built on the GPL. The FSF essay "why not lgpl" would carry the "weaker copyleft" wording but the gnu.org pages returned HTTP 429 and I did not read it. So the FSF classification of LGPL itself is UNVERIFIED by me; SPDX page for LGPL-3.0-or-later has no copyleft classification (not found on https://spdx.org/licenses/LGPL-3.0-or-later.html). Secondary results (Wikipedia mirrors, MDN glossary) call it weak copyleft. SECONDARY.
- Reported classification only: LGPL is generally treated as a weak/lesser copyleft, not as the GPL. Whether the task card means to exclude it is a question for the owner/partner.

## Not verified / requests to lead

1. Real install closure and licences on Debian and Alpine (run `apt-get -s`, `apk` dry run, read copyright files in the image build); check libjbig0 and liblerc4 licences.
2. Run heif-dec on a synthetic HEIC with only the libde265 plugin.
3. Open the pi-heif wheel (`pi_heif.libs`) for bundled libraries; the safest choice is system libheif plus no Python wheel, or decode with `heif-dec` as a subprocess.
4. Owner decision: is LGPL (libheif, libde265) admitted under the task card? If not, no HEIC route on these bases is free of it.
5. Confirm xlrd on Python 3.14 in CI.
