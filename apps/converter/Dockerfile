# The converter service: two images from one file (design 9).
#
#   docker build -f apps/converter/Dockerfile -t converter:core .            # target core (the default, the last stage)
#   docker build -f apps/converter/Dockerfile --target plus -t converter:plus .
#
# The build context is the REPOSITORY ROOT (the file is in apps/converter/, the context is "."). Every base image
# is pinned by digest (the index digest, so one line serves amd64 and arm64); to move to a newer base, change the
# digest, never use a tag alone. Nothing here downloads anything at start: the product calls nothing out.
# Python packages come from requirements.lock with hashes and wheels only: a missing wheel fails the build here.
#
# NOTE: nobody could build this file on the author's laptop (no Docker). CI (WP-F20) is the first real build.
# Digests read from the Docker Hub registry on 21 November 2026.

ARG PY_ALPINE=python:3.14-alpine@sha256:5862d971d1f0ae26b258cefa4e893556b1d3aba81bd2ff30888704ad378bab67
ARG PY_SLIM=python:3.14-slim-trixie@sha256:9aaa474097d094040649f2162a627c0049b408f52138d980916788d80f04802f
ARG NODE=node:22-alpine@sha256:1314fb30ec37592d5845e5a160d522c0e680972aa534549940b8d73bde88481a

# ---- front end -----------------------------------------------------------------------------------------------
# apps/review-web may not exist yet. The glob below matches nothing then; pyproject.toml is always there, so the
# COPY itself never fails. When the folder appears, its files land in /src and are built; until then /out is empty.
FROM ${NODE} AS ui
WORKDIR /src
COPY apps/converter/pyproject.toml apps/review-web*/ ./
RUN mkdir -p /out && \
    if [ -f package.json ]; then \
        if [ -f package-lock.json ]; then npm ci --no-audit --no-fund; else npm install --no-audit --no-fund; fi && \
        npm run build && cp -r dist/. /out/; \
    else \
        echo "apps/review-web is not present: the image is built without the front end" >&2; \
    fi

# ---- plus: Debian base (second OCR engine, OpenCV and Morfeusz have no wheel for Alpine) ---------------------
FROM ${PY_SLIM} AS plus
ENV PYTHONDONTWRITEBYTECODE=1 PYTHONUNBUFFERED=1 PYTHONUTF8=1 PIP_NO_CACHE_DIR=1 PIP_DISABLE_PIP_VERSION_CHECK=1
RUN apt-get update && \
    apt-get install -y --no-install-recommends tesseract-ocr tesseract-ocr-pol tesseract-ocr-eng && \
    rm -rf /var/lib/apt/lists/* && \
    useradd --system --uid 10001 --no-create-home --shell /usr/sbin/nologin converter
WORKDIR /srv/converter
COPY apps/converter/requirements.lock ./requirements.lock
RUN pip install --require-hashes --only-binary=:all: -r requirements.lock
COPY apps/converter/app ./app
COPY apps/converter/converter ./converter
# The pre-import gate (app.gate) needs the partner's linter and the form schemas where coi_lint looks for them:
# <root>/tools/coi_lint.py and <root>/contracts/coi/. Without them G1 and G2 fail closed.
COPY tools/coi_lint.py ./tools/coi_lint.py
COPY contracts/coi/form.schema.json contracts/coi/form.tolerant.schema.json ./contracts/coi/
COPY --from=ui /out ./ui
ENV PYTHONPATH=/srv/converter OCR_SECOND_ENGINE=on
USER 10001:10001
EXPOSE 8080
HEALTHCHECK --interval=30s --timeout=3s --retries=3 \
    CMD ["python", "-c", "import urllib.request,sys; sys.exit(0 if urllib.request.urlopen('http://127.0.0.1:8080/healthz', timeout=2).status == 200 else 1)"]
ENTRYPOINT ["python", "-m", "converter"]
CMD ["serve", "--host", "0.0.0.0", "--port", "8080"]

# ---- core: Alpine base, the image of the submission (LAST stage: the default target) --------------------------
FROM ${PY_ALPINE} AS core
ENV PYTHONDONTWRITEBYTECODE=1 PYTHONUNBUFFERED=1 PYTHONUTF8=1 PIP_NO_CACHE_DIR=1 PIP_DISABLE_PIP_VERSION_CHECK=1
RUN apk add --no-cache tesseract-ocr tesseract-ocr-data-pol tesseract-ocr-data-eng && \
    adduser -S -D -H -u 10001 -s /sbin/nologin converter
WORKDIR /srv/converter
COPY apps/converter/requirements.lock ./requirements.lock
RUN pip install --require-hashes --only-binary=:all: -r requirements.lock
COPY apps/converter/app ./app
COPY apps/converter/converter ./converter
# The pre-import gate (app.gate) needs the partner's linter and the form schemas where coi_lint looks for them:
# <root>/tools/coi_lint.py and <root>/contracts/coi/. Without them G1 and G2 fail closed.
COPY tools/coi_lint.py ./tools/coi_lint.py
COPY contracts/coi/form.schema.json contracts/coi/form.tolerant.schema.json ./contracts/coi/
COPY --from=ui /out ./ui
ENV PYTHONPATH=/srv/converter
# A dedicated user, one port, no secret in the image: keys come in as files (JWT_SECRET_FILE and the like).
USER 10001:10001
EXPOSE 8080
HEALTHCHECK --interval=30s --timeout=3s --retries=3 \
    CMD ["python", "-c", "import urllib.request,sys; sys.exit(0 if urllib.request.urlopen('http://127.0.0.1:8080/healthz', timeout=2).status == 200 else 1)"]
ENTRYPOINT ["python", "-m", "converter"]
CMD ["serve", "--host", "0.0.0.0", "--port", "8080"]
