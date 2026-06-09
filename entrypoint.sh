#!/bin/sh

cd /app/examples
. .venv/bin/activate

UVC_QUIRKS=/sys/module/uvcvideo/parameters/quirks
ORIGINAL_QUIRKS=""

rebind_uvc() {
    for iface in /sys/bus/usb/drivers/uvcvideo/*/; do
        [ -e "$iface" ] || continue
        ifname=$(basename "$iface")
        echo "$ifname" > /sys/bus/usb/drivers/uvcvideo/unbind 2>/dev/null || true
        echo "$ifname" > /sys/bus/usb/drivers/uvcvideo/bind   2>/dev/null || true
    done
}

modprobe uvcvideo 2>/dev/null || true

if [ -f "$UVC_QUIRKS" ]; then
    ORIGINAL_QUIRKS=$(cat "$UVC_QUIRKS")
    echo 640 > "$UVC_QUIRKS"
    rebind_uvc
fi

cleanup() {
    if [ -n "$ORIGINAL_QUIRKS" ] && [ -f "$UVC_QUIRKS" ]; then
        echo "$ORIGINAL_QUIRKS" > "$UVC_QUIRKS" 2>/dev/null || true
        rebind_uvc
    fi
}

trap 'cleanup; kill "$PY_PID" 2>/dev/null' TERM INT

python3 -m vision.dual_models &
PY_PID=$!
wait "$PY_PID" || true
cleanup
