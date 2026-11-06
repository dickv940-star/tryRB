# tryRB Web App and Backend

## Frontend

`index.html` is a static browser interface suitable for GitHub Pages. Browser mode first tries BiRefNet Lite through WebGPU/WebGL. If GPU context creation fails, the worker automatically falls back to `@imgly/background-removal` using its ISNet quantized model on CPU/WebAssembly. The fallback runs locally, downloads model/runtime assets from the IMG.LY CDN, and may be slower with different edge detail than BiRefNet. First-run download and inference time depend on device memory, browser support, and network.

## Authenticated Python backend

The repository's original upload contains the rembg README and packaging metadata but not the Python `rembg/` package source directory. The API therefore installs the official `rembg[cpu]` distribution from PyPI rather than trying to install a missing local package.

The custom `server.py` API:
- requires a bearer token of at least 24 characters;
- uses an explicit CORS origin allowlist;
- accepts only JPG, PNG, and WEBP;
- limits upload size and image pixel count;
- restricts selectable model names to models available in the installed rembg release;
- serializes CPU inference to reduce memory pressure;
- reuses loaded model sessions;
- returns PNG output.

### Run locally with Docker Desktop

1. Copy `.env.example` to `.env`.
2. Generate a token with `python -c "import secrets; print(secrets.token_urlsafe(32))"` and put it in `TRYRB_API_TOKEN`.
3. Keep `ALLOWED_ORIGINS=http://localhost:8080,http://127.0.0.1:8080` for local frontend testing.
4. Run `docker compose up --build -d`.
5. Check `http://localhost:7000/health`.
6. In another terminal, run `python -m http.server 8080` from the repository root.
7. Open `http://localhost:8080`, choose **Server rembg**, set API URL to `http://localhost:7000`, and enter the token.

The Docker Compose port is bound to localhost only. The `tryrb-models` volume caches model weights across restarts. The first request for a model downloads its weights.

### Use with GitHub Pages

The public Pages site is HTTPS and cannot call a local HTTP backend from a normal browser context. A separately hosted backend must have a public HTTPS address. Set `ALLOWED_ORIGINS` to the exact Pages origin and expose the service only through a trusted HTTPS reverse proxy or tunnel. Do not expose port 7000 directly to the internet. The API requires authentication but should still be placed behind a secure ingress.

## Edge refinement

The server UI offers:
- **Decontamination** (default): estimates foreground color to reduce old-background color fringes on soft edges. It changes edge color, not mask coverage.
- **ViTMatte**: refines soft alpha detail; it takes precedence over alpha matting and is slower. Rembg then performs foreground-color recovery in this path.
- **Alpha matting**: alternative alpha refinement; decontamination is ignored when alpha matting is active.

BiRefNet General is the default model; BiRefNet Portrait is available for people and hair. BRIA RMBG is an optional model, but model-weight licensing is separate from the rembg package license. Check the BRIA model license before commercial use.

## Performance and quality limits

- GitHub Pages hosts only the static frontend; it does not run Python inference.
- The backend is CPU-only in this Docker configuration. Large images may take time; first-use model downloads add latency.
- ViTMatte needs extra model files and is substantially slower. It is optional, not a default.
- No claim of PhotoRoom-equivalent quality is made until the same representative photos are tested side by side.
- Preserve the original upload separately; the PNG output is newly encoded by the inference pipeline.

## Licensing

The rembg Python package is MIT-licensed, but model weights have separate licenses. The browser fallback dependency `@imgly/background-removal` is AGPL-3.0 according to its upstream repository. Review the AGPL obligations before commercial redistribution or network deployment. This is a technical note, not legal advice.
