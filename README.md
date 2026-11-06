# tryRB backend

Install Docker Desktop, copy `.env.example` to `.env`, then generate a private token:

```powershell
python -c "import secrets; print(secrets.token_urlsafe(32))"
```

Paste that value into `TRYRB_API_TOKEN` in `.env`. Keep `.env` private; never commit it.

For local development, keep the allowed origins as:
`http://localhost:8080,http://127.0.0.1:8080`.

Build and start the API:

```powershell
docker compose up --build -d
```

The API is bound to `127.0.0.1:7000` only. Check health at
`http://localhost:7000/health`.

Serve the static frontend locally from the repository folder:

```powershell
python -m http.server 8080
```

Open `http://localhost:8080`, select **Server rembg**, enter
`http://localhost:7000` and paste the same token.

The first request for each model downloads model weights. The Docker volume
`tryrb-models` preserves those files between container restarts.

## Connecting the public GitHub Pages frontend

A browser on the public HTTPS site cannot call a local HTTP endpoint. To use
the GitHub Pages frontend, the API needs a public HTTPS address. Configure
`ALLOWED_ORIGINS` to the exact Pages origin and expose the API only through a
secure HTTPS reverse proxy or tunnel. Do not expose port 7000 directly to the
internet. The API requires a bearer token and limits upload size, pixel count,
allowed models, and concurrent inference, but it should still be placed behind
a trusted HTTPS ingress.

## Edge-quality modes

- **Decontamination** is enabled by default. It targets colored halos on soft
  edges without changing mask coverage.
- **ViTMatte** is optional and slower; it refines soft alpha detail and uses
  foreground-color recovery in the rembg pipeline.
- **Alpha matting** is an alternative refinement mode. ViTMatte takes
  precedence if both options are enabled.

The general BiRefNet model is selected by default. Choose BiRefNet Portrait
for people/hair. BRIA RMBG is available as an optional model; check its model
license before commercial use.

## Important notes

- GitHub Pages serves only the frontend; the API must run on a separate host.
- CPU inference can be slow on large images. GPU acceleration needs compatible
  CUDA/ONNX Runtime hardware and a separate tested image.
- No claim of PhotoRoom-equivalent output is made until representative
  source photos have been tested side by side.
- The browser fallback uses `@imgly/background-removal`, whose upstream
  project is AGPL-3.0. Review the license obligations before commercial
  distribution or network deployment.
- The rembg Python package is MIT-licensed, but model weights have separate
  licenses. In particular, BRIA RMBG 2.0 has commercial-use restrictions;
  do not assume that the Python package's MIT license covers model weights.
