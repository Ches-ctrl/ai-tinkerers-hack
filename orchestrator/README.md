# Contact Orchestrator API

Receives contact data from iPhone Shortcuts app and orchestrates LinkedIn connections.

## Setup

1. Install dependencies:
```bash
pip install -r requirements.txt
```

2. Run the orchestrator:
```bash
python app.py
```
The API will run on `http://localhost:8000`

3. Expose with ngrok:
```bash
ngrok http 8000
```

## iPhone Shortcuts Integration

### Endpoint
`POST https://your-ngrok-url.ngrok.io/api/contact`

### Request Format
```json
{
  "first_name": "John",
  "last_name": "Doe",
  "phone_numbers": ["+1234567890"],
  "emails": ["john.doe@example.com"],
  "urls": ["https://www.linkedin.com/in/johndoe/"]
}
```

### Shortcuts App Configuration
1. Create a new Shortcut
2. Add "Get Contents of URL" action
3. Set URL to your ngrok endpoint
4. Set Method to POST
5. Add Headers: `Content-Type: application/json`
6. Set Request Body to JSON with the contact fields

## Features

- **Automatic JSON Storage**: Saves all contacts to `data/` directory
- **LinkedIn Integration**: Automatically triggers connection if LinkedIn URL provided
- **Contact Management**: List, view, and manually trigger LinkedIn connections
- **Background Processing**: LinkedIn connections happen asynchronously

## API Endpoints

- `POST /api/contact` - Receive contact from Shortcuts
- `GET /api/contacts` - List all saved contacts
- `GET /api/contact/{id}` - Get specific contact
- `POST /api/trigger-linkedin/{id}` - Manually trigger LinkedIn connection
- `GET /health` - Health check

## Running with LinkedIn Worker

1. Start LinkedIn worker first (port 8001):
```bash
cd ../linkedin-worker
python app.py
```

2. Then start orchestrator:
```bash
python app.py
```

3. Set environment variable for LinkedIn API:
```bash
export LINKEDIN_API_URL=http://localhost:8001
```

## Data Storage

Contacts are saved as JSON files in the `data/` directory with timestamps:
- Filename format: `contact_YYYYMMDD_HHMMSS_MS.json`
- Each file contains full contact data plus timestamp and unique ID