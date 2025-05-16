# Google OAuth Setup Instructions

To use the Google authentication feature in this application, you need to create OAuth 2.0 credentials:

1. Go to the [Google Cloud Console](https://console.cloud.google.com/)
2. Create a new project or select an existing one
3. Navigate to "APIs & Services" > "Credentials"
4. Click "Create Credentials" > "OAuth client ID"
5. Select "Desktop app" as the application type
6. Name your client ID (e.g., "Proxy GUI Client")
7. Click "Create"
8. Download the JSON file
9. Rename the downloaded file to `client_secret.json`
10. Place the file in the same directory as the application executable

The application will look for this file when you try to authenticate with Google.
