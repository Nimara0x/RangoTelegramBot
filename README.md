# Rango Telegram Bot 
This is a simple Telegram Bot that can swap using Rango's API.

### Run with docker:

```bash
docker-compose up -d
```

### Set up `.env`:

```dotenv
TOKEN='xxxx'  # your bot token here
RANGO_API_KEY='YourRangoApi'
RANGO_BASE_URL='https://api.rango.exchange/'
DEVELOPMENT='true' # For testing
```

### Running Bot Locally
First install dependencies:
```bash
pip install -r src/requirements.txt
python src/main.py
```

Note that you need python +3.9 to run the project.