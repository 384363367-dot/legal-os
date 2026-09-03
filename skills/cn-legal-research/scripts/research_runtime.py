"""Small, dependency-free runtime shared by the public source adapters."""
from __future__ import annotations

import base64
import hashlib
import json
import mimetypes
import re
import ssl
import time
import urllib.error
import urllib.parse
import urllib.request
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Mapping

from source_registry import OfficialSource, official_source_for_url, source_for_id


class SourceBoundaryError(ValueError):
    """Raised when a request would leave the registered official-source boundary."""


class SourceAccessError(RuntimeError):
    """Raised for a source response that cannot be treated as a verified result."""


class RequestAuditLog:
    """Optional JSON-lines request log; no path is selected implicitly."""

    def __init__(self, path: Path | str | None = None) -> None:
        self.path = Path(path).expanduser().resolve() if path else None

    def write(self, event: str, **fields: object) -> None:
        if self.path is None:
            return
        self.path.parent.mkdir(parents=True, exist_ok=True)
        payload = {"event": event, "at": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())}
        payload.update(fields)
        with self.path.open("a", encoding="utf-8") as stream:
            stream.write(json.dumps(payload, ensure_ascii=False, sort_keys=True) + "\n")


@dataclass(frozen=True)
class SourceResponse:
    status: int
    url: str
    headers: dict[str, str]
    content: bytes

    @property
    def text(self) -> str:
        content_type = self.headers.get("content-type", "")
        charset_match = re.search(r"charset=([\w.-]+)", content_type, flags=re.I)
        encoding = charset_match.group(1) if charset_match else "utf-8"
        try:
            return self.content.decode(encoding, errors="replace")
        except LookupError:
            return self.content.decode("utf-8", errors="replace")

    def json(self) -> Any:
        return json.loads(self.text)


class RateLimiter:
    """Serialize requests and enforce a caller-selected maximum request rate."""

    def __init__(self, requests_per_second: float | None = 2.0) -> None:
        if requests_per_second is not None and requests_per_second < 0:
            raise ValueError("requests_per_second must be non-negative or None")
        self.requests_per_second = requests_per_second
        self._last_request = 0.0

    def wait(self) -> None:
        if not self.requests_per_second:
            return
        minimum_interval = 1.0 / self.requests_per_second
        elapsed = time.monotonic() - self._last_request
        if elapsed < minimum_interval:
            time.sleep(minimum_interval - elapsed)
        self._last_request = time.monotonic()


class CacheStore:
    """An opt-in byte cache; no default directory is ever selected."""

    def __init__(self, root: Path | str, namespace: str) -> None:
        self.root = Path(root).expanduser().resolve()
        self.namespace = re.sub(r"[^a-zA-Z0-9._-]+", "-", namespace).strip("-") or "source"
        (self.root / self.namespace).mkdir(parents=True, exist_ok=True)

    def _path(self, key: str) -> Path:
        digest = hashlib.sha256(key.encode("utf-8")).hexdigest()
        return self.root / self.namespace / f"{digest}.json"

    def get(self, key: str, max_age: float | None = None) -> SourceResponse | None:
        path = self._path(key)
        try:
            payload = json.loads(path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError):
            return None
        try:
            if max_age is not None and time.time() - float(payload.get("saved_at", 0)) > max_age:
                return None
        except (TypeError, ValueError):
            return None
        try:
            return SourceResponse(
                int(payload["status"]),
                str(payload["url"]),
                {str(k): str(v) for k, v in payload.get("headers", {}).items()},
                base64.b64decode(payload["content"]),
            )
        except (KeyError, ValueError, TypeError):
            return None

    def put(self, key: str, response: SourceResponse) -> None:
        payload = {
            "saved_at": time.time(),
            "status": response.status,
            "url": response.url,
            "headers": response.headers,
            "content": base64.b64encode(response.content).decode("ascii"),
        }
        self._path(key).write_text(json.dumps(payload, ensure_ascii=False), encoding="utf-8")

    def stats(self) -> dict[str, int]:
        files = list((self.root / self.namespace).glob("*.json"))
        return {"entries": len(files), "bytes": sum(path.stat().st_size for path in files if path.is_file())}

    def clear(self) -> int:
        removed = 0
        for path in (self.root / self.namespace).glob("*.json"):
            if path.is_file():
                path.unlink()
                removed += 1
        return removed


def _query_url(url: str, params: Mapping[str, object] | None) -> str:
    if not params:
        return url
    pairs: list[tuple[str, str]] = []
    for key, value in params.items():
        if value is None:
            continue
        if isinstance(value, (list, tuple)):
            pairs.extend((str(key), str(item)) for item in value)
        else:
            pairs.append((str(key), str(value)))
    if not pairs:
        return url
    parsed = urllib.parse.urlsplit(url)
    existing = urllib.parse.parse_qsl(parsed.query, keep_blank_values=True)
    query = urllib.parse.urlencode(existing + pairs)
    return urllib.parse.urlunsplit((parsed.scheme, parsed.netloc, parsed.path, query, parsed.fragment))


def _header_map(headers: Mapping[str, object] | None) -> dict[str, str]:
    result = {"Accept": "application/json, text/html;q=0.9, */*;q=0.1", "User-Agent": "LegalOS-public-cn-legal-research/0.1"}
    for key, value in (headers or {}).items():
        if key.lower() in {"authorization", "cookie", "proxy-authorization"}:
            raise SourceBoundaryError(f"credential-bearing header is not accepted: {key}")
        result[str(key)] = str(value)
    return result


def _content_disposition_filename(headers: Mapping[str, str]) -> str | None:
    value = next((v for k, v in headers.items() if k.lower() == "content-disposition"), "")
    encoded = re.search(r"filename\*=UTF-8''([^;]+)", value, flags=re.I)
    if encoded:
        return urllib.parse.unquote(encoded.group(1)).strip('"')
    plain = re.search(r"filename\s*=\s*\"?([^\";]+)", value, flags=re.I)
    return plain.group(1).strip() if plain else None


class OfficialClient:
    """HTTPS client constrained to one registered official source."""

    def __init__(
        self,
        source: str | OfficialSource,
        *,
        cache_dir: Path | str | None = None,
        no_cache: bool = False,
        requests_per_second: float | None = 2.0,
        timeout: int = 30,
        opener: urllib.request.OpenerDirector | Any | None = None,
        max_bytes: int = 50 * 1024 * 1024,
        retry_attempts: int = 2,
        retry_backoff: float = 1.0,
        log_file: Path | str | None = None,
    ) -> None:
        self.source = source_for_id(source) if isinstance(source, str) else source
        self.timeout = timeout
        self.max_bytes = max_bytes
        self.retry_attempts = max(0, min(int(retry_attempts), 5))
        self.retry_backoff = max(0.0, float(retry_backoff))
        self.audit_log = RequestAuditLog(log_file)
        self.limiter = RateLimiter(requests_per_second)
        self.cache = None if no_cache or cache_dir is None else CacheStore(cache_dir, self.source.id)
        if opener is not None:
            self.opener = opener
        else:
            context = ssl.create_default_context()
            self.opener = urllib.request.build_opener(urllib.request.HTTPSHandler(context=context))

    def validate_url(self, url: str) -> str:
        source = official_source_for_url(url)
        if source is None:
            raise SourceBoundaryError(f"URL is not a registered HTTPS official source: {url}")
        if source.id != self.source.id:
            raise SourceBoundaryError(f"URL belongs to {source.id}, expected {self.source.id}")
        return url

    def request(
        self,
        method: str,
        url: str,
        *,
        params: Mapping[str, object] | None = None,
        data: bytes | str | Mapping[str, object] | None = None,
        headers: Mapping[str, object] | None = None,
        cache_age: float | None = None,
        max_bytes: int | None = None,
    ) -> SourceResponse:
        method = method.upper()
        request_url = _query_url(self.validate_url(url), params)
        request_headers = _header_map(headers)
        body: bytes | None
        if isinstance(data, Mapping):
            body = json.dumps(data, ensure_ascii=False).encode("utf-8")
            request_headers.setdefault("Content-Type", "application/json; charset=utf-8")
        elif isinstance(data, str):
            body = data.encode("utf-8")
        else:
            body = data
        cache_key = method + "\n" + request_url + "\n" + (body or b"").decode("utf-8", errors="replace")
        if self.cache is not None:
            cached = self.cache.get(cache_key, cache_age)
            if cached is not None:
                self.audit_log.write("cache_hit", method=method, url=request_url, status=cached.status, bytes=len(cached.content))
                return cached

        request = urllib.request.Request(request_url, data=body, headers=request_headers, method=method)
        retryable = {408, 429, 500, 502, 503, 504}
        for attempt in range(self.retry_attempts + 1):
            self.limiter.wait()
            try:
                with self.opener.open(request, timeout=self.timeout) as response:
                    final_url = response.geturl()
                    self.validate_url(final_url)
                    limit = max_bytes or self.max_bytes
                    content = response.read(limit + 1)
                    if len(content) > limit:
                        raise SourceAccessError(f"source response exceeds {limit} bytes")
                    status = getattr(response, "status", None)
                    if status is None:
                        status = response.getcode()
                    result = SourceResponse(
                        int(status),
                        final_url,
                        {str(k).lower(): str(v) for k, v in response.headers.items()},
                        content,
                    )
                    self.audit_log.write("response", method=method, url=final_url, status=result.status, bytes=len(content), attempt=attempt)
                    if self.cache is not None:
                        self.cache.put(cache_key, result)
                    return result
            except urllib.error.HTTPError as exc:
                detail = exc.read(1024).decode("utf-8", errors="replace")
                self.audit_log.write("http_error", method=method, url=request_url, status=exc.code, attempt=attempt)
                if exc.code in retryable and attempt < self.retry_attempts:
                    retry_after = exc.headers.get("Retry-After") if exc.headers else None
                    try:
                        delay = min(60.0, max(0.0, float(retry_after))) if retry_after else self.retry_backoff * (2**attempt)
                    except ValueError:
                        delay = self.retry_backoff * (2**attempt)
                    time.sleep(delay)
                    continue
                raise SourceAccessError(f"official source HTTP {exc.code}: {detail[:200]}") from exc
            except urllib.error.URLError as exc:
                self.audit_log.write("url_error", method=method, url=request_url, error=str(exc.reason), attempt=attempt)
                if attempt < self.retry_attempts:
                    time.sleep(self.retry_backoff * (2**attempt))
                    continue
                raise SourceAccessError(f"official source request failed: {exc.reason}") from exc
        raise SourceAccessError("official source request exhausted retry budget")

    def json_request(self, method: str, url: str, **kwargs: object) -> Any:
        return self.request(method, url, **kwargs).json()

    def download(
        self,
        url: str,
        output: Path | str,
        *,
        output_root: Path | str | None = None,
        max_bytes: int | None = None,
    ) -> dict[str, object]:
        path = Path(output).expanduser()
        if output_root is not None:
            root = Path(output_root).expanduser().resolve()
            path = path if path.is_absolute() else root / path
            path = path.resolve()
            try:
                path.relative_to(root)
            except ValueError as exc:
                raise SourceBoundaryError("download output escapes output_root") from exc
        else:
            path = path.resolve()
        response = self.request("GET", url, max_bytes=max_bytes)
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(response.content)
        return {
            "path": str(path),
            "url": response.url,
            "bytes": len(response.content),
            "content_type": response.headers.get("content-type", mimetypes.guess_type(str(path))[0] or ""),
            "filename": _content_disposition_filename(response.headers),
        }


def clean_text(value: object) -> str:
    return re.sub(r"\s+", " ", str(value or "")).strip()


def safe_filename(value: str, fallback: str = "download") -> str:
    value = clean_text(value)
    value = re.sub(r"[^0-9A-Za-z一-龥._-]+", "_", value).strip("._")
    return value[:160] or fallback


def write_json(path: Path | str, payload: object) -> Path:
    destination = Path(path).expanduser().resolve()
    destination.parent.mkdir(parents=True, exist_ok=True)
    destination.write_text(json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return destination
