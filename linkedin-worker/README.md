# LinkedIn Connection Automation

A lightweight Python script that automates adding LinkedIn connections using Playwright with stealth mode.

## Setup

1. Install dependencies:
```bash
pip install -r requirements.txt
playwright install chromium
python -m playwright install
```

2. Configure credentials:
```bash
cp .env.example .env
# Edit .env with your LinkedIn credentials
```

## Usage

### Option 1: Run interactively
```bash
python linkedin_add_connection.py
```
Then uncomment and modify the examples in the main() function.

### Option 2: Use as a module
```python
from linkedin_add_connection import LinkedInAutomation

async def run():
    automation = LinkedInAutomation()
    await automation.setup_browser()
    await automation.login()

    # Add by profile URL
    await automation.add_connection(
        profile_url="https://www.linkedin.com/in/example/",
        message="Hi! I'd like to connect."
    )

    # Or search by name
    await automation.add_connection(
        name="John Doe",
        message="Hi! I'd like to connect."
    )

    await automation.close()
```

## Features

- **Headful mode**: Watch the automation in real-time
- **Stealth mode**: Uses tf-playwright-stealth to avoid detection
- **Two methods**: Add connections by profile URL or search by name
- **Custom messages**: Optionally include a personalized connection message
- **Security checkpoint handling**: Prompts for manual intervention if needed

## Important Notes

- The browser runs in headful mode so you can monitor the automation
- If LinkedIn presents a security challenge, the script will pause for manual completion
- Use responsibly and in accordance with LinkedIn's terms of service
