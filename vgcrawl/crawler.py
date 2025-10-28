import asyncio
import aiohttp
from aiohttp import ClientError, ClientSession
from tqdm.asyncio import tqdm
import time
from urllib.parse import urlparse
from .parser import extract_links
from .utils import normalize_url, same_domain, extract_params

class Crawler:
    def __init__(self, root_url, max_depth=2, concurrency=10, delay=0.0, verbose=False):
        self.root = root_url.rstrip("/")
        self.max_depth = max_depth
        self.seen = set()
        self.discovered = set()
        self.to_visit = asyncio.Queue()
        self.concurrency = concurrency
        self.delay = delay
        self.verbose = verbose
        self.session: ClientSession | None = None
        self._sem = asyncio.Semaphore(concurrency)
        self._parsed_root = urlparse(self.root).netloc
        # store status codes for endpoints (useful for bruteforce output)
        self.status_map = {}

    async def _fetch(self, url):
        async with self._sem:
            try:
                async with self.session.get(url, timeout=30, allow_redirects=True) as resp:
                    text = await resp.text(errors="ignore")
                    self.status_map[url] = resp.status
                    return resp.status, text
            except asyncio.TimeoutError:
                self.status_map[url] = "timeout"
                return None, None
            except ClientError as e:
                self.status_map[url] = f"error:{e}"
                return None, None
            finally:
                if self.delay:
                    await asyncio.sleep(self.delay)

    async def _worker(self):
        while True:
            try:
                url, depth = await asyncio.wait_for(self.to_visit.get(), timeout=1.0)
            except asyncio.TimeoutError:
                # queue empty-ish
                return
            if url in self.seen:
                self.to_visit.task_done()
                continue
            if depth > self.max_depth:
                self.to_visit.task_done()
                continue
            self.seen.add(url)
            if self.verbose:
                print(f"[crawl] depth={depth} url={url}")
            status, text = await self._fetch(url)
            if status is not None and text:
                links = extract_links(url, text)
                for l in links:
                    if same_domain(self.root, l):
                        if l not in self.seen:
                            await self.to_visit.put((l, depth + 1))
                    # add to discovered regardless of domain (useful)
                    self.discovered.add(l)
                # include the url itself
                self.discovered.add(url)
            self.to_visit.task_done()

    async def crawl(self):
        headers = {
            "User-Agent": "VGCrawl/0.1 (+https://github.com/<your-org>/vanguard-crawl) "
        }
        self.session = aiohttp.ClientSession(headers=headers)
        # seed
        await self.to_visit.put((self.root, 0))
        workers = [asyncio.create_task(self._worker()) for _ in range(self.concurrency)]
        # wait for workers to finish
        await asyncio.gather(*workers)
        await self.session.close()

    
async def _try_http_get(self, session, url):
    try:
        async with session.get(url, timeout=10, allow_redirects=True) as resp:
            return resp.status
    except Exception:
        return None

async def _tcp_connect(self, host, port, timeout=3):
    try:
        reader, writer = await asyncio.open_connection(host, port, limit=2**16)
        writer.close()
        try:
            await writer.wait_closed()
        except Exception:
            pass
        return True
    except Exception:
        return False

async def check_ports(self, ports, try_https=False, concurrency=200):
    """Check the provided ports on the crawler's root host (and discovered same-domain hosts).
    For each port that accepts a TCP connection we attempt an HTTP GET to see if it serves a web page.
    This is optional and can be slow for large port ranges. Results are added to discovered and status_map."""
    # gather unique hosts from root and discovered that match the root domain
    hosts = set()
    try:
        from urllib.parse import urlparse
    except Exception:
        urlparse = None
    # extract host(s) to test
    parsed_root = urlparse(self.root)
    hosts.add(parsed_root.hostname)
    for u in list(self.discovered):
        try:
            pu = urlparse(u)
            if pu.hostname and pu.hostname == parsed_root.hostname:
                hosts.add(pu.hostname)
        except Exception:
            continue

    print(f"[port-check] scanning {len(hosts)} host(s) on {len(ports)} ports each (may be slow)")
    sem = asyncio.Semaphore(concurrency)
    headers = {"User-Agent": "VGCrawl/0.1 (+port-check)"}
    async with aiohttp.ClientSession(headers=headers) as session:
        tasks = []
        for host in hosts:
            for p in ports:
                async def do_check(h, port):
                    async with sem:
                        up = await self._tcp_connect(h, port)
                        if not up:
                            return
                        # try HTTP
                        for scheme in (["http"] + (["https"] if try_https else [])):
                            url = f"{scheme}://{h}:{port}/"
                            status = await self._try_http_get(session, url)
                            if status and status not in (404, None):
                                entry = f"{url.rstrip('/')}{''}"
                                print(f"[port-check] {entry} -> {status}")
                                self.discovered.add(entry)
                                self.status_map[entry] = status
                                # once we find a page on this port, stop checking other scheme for same port
                                break
                tasks.append(asyncio.create_task(do_check(host, p)))
        # run tasks in batches with progress
        total = len(tasks)
        for f in tqdm(asyncio.as_completed(tasks), total=total):
            try:
                await f
            except Exception:
                pass

def get_sitemap(self):
        return {
            "root": self.root,
            "depth": self.max_depth,
            "discovered_urls": sorted(list(self.discovered)),
            "status_map": self.status_map
        }

    # Directory bruteforce: tries wordlist entries appended to target root or any discovered path
    async def _bf_fetch(self, session, url):
        try:
            async with session.get(url, timeout=15, allow_redirects=False) as resp:
                return resp.status
        except Exception:
            return None

    async def directory_bruteforce(self, wordlist_path, bf_concurrency=20):
        print(f"[bruteforce] loading wordlist: {wordlist_path}")
        try:
            with open(wordlist_path, "r", encoding="utf-8") as f:
                words = [w.strip() for w in f if w.strip()]
        except Exception as e:
            print(f"Failed to open wordlist: {e}")
            return

        # targets: root + discovered directories (only paths from same domain)
        base_targets = {self.root}
        for u in list(self.discovered):
            try:
                parsed = urlparse(u)
                if parsed.netloc == self._parsed_root:
                    # build base path (scheme + netloc + path w/o filename)
                    path = parsed.path
                    if path.endswith("/"):
                        base = f"{parsed.scheme}://{parsed.netloc}{path}"
                    else:
                        # remove last segment to bruteforce directories
                        base = f"{parsed.scheme}://{parsed.netloc}{'/'.join(path.split('/')[:-1])}/"
                    base_targets.add(base.rstrip("/"))
            except Exception:
                continue

        print(f"[bruteforce] Targets: {len(base_targets)} bases, words: {len(words)}")
        headers = {
            "User-Agent": "VGCrawl/0.1 (+bruteforce)"
        }
        sem = asyncio.Semaphore(bf_concurrency)
        async with aiohttp.ClientSession(headers=headers) as session:
            tasks = []
            for base in base_targets:
                for w in words:
                    # skip obvious dots
                    if w.startswith("."):
                        continue
                    url = f"{base.rstrip('/')}/{w}"
                    # a small helper to wrap concurrency
                    async def do(u):
                        async with sem:
                            status = await self._bf_fetch(session, u)
                            if status and status not in (404, None):
                                # record discovered directory/file
                                print(f"[bf] {u} -> {status}")
                                self.discovered.add(u)
                                self.status_map[u] = status
                    tasks.append(asyncio.create_task(do(url)))
            # run tasks with progress
            for f in tqdm(asyncio.as_completed(tasks), total=len(tasks)):
                try:
                    await f
                except Exception:
                    pass
