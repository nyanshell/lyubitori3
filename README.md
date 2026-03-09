# fav_collector

Twitter/X favorites image crawler using Selenium Remote WebDriver.

Connects to a `selenium/standalone-chrome` Docker container via Selenium Grid, scrolls through a user's likes page, and downloads original-resolution images with metadata.

## Prerequisites

- Python 3.14+
- Docker container running `selenium/standalone-chrome` with VNC enabled
- Network route to the container (see [Network Setup](#network-setup))

## Setup

```bash
python -m venv .venv
source .venv/bin/activate
pip install -e .
cp .env.example .env
# Edit .env with your values
```

## Container Setup

### containerd / nerdctl

Create a macvlan CNI config at `/etc/cni/net.d/nerdctl-host-macvlan.conflist`:

```json
{
  "cniVersion": "1.0.0",
  "name": "host-macvlan",
  "nerdctlID": "host-macvlan",
  "nerdctlLabels": {},
  "plugins": [
    {
      "type": "macvlan",
      "master": "<NIC>",
      "mode": "bridge",
      "ipam": {
        "type": "host-local",
        "ranges": [
          [
            {
              "subnet": "<SUBNET>/24",
              "gateway": "<GATEWAY>"
            }
          ]
        ],
        "routes": [
          {
            "dst": "0.0.0.0/0"
          }
        ]
      }
    }
  ]
}
```

Then start the container:

```bash
nerdctl run -d \
  --name selenium-twitter \
  --net host-macvlan \
  --ip <CONTAINER_IP> \
  --shm-size="8g" \
  -v $(pwd)/chrome_profile:/home/seluser/.config/chrome \
  selenium/standalone-chrome:latest
```

### Host-to-Container Routing

With macvlan, the host cannot reach the container directly. Create a shim interface:

```bash
sudo ip link add host-shim link <NIC> type macvlan mode bridge
sudo ip addr add <HOST_SHIM_IP>/32 dev host-shim
sudo ip link set host-shim up
sudo ip route add <CONTAINER_IP>/32 dev host-shim
```

Replace `<NIC>` with your physical interface, `<CONTAINER_IP>` with the IP assigned above, and `<HOST_SHIM_IP>` with an unused IP on the same subnet.

## First Run

1. Start the container
2. Run the crawler: `dotenv run -- python -m fav_collector.cli`
3. Connect to VNC at `http://<CONTAINER_IP>:7900`
4. Log in to Twitter/X in the Chrome window opened by Selenium
5. Stop the script (Ctrl+C), then restart it - the login persists via `--user-data-dir`

## Usage

```bash
source .venv/bin/activate
dotenv run -- python -m fav_collector.cli --max-stale 100
```

Or via the installed entry point:

```bash
dotenv run -- fav-collector --max-stale 100
```

### CLI Options

```
--max-stale INT     Stop after N cycles with no new images (default: 5000)
--user TEXT         Twitter username (overrides TWITTER_USER env)
--downloads-dir PATH  Directory to save images (overrides DOWNLOADS_DIR env)
--scroll-min INT    Min scroll pixels per cycle (overrides SCROLL_PIXELS_MIN env)
--scroll-max INT    Max scroll pixels per cycle (overrides SCROLL_PIXELS_MAX env)
--log-level TEXT    Log level: DEBUG, INFO, WARNING, ERROR (overrides LOG_LEVEL env)
--help              Show help message
```

## Configuration

Copy the example and edit:

```bash
cp .env.example .env
```

Then edit `.env` with your values (this file is gitignored). See `.env.example` for all available environment variables.

## Output

Images are saved to `downloads/` with the naming pattern:

```
{author}_{tweet_id}_{timestamp}_{hash8}.{ext}
```

Each image has a companion `.json` file with metadata:

```json
{
    "author": "username",
    "tweet_id": "123456789",
    "time": "2026-03-01T14:39:17.000Z",
    "text": "tweet text",
    "url": "https://pbs.twimg.com/media/...",
    "hash": "md5hash",
    "download_time": 1772420307
}
```

## Cron Job

Run the crawler every 6 hours:

```bash
crontab -e
```

Add the following line:

```cron
0 */6 * * * /path/to/fav_collector_vnc/.venv/bin/dotenv -f /path/to/fav_collector_vnc/.env run -- /path/to/fav_collector_vnc/.venv/bin/python /path/to/fav_collector_vnc/fav_collector/cli.py --max-stale 100 --downloads-dir /path/to/fav_collector_vnc/downloads
```

## Linting

```bash
pip install ruff
ruff check fav_collector/
ruff format fav_collector/
```
