# Luna Body Pose and Object Detection Demo

Runs two AI inference pipelines simultaneously on the Luna SL1680, each fed by a separate USB camera. One pipeline detects objects and the other estimates human body pose keypoints. The outputs are displayed on the connected screen and can also be accessed remotely by opening a browser on the IP of the board.

## Requirements

- Luna SL1680
- 2x USB cameras (see [Camera compatibility](#camera-compatibility))
- HDMI cable + Micro-HDMI adapter
- 16:9 HDMI screen
- Heatsink (strongly recommended)

## Camera compatibility

Cameras share a USB 2.0 hub (480 Mbps total). Two cameras together must stay within ~384 Mbps of isochronous bandwidth, leaving roughly **192 Mbps per camera**.

| Format | Resolution | FPS | Bandwidth  | Compatible |
|--------|------------|-----|------------|------------|
| YUYV   | 640×480    | 30  | ~147 Mbps  | ✓ |
| YUYV   | 1280×720   | 30  | ~442 Mbps  | ✗ |
| MJPEG  | any        | 30  | 15–50 Mbps | ✓ |

## Setup

1. Plug both cameras into the USB ports on the hub.
2. Download `docker-compose.yml` to Luna.
3. Run:

```bash
docker compose up
```
