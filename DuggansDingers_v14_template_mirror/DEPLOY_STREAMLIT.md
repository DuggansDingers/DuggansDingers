# Put DuggansDingers online

1. Create a private GitHub repository and upload every project file except `.env`, cache folders, and real `secrets.toml` files.
2. Sign in to Streamlit Community Cloud with GitHub and create a new app.
3. Select the private repository, branch `main`, and main file `app.py`.
4. Open the app's **Settings > Secrets** and copy the variables from `.streamlit/secrets.toml.example`, replacing every placeholder with the real value from your local `.env` file.
5. Deploy and share the Streamlit URL. Friends can open it in Safari on iPhone and use **Share > Add to Home Screen**.

The app now requires a username and password before loading any baseball or sportsbook data.
