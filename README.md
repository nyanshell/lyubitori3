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
pip install selenium requests
cp settings.example.toml settings.toml
# Edit settings.toml with your values
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
2. Run the script: `python -m fav_collector`
3. Connect to VNC at `http://<CONTAINER_IP>:7900`
4. Log in to Twitter/X in the Chrome window opened by Selenium
5. Stop the script (Ctrl+C), then restart it - the login persists via `--user-data-dir`

## Usage

```bash
source .venv/bin/activate
python -m fav_collector
```

The crawler will:
- Attach to an existing Selenium session if one is active, or create a new one
- Navigate to the configured user's likes page
- Scroll down with human-like mouse movements (Bezier curves) and smooth scrolling
- Extract tweet images, clean URLs to original resolution, download and deduplicate by hash
- Save images and JSON metadata to `downloads/`
- Adaptively increase scroll distance when no new images are found

## Configuration

Copy the example and edit:

```bash
cp settings.example.toml settings.toml
```

Then edit `settings.toml` with your values (this file is gitignored):

```toml
[twitter]
user = "your_username"
```

See `settings.example.toml` for all available options.

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

## Linting

```bash
pip install ruff
ruff check fav_collector/
ruff format fav_collector/
```
