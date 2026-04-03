# GitHub Pages Deployment Guide

## 🚀 Deployment Setup

This repository is configured to automatically deploy to GitHub Pages using GitHub Actions.

### Files Created:

1. **index.html** - Main landing page showcasing the Lex Amoris Ecosystem
2. **style.css** - Responsive styling for the website
3. **lex_amoris_ecosystem.py** - The Python implementation (downloadable from the site)
4. **.github/workflows/deploy.yml** - GitHub Actions workflow for automatic deployment

### How It Works:

The GitHub Actions workflow automatically deploys to GitHub Pages when:
- Code is pushed to the `main` or `copilot/deploy-github-pages` branch
- Manual trigger via "workflow_dispatch"

### Enabling GitHub Pages:

To enable GitHub Pages for this repository, you need to:

1. Go to your repository on GitHub
2. Click on **Settings**
3. Navigate to **Pages** in the left sidebar
4. Under **Build and deployment**:
   - Source: Select **GitHub Actions**
5. Save your settings

The workflow will automatically run and deploy your site.

### Accessing Your Site:

Once deployed, your site will be available at:
```
https://hannesmitterer.github.io/NSR-framework-/
```

### What Gets Deployed:

- The main landing page (index.html) with project information
- Styled with modern, responsive CSS
- The Python script available for download
- All content is static and loads instantly

### Updating the Site:

Simply push changes to the repository, and the workflow will automatically redeploy the site.

## 🔧 Local Development

To preview the site locally:

```bash
# Simple Python HTTP server
python -m http.server 8000

# Then visit http://localhost:8000 in your browser
```

## 📝 Notes:

- The workflow requires GitHub Pages to be enabled in repository settings
- The first deployment may take a few minutes
- Subsequent deployments are typically faster
- The site is static HTML/CSS/JS only (Python script is provided as download)
