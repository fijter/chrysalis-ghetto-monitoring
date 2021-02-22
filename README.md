# Chrysalis ghetto monitoring

Simple Python script to monitor Chrysalis testnet and report to Slack on issues.

**Note that this is a quick hacky way to monitor and is probably not the best solution for this,
it was very quick to build though ;)**

## Setup

- Create a virtual environment (`python -mvenv env`)
- Source the virtual environment (`source env/bin/activate`)
- Install the dependancies (`pip install -r requirements.txt`)
- Copy `.env.example` to `.env` and fill in the Slack webhook
- Test run the script (`python monitor.py`)

If this all works correctly you can just run this in a 5 minute or so crontab:

`sudo crontab -e`

`*/5 * * * * /path/to/dir/env/bin/python /path/to/dir/monitor.py`

