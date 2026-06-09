import fcntl
import fnmatch
import glob
import json
import os
import re
import struct
import sys
import time
import threading
from utils.websockets import WebSockets
from synapRT.pipelines import pipeline

CAMERA_HUB_PATTERN = "platform-xhci-hcd.*.auto-usb-*"

def get_object_model():
    return "/usr/share/synap/models/object_detection/coco/model/yolov8s-640x384/model.synap"

def get_pose_model():
    return "/usr/share/synap/models/object_detection/body_pose/model/yolov8s-pose/model.synap"

_VIDIOC_QUERYCAP = 0x80685600
_V4L2_CAP_VIDEO_CAPTURE = 0x00000001

_V4L2_CAP_DEVICE_CAPS = 0x80000000

def _sysfs_id_path(dev):
    name = os.path.basename(dev)
    try:
        real = os.path.realpath(f"/sys/class/video4linux/{name}")
        # Capture the component immediately before /usb<N>/ — that's the host controller name
        m = re.search(
            r'/([^/]+)/usb(\d+)/(?:[^/]+/)*(\d+(?:-[\d.]+)+):(\d+\.\d+)/video4linux',
            real
        )
        if not m:
            return ""
        platform_name = m.group(1)
        bus_num = int(m.group(2)) - 1
        port_path = re.sub(r'^\d+-', '', m.group(3))
        config_iface = m.group(4)
        return f"platform-{platform_name}-usb-{bus_num}:{port_path}:{config_iface}"
    except Exception:
        return ""

def _is_capture_device(dev):
    try:
        with open(dev, 'rb') as f:
            buf = bytearray(104)
            fcntl.ioctl(f, _VIDIOC_QUERYCAP, buf)
            caps = struct.unpack_from('<I', buf, 84)[0]
            device_caps = struct.unpack_from('<I', buf, 88)[0]
            effective = device_caps if (caps & _V4L2_CAP_DEVICE_CAPS) else caps
            return bool(effective & _V4L2_CAP_VIDEO_CAPTURE)
    except Exception:
        return False

def find_cameras(count=2):
    print(f"Searching for {count} capture cameras on hub {CAMERA_HUB_PATTERN}...", flush=True)
    while True:
        found = []
        for dev in sorted(glob.glob('/dev/video*')):
            if (fnmatch.fnmatch(_sysfs_id_path(dev), CAMERA_HUB_PATTERN)
                    and _is_capture_device(dev)):
                found.append(dev)
                if len(found) == count:
                    print(f"Found cameras: {found}", flush=True)
                    return found
        print(f"Found {len(found)}/{count} cameras, retrying...", flush=True)
        time.sleep(1)

def main():
    if len(sys.argv) >= 3:
        cam_obj = sys.argv[1]
        cam_pose = sys.argv[2]
    elif len(sys.argv) == 2:
        cam_obj = sys.argv[1]
        cam_pose = cam_obj
    else:
        cam_obj, cam_pose = find_cameras(count=2)

    if cam_obj == cam_pose:
        print("⚠ Using the same camera for both pipelines — may fail on some platforms")
    else:
        print(f"Using two cameras:\n  Object: {cam_obj}\n  Pose:   {cam_pose}")

    ws_server = WebSockets(port=6789, index="./vision/index.html")
    ws_server.start()

    obj_results = None
    pose_results = None
    lock = threading.Lock()

    def handle_obj(results, inference_time):
        nonlocal obj_results
        with lock:
            obj_results = results

    def handle_pose(results, inference_time):
        nonlocal pose_results
        with lock:
            pose_results = results

    obj_pipe = pipeline(
        task="object-detection",
        model=get_object_model(),
        profile=True,
        handler=handle_obj
    )

    pose_pipe = pipeline(
        task="object-detection",
        model=get_pose_model(),
        profile=True,
        handler=handle_pose
    )

    print("Starting object pipeline...")
    threading.Thread(target=obj_pipe, args=(cam_obj,), daemon=True).start()

    time.sleep(2)

    print("Starting pose pipeline...")
    threading.Thread(target=pose_pipe, args=(cam_pose,), daemon=True).start()

    try:
        while True:
            merged = {"items": []}

            with lock:
                if obj_results and "items" in obj_results:
                    for item in obj_results["items"]:
                        item = dict(item)
                        item["source"] = "object"
                        merged["items"].append(item)

                if pose_results and "items" in pose_results:
                    for item in pose_results["items"]:
                        item = dict(item)
                        item["source"] = "pose"
                        merged["items"].append(item)

            if merged["items"]:
                ws_server.broadcast(json.dumps(merged))

            time.sleep(0.02)

    except KeyboardInterrupt:
        print("Stopping...")
        sys.exit(0)

if __name__ == "__main__":
    main()
