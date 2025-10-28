#!/usr/bin/env python3
import argparse
import asyncio
import sys
from vgcrawl.crawler import Crawler
from vgcrawl.sitemap import write_output

BANNER = r"""

 __     __                 _                            _ 
 \ \   / /__ _ __ _ __ ___| |__   __ _ ___  ___  ___   / |
  \ \ / / _ \ '__| '__/ _ \ '_ \ / _` / __|/ _ \/ __|  | |
   \ V /  __/ |  | | |  __/ |_) | (_| \__ \  __/\__ \  | |
    \_/ \___|_|  |_|  \___|_.__/ \__,_|___/\___||___/  |_|

             Vanguard by vishmeluck
"""

def parse_args():
    parser = argparse.ArgumentParser(prog="vgcrawl", description="VanguardCrawler (vgcrawl) - lightweight security crawler")
    parser.add_argument("-u", "--url", required=True, help="Root URL to crawl (e.g. https://example.com)")
    parser.add_argument("-d", "--depth", type=int, default=2, help="Max crawl depth (default 2)")
    parser.add_argument("-o", "--output", default="sitemap.json", help="Output file (ends with .json or .xml)")
    parser.add_argument("--concurrency", type=int, default=10, help="Number of concurrent requests (default 10)")
    parser.add_argument("--delay", type=float, default=0.0, help="Delay between requests in seconds (politeness)")
    parser.add_argument("--bruteforce", action="store_true", help="Enable directory bruteforce using a wordlist")
    parser.add_argument("--wordlist", help="Path to wordlist file for bruteforce (one entry per line)")
    parser.add_argument("--bf-threads", type=int, default=20, help="Concurrency for bruteforce (default 20)")
    parser.add_argument("--check-ports", action="store_true", help="Check a range/list of ports on the target host to see if they serve web pages (may slow scan)")
    parser.add_argument("--ports", default="1-1024", help="Ports to check — either a range like 1-1024 or comma-separated list like 80,443,8080 (default: 1-1024)")
    parser.add_argument("--https-scan", action="store_true", help="When checking ports, also try HTTPS (may increase time)")
    parser.add_argument("--verbose", action="store_true", help="Verbose output")
    return parser.parse_args()

def parse_ports_spec(spec):
    spec = spec.strip()
    ports = set()
    if not spec:
        return []
    parts = spec.split(',')
    for p in parts:
        if '-' in p:
            try:
                a,b = p.split('-',1)
                a = int(a); b = int(b)
                if a>b:
                    a,b = b,a
                ports.update(range(max(1,a), min(65535,b)+1))
            except Exception:
                continue
        else:
            try:
                ports.add(int(p))
            except Exception:
                continue
    # sort and return as list
    return sorted([p for p in ports if 1 <= p <= 65535])

async def main():
    args = parse_args()
    print(BANNER)
    print("Disclaimer: Enable port checks only if you have permission. Port scanning and checking for web pages may significantly slow down the scan.\n")
    if args.bruteforce and not args.wordlist:
        print("Error: --bruteforce requires --wordlist to be set", file=sys.stderr)
        sys.exit(2)

    ports_to_check = []
    if args.check_ports:
        ports_to_check = parse_ports_spec(args.ports)
        if not ports_to_check:
            print("No valid ports parsed from --ports; aborting.", file=sys.stderr)
            sys.exit(2)
        print(f"[info] Port-check enabled: {len(ports_to_check)} ports to test (this may slow the scan)")

    crawler = Crawler(root_url=args.url,
                      max_depth=args.depth,
                      concurrency=args.concurrency,
                      delay=args.delay,
                      verbose=args.verbose)

    await crawler.crawl()

    if args.bruteforce:
        await crawler.directory_bruteforce(args.wordlist, bf_concurrency=args.bf_threads)

    if args.check_ports:
        # perform port checks on the root host (and also any discovered hosts on same netloc)
        await crawler.check_ports(ports_to_check, try_https=args.https_scan)

    sitemap = crawler.get_sitemap()
    write_output(sitemap, args.output)
    print(f"Saved sitemap to {args.output}")

if __name__ == "__main__":
    asyncio.run(main())
