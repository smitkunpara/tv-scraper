# Publishing to PyPI

This guide explains how to publish the `tradingview-scraper` package to PyPI (Python Package Index) using **Trusted Publishing** (OIDC), which is the most secure and modern way to publish Python packages.

## 1. Create a PyPI Account
If you don't have one yet, create an account on [PyPI](https://pypi.org/account/register/).

## 2. Set Up Trusted Publishing (OIDC)
You do **not** need to create an API token or add secrets to your GitHub repository. Trusted Publishing uses GitHub's identity to authorize the upload.

1. Go to your [PyPI Projects](https://pypi.org/manage/projects/) (after your first upload) or go to [Publishing (under Account Settings)](https://pypi.org/manage/account/publishing/).
2. Click **Add a new publisher**.
3. Select **GitHub**.
4. Fill in the details:
   - **Owner**: `smitkunpara`
   - **Repository**: `tv_scraper`
   - **Workflow name**: `publish.yml`
   - **Environment name**: `pypi` (optional, but recommended if you use GitHub Environments)
5. Click **Add Publisher**.

## 3. Configure GitHub Environment (Optional but Recommended)
1. Go to your GitHub repository: `Settings` -> `Environments`.
2. Click **New environment** and name it `pypi`.
3. This adds an extra layer of security.

## 4. Trigger the Publish Workflow
To publish a new version:

1. **Update Version**: Change the `version` field in `pyproject.toml` (e.g., from `1.0.0` to `1.0.1`).
2. **Commit and Push**:
   ```bash
   git add pyproject.toml
   git commit -m "chore: bump version to 1.0.1"
   git push origin main
   ```
3. **Create a GitHub Release**:
   - Go to the **Releases** section on your GitHub repository.
   - Click **Draft a new release**.
   - Create a new tag (e.g., `v1.0.1`).
   - Fill in the release title and description.
   - Click **Publish release**.

The [Publish to PyPI](.github/workflows/publish.yml) workflow will start automatically, build the package using `uv`, and upload it to PyPI.

## ⚠️ Important Notes
- **Package Name**: Ensure `tradingview-scraper` isn't already taken on PyPI. If it is, you'll need to change the `name` in `pyproject.toml`.
- **First-time Publish**: For the very first publish, you might need to use a temporary API token or run the workflow manually once if PyPI doesn't let you set up OIDC before the project exists.
   - *Alternative*: If it's your first time, you can temporarily use an API token by reverting the `publish.yml` changes or following the PyPI "Pending Publisher" instructions.
- **Manual Publish**: If you ever need to publish manually from your local machine:
  ```bash
  uv build
  uv run twine upload dist/*
  ```
  (Requires `twine` to be installed and a PyPI token).
