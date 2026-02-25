# piMacroScreen

## Web Interface Authentication

- The web interface now requires login.
- Initial credentials are `admin` / `admin`.
- Passwords are not stored in plain text. A secure password hash is stored in `auth.json`.
- Change the password from the web UI via the `Change Password` button after login.
- Change the username from the web UI via the `Change Username` button (requires current password).