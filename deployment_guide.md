# How to Deploy "Universal AI Context Auditor" for Free

The easiest and best free way to deploy this application is using **Streamlit Cloud**.

## Prerequisites
1.  A **GitHub** account.
2.  Your project code pushed to a GitHub repository.

## Step-by-Step Guide

### 1. Prepare your Repository
Ensure your repository has the following files (which we have already created):
-   `app.py` (Your main application code)
-   `requirements.txt` (List of dependencies)

### 2. Push to GitHub
If you haven't already, push your code to a new GitHub repository.
```bash
git init
git add .
git commit -m "Initial commit"
# Create a new repo on GitHub, then:
git remote add origin <your-repo-url>
git push -u origin main
```

### 3. Deploy on Streamlit Cloud
1.  Go to [share.streamlit.io](https://share.streamlit.io/) and sign in with GitHub.
2.  Click **"New app"**.
3.  Select your repository, branch (usually `main`), and the main file path (`app.py`).
4.  Click **"Deploy!"**.

### 4. Configure Secrets (Crucial!)
Since we are using an API key, you **MUST** set it up in the cloud environment (do NOT commit your `.env` file to GitHub).

1.  Once the app is deploying (or after it fails due to missing key), go to your App's dashboard.
2.  Click the **Settings** menu (three dots) -> **Settings**.
3.  Go to the **Secrets** tab.
4.  Paste your API key in the TOML format:
    ```toml
    GOOGLE_API_KEY = "AIzaSyCQ2NXrIthrAaJfr_I1z33Pf1I8yxsRTuw"
    ```
5.  Click **Save**.

The app should now restart and work perfectly!
