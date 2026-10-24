#!/usr/bin/env python3
# ==============================================================================
# Pre-build qutebrowser's Brave adblock cache from brave-lists.txt
# ==============================================================================
# qutebrowser normally asks the user to run `:adblock-update` before the
# adblock engine has any rules. This helper does the same work at install
# time, so ads are blocked on the very first launch.
#
# It downloads the exact list catalog configured for qutebrowser and serializes
# an adblock-rust engine to qutebrowser's `adblock-cache.dat`. The format is
# produced by the same `adblock` Python package qutebrowser uses.
# ==============================================================================
import argparse
import concurrent.futures
import hashlib
import os
import pathlib
import sys
import time
import urllib.request

USER_AGENT = (
    "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 "
    "(KHTML, like Gecko) Chrome/141.0.0.0 Safari/537.36"
)
MAX_CACHE_AGE = 12 * 60 * 60  # seconds


def read_lists(path):
    lists = []
    for line in path.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if line and not line.startswith("#"):
            lists.append(line)
    return lists


def fetch(url, cache_dir, refresh=False):
    """Download a list, reusing a recent copy from cache_dir."""
    name = hashlib.sha256(url.encode()).hexdigest()[:20] + ".txt"
    target = cache_dir / name
    if not refresh and target.is_file():
        if time.time() - target.stat().st_mtime < MAX_CACHE_AGE:
            return target.read_text(encoding="utf-8", errors="replace")
    request = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})
    with urllib.request.urlopen(request, timeout=90) as response:
        data = response.read()
    text = data.decode("utf-8", errors="replace")
    target.write_text(text, encoding="utf-8")
    return text


def main():
    home = pathlib.Path.home()
    xdg_config = pathlib.Path(os.environ.get("XDG_CONFIG_HOME", home / ".config"))
    xdg_data = pathlib.Path(os.environ.get("XDG_DATA_HOME", home / ".local/share"))
    xdg_cache = pathlib.Path(os.environ.get("XDG_CACHE_HOME", home / ".cache"))

    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--lists",
        type=pathlib.Path,
        default=xdg_config / "qutebrowser" / "brave-lists.txt",
        help="brave-lists.txt to read (default: %(default)s)",
    )
    parser.add_argument(
        "--output",
        type=pathlib.Path,
        default=xdg_data / "qutebrowser" / "adblock-cache.dat",
        help="engine cache to write (default: %(default)s)",
    )
    parser.add_argument(
        "--download-cache",
        type=pathlib.Path,
        default=xdg_cache / "omarchy-qutebrowser" / "brave-adblock",
        help="where downloaded lists are cached (default: %(default)s)",
    )
    parser.add_argument(
        "--refresh",
        action="store_true",
        help="redownload every list instead of using the 12h cache",
    )
    args = parser.parse_args()

    try:
        import adblock
    except ImportError:
        print(
            "error: Python module 'adblock' is missing.\n"
            "Install Brave's engine with: sudo pacman -S python-adblock",
            file=sys.stderr,
        )
        return 2

    if not args.lists.is_file():
        print(f"error: list file not found: {args.lists}", file=sys.stderr)
        return 2
    urls = read_lists(args.lists)
    if not urls:
        print(f"error: no list URLs in {args.lists}", file=sys.stderr)
        return 2

    args.download_cache.mkdir(parents=True, exist_ok=True)
    args.output.parent.mkdir(parents=True, exist_ok=True)

    print(f"Downloading {len(urls)} filter lists (Brave catalog)...")
    contents = {}
    failures = []
    with concurrent.futures.ThreadPoolExecutor(max_workers=8) as pool:
        futures = {
            pool.submit(fetch, url, args.download_cache, args.refresh): url
            for url in urls
        }
        for future in concurrent.futures.as_completed(futures):
            url = futures[future]
            try:
                contents[url] = future.result()
                print(f"  ok   {url}")
            except Exception as exc:
                failures.append((url, exc))
                print(f"  FAIL {url}: {exc}", file=sys.stderr)

    if not contents:
        print("error: every filter-list download failed", file=sys.stderr)
        return 1

    filter_set = adblock.FilterSet()
    total_bytes = 0
    for url, text in contents.items():
        total_bytes += len(text)
        try:
            filter_set.add_filter_list(text)
        except Exception as exc:
            print(f"  parse error, skipping {url}: {exc}", file=sys.stderr)

    engine = adblock.Engine(filter_set)
    tmp = args.output.with_suffix(args.output.suffix + ".tmp")
    engine.serialize_to_file(str(tmp))
    tmp.replace(args.output)

    print(
        f"\nWrote {args.output} "
        f"({args.output.stat().st_size / 1_000_000:.1f} MB, "
        f"{len(contents)} lists, {total_bytes / 1_000_000:.1f} MB of rules)"
    )

    # Also write StevenBlack hosts for qutebrowser's hostblock component
    hosts_output = args.output.parent / "blocked-hosts"
    hosts_url = "https://raw.githubusercontent.com/StevenBlack/hosts/master/hosts"
    try:
        hosts_text = fetch(hosts_url, args.download_cache, args.refresh)
        hosts_tmp = hosts_output.with_suffix(hosts_output.suffix + ".tmp")
        hosts_tmp.write_text(hosts_text, encoding="utf-8")
        hosts_tmp.replace(hosts_output)
        print(f"Wrote {hosts_output} ({hosts_output.stat().st_size / 1_000_000:.1f} MB, hosts file)")
    except Exception as exc:
        print(f"warning: failed to download hosts file: {exc}", file=sys.stderr)

    if failures:
        print(f"warning: {len(failures)} list(s) failed to download; "
              "run `:adblock-update` later to retry", file=sys.stderr)
    return 0


if __name__ == "__main__":
    sys.exit(main())
