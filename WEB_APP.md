# tryRB Web App

## Frontend

The GitHub Pages frontend is a static browser application in `index.html`. It uses the open-source `@imgly/background-removal` package through an ESM CDN and runs inference locally in the browser. The first run downloads the model assets; performance depends on the device, browser memory, and network speed.

### Local preview

Open `index.html` through a local static server (not `file://`), for example:

```bash
python -m http.server 8080
```

Then open `http://localhost:8080`.

## Python rembg engine

The repository also contains the Python `rembg` project and its Dockerfile. It can be run as a separate service on a machine or container host. The current web UI's optional server mode expects a CORS-enabled HTTP endpoint at `/api/remove` that accepts multipart form data with a `file` field and returns an image response. The upstream rembg server's API contract must be checked and adapted before connecting it; do not assume the endpoint is interchangeable.

## Current limitations

- GitHub Pages serves static files only. It does not run the Python package or host model inference.
- Browser inference is a first implementation, not a claim of PhotoRoom-equivalent quality. Test difficult hair, fur, transparent objects, motion blur, and low-contrast edges.
- Browser mode does not upload the selected photo to a tryRB server. Model files are fetched from the configured CDN.
- No server URL is preconfigured. A separately hosted backend requires deployment, CORS configuration, and endpoint compatibility work.
- Do not use unreviewed output for identity documents or other critical workflows.

## License and attribution

The existing Python `rembg` code retains its upstream MIT license and attribution. The web interface is a separate tryRB project addition. Review the upstream license and the browser-removal package license before redistributing a modified bundle.
