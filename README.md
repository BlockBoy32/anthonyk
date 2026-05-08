# anthonyk

A small static personal site, deployed automatically to GitHub Pages.

## Live site

After the first deploy succeeds, the site is available at:

```
https://<your-github-username>.github.io/anthonyk/
```

## How auto-deploy works

`.github/workflows/deploy.yml` runs on every push to `main` (and to the
current development branch). It uploads the repo as a Pages artifact and
publishes it via `actions/deploy-pages`. There is no build step — the
files at the repo root are served as-is.

## One-time setup (must be done in the GitHub UI)

1. Push this repo to GitHub.
2. Go to **Settings → Pages**.
3. Under **Build and deployment → Source**, select **GitHub Actions**.
4. Push to `main` (or run the workflow manually from the **Actions** tab).
   The site will be live in ~30 seconds.

## Using a custom domain

GitHub Pages supports custom domains with free HTTPS.

1. Add a file named `CNAME` at the repo root containing only your domain,
   e.g.:

   ```
   www.example.com
   ```

2. Configure DNS at your registrar:
   - **Apex domain** (`example.com`): create `A` records pointing to
     GitHub's Pages IPs:
     ```
     185.199.108.153
     185.199.109.153
     185.199.110.153
     185.199.111.153
     ```
   - **Subdomain** (`www.example.com`): create a `CNAME` record pointing
     to `<your-username>.github.io`.

3. In **Settings → Pages**, enter the custom domain and tick
   **Enforce HTTPS** once the certificate finishes provisioning (a few
   minutes after DNS propagates).

## Local preview

Just open `index.html` in a browser, or run any static server:

```
python3 -m http.server 8000
```
