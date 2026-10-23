"""Boundary protection for a single-user, loopback-only research application."""
from urllib.parse import urlparse
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import JSONResponse
from app.core.config import get_settings

LOCAL_HOSTS = {'localhost', '127.0.0.1', '::1', 'testserver'}
ORIGINS = {f'http://{host}:{port}' for host in ('localhost', '127.0.0.1') for port in (5173, 8000, 8011)}
MAX_BODY = 2_100_000


class LocalBoundaryMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request, call_next):
        public_deployment = get_settings().public_deployment
        peer = request.client.host if request.client else ''
        if not public_deployment and peer not in {'127.0.0.1', '::1', 'testclient'}:
            return JSONResponse({'detail': 'This application is restricted to the local workstation.'}, 403)
        try:
            host = urlparse('http://' + request.headers.get('host', '')).hostname
        except ValueError:
            host = None
        if not public_deployment and host not in LOCAL_HOSTS:
            return JSONResponse({'detail': 'Untrusted Host header.'}, 400)
        origin = request.headers.get('origin')
        allowed_origins = set(get_settings().cors_origin_list) | ORIGINS
        if (origin and origin not in allowed_origins) or request.headers.get('sec-fetch-site') == 'cross-site':
            return JSONResponse({'detail': 'Cross-site API requests are not allowed.'}, 403)
        if request.method in {'POST', 'PUT', 'PATCH'}:
            try:
                size = int(request.headers.get('content-length', '0'))
            except ValueError:
                return JSONResponse({'detail': 'Invalid request length.'}, 400)
            if size < 0 or size > MAX_BODY:
                return JSONResponse({'detail': 'Request body exceeds the 2.1 MB transport limit.'}, 413)
            parts, total = [], 0
            async for chunk in request.stream():
                total += len(chunk)
                if total > MAX_BODY:
                    return JSONResponse({'detail': 'Request body exceeds the 2.1 MB transport limit.'}, 413)
                parts.append(chunk)
            # Starlette's cached request replays this body to downstream parsing.
            request._body = b''.join(parts)
        response = await call_next(request)
        response.headers['X-Content-Type-Options'] = 'nosniff'
        response.headers['X-Frame-Options'] = 'DENY'
        response.headers['Cache-Control'] = 'no-store'
        response.headers['Referrer-Policy'] = 'no-referrer'
        return response
