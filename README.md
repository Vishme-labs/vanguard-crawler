# VanguardCrawler (vgcrawl)
Lightweight async web crawler and optional directory bruteforcer.

**Usage**

1. Install dependencies:
   ```bash
   python3 -m pip install -r requirements.txt
   ```
2. Run a crawl:
   ```bash
   python cli.py -u https://example.com -d 2 -o sitemap.json
   ```
3. Crawl with directory bruteforce (requires wordlist):
   ```bash
   python cli.py -u https://example.com -d 2 -o sitemap.json --bruteforce --wordlist ./wordlist.txt --bf-threads 30
   ```

**Important:** Only scan targets you own or have explicit permission to test.


## New: Port-check feature

- Use `--check-ports` to optionally check a range or list of ports on the target host to see if they are accepting TCP and serving HTTP(S) pages.
- Control ports via `--ports` (e.g., `--ports 1-1024` or `--ports 80,443,8080`). Default is `1-1024`.
- Use `--https-scan` to also try HTTPS when checking ports.

**Disclaimer:** Port checking may significantly slow down scans and should only be used against targets you own or have permission to test.
