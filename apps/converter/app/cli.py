"""Command line: `python -m converter convert FILE [--out FILE] [--report DIR]` and `python -m converter serve`.

`convert` runs the same guard and the same pipeline as the HTTP endpoint, without HTTP and without a token. It
works in a container with no network. After a conversion one line on stderr names the engine (`ENGINE: rules`).
Exit codes: 0 done, 2 the file was refused (problem JSON on stderr),
3 the configuration is inconsistent, 4 the file cannot be read from disk or the output cannot be written.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
import sys
from pathlib import Path

from app import __version__, engine, pipeline
from app.config import ConfigError, Settings
from app.guard import ProblemError, inspect_upload


def _settings(no_auth: bool = False) -> Settings:
    env = dict(os.environ)
    if no_auth:  # the command line has no HTTP and so no token: it must not demand a key
        env["AUTH_MODE"] = "off"
    return Settings.from_env(env)


def cmd_convert(args: argparse.Namespace) -> int:
    try:
        s = _settings(no_auth=True)
    except ConfigError as exc:
        print("Configuration refused:\n  " + "\n  ".join(exc.problems), file=sys.stderr)
        return 3
    path = Path(args.file)
    try:
        if path.stat().st_size > s.max_upload_bytes:  # the size is judged before the file is read into memory
            raise ProblemError("TOO_LARGE", f"Plik przekracza {s.max_upload_bytes} bajtów.",
                               limits={"max_upload_bytes": s.max_upload_bytes})
        data = path.read_bytes()
    except OSError as exc:
        print(f"Cannot read the file: {exc.strerror}", file=sys.stderr)
        return 4
    except ProblemError as exc:
        print(json.dumps(exc.body(), ensure_ascii=False), file=sys.stderr)
        return 2
    try:
        info = inspect_upload(path.name, data, s)
        result = pipeline.run(data, info.name, s, **({"notes": info.warnings} if info.warnings else {}))
    except ProblemError as exc:
        print(json.dumps(exc.body(), ensure_ascii=False), file=sys.stderr)
        return 2
    form_text = json.dumps(result.form, ensure_ascii=False, separators=(",", ":"))
    if args.out:
        try:
            Path(args.out).write_text(form_text, encoding="utf-8")
        except OSError as exc:
            return _cannot_write(args.out, exc)
    else:
        sys.stdout.write(form_text + "\n")
    if args.report:
        folder = Path(args.report)
        meta = dict(result.sidecar)
        meta["input_sha256"] = info.sha256
        meta["form_sha256"] = hashlib.sha256(form_text.encode("utf-8")).hexdigest()
        try:
            folder.mkdir(parents=True, exist_ok=True)
            (folder / f"{path.stem}.meta.json").write_text(json.dumps(meta, ensure_ascii=False, indent=2), encoding="utf-8")
        except OSError as exc:
            return _cannot_write(args.report, exc)
    # The engine goes to standard error, never to standard output: standard output is the form JSON and nothing else.
    print(engine.cli_line(engine.engine_of(result.sidecar)), file=sys.stderr)
    return 0


def _cannot_write(target: str, exc: OSError) -> int:
    """One line and exit code 4, no stack trace. The usual cause is a folder mounted into the container that the
    container's user may not write (review D19, B3), hence the hint."""
    print(f'Cannot write {target}: {exc.strerror or type(exc).__name__}. On Linux add --user "$(id -u):$(id -g)"',
          file=sys.stderr)
    return 4


def cmd_serve(args: argparse.Namespace) -> int:
    try:
        s = _settings()
    except ConfigError as exc:
        print("Configuration refused:\n  " + "\n  ".join(exc.problems), file=sys.stderr)
        return 3
    import copy

    import uvicorn
    from uvicorn.config import LOGGING_CONFIG

    from app.main import create_app

    # The service's own lines (logger `converter`: the engine at start, one content-free line per conversion) go
    # where the server's lines go. Without this the logger has no handler and everything below a warning is lost.
    log_config = copy.deepcopy(LOGGING_CONFIG)
    log_config["loggers"]["converter"] = {"handlers": ["default"], "level": s.log_level.upper(), "propagate": False}
    uvicorn.run(create_app(s), host=args.host, port=args.port, log_level=s.log_level, access_log=False,
                log_config=log_config)
    return 0


def main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser(prog="converter", description="Blank official form in, form JSON out.")
    p.add_argument("--version", action="version", version=__version__)
    sub = p.add_subparsers(dest="command", required=True)
    c = sub.add_parser("convert", help="convert one file")
    c.add_argument("file")
    c.add_argument("--out", help="write the form here instead of standard output")
    c.add_argument("--report", metavar="DIR", help="write the sidecar to DIR/<name>.meta.json")
    c.set_defaults(func=cmd_convert)
    v = sub.add_parser("serve", help="start the API and the front end")
    v.add_argument("--host", default="127.0.0.1", help="use 0.0.0.0 inside a container")
    v.add_argument("--port", type=int, default=8080)
    v.set_defaults(func=cmd_serve)
    args = p.parse_args(argv)
    return args.func(args)
