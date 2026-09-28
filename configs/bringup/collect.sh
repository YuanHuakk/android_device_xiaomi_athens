#!/system/bin/sh
# Read-only observation of Android startup. Logs stay on unencrypted metadata.
# At most four 1-MiB logcat files; two kernel snapshots; current service state.
OUT=/metadata/athens-diag/logs
umask 077
mkdir -p "$OUT" || exit 1
exec > "$OUT/collector.txt" 2>&1
echo "athens boot diagnostics v1"
cat /proc/uptime
cat /proc/bootconfig > "$OUT/bootconfig.txt"
dmesg > "$OUT/dmesg-initial.txt"
LOGPID=
finish() {
    [ -z "$LOGPID" ] || kill "$LOGPID" 2>/dev/null
    sync
}
trap finish EXIT
trap 'exit 0' HUP INT TERM
n=0
while [ "$n" -lt 180 ]; do
    if [ -z "$LOGPID" ] || ! kill -0 "$LOGPID" 2>/dev/null; then
        /system/bin/logcat -b all -v threadtime -f "$OUT/logcat.txt" -r 1024 -n 3 &
        LOGPID=$!
    fi
    if [ "$((n % 5))" -eq 0 ]; then
        getprop > "$OUT/properties.txt"
        cat /proc/mounts > "$OUT/mounts.txt"
        ps -A -o USER,PID,PPID,NAME,ARGS > "$OUT/processes.txt"
        {
            echo "--- uptime ---"
            cat /proc/uptime
            for prop in sys.boot_completed init.svc.zygote init.svc.bootanim \
                init.svc.adbd sys.usb.config sys.usb.state apexd.status \
                keystore.module_hash.sent odsign.key.done odsign.verification.done \
                arm64.memtag.bootctl_loaded; do
                echo "$prop=$(getprop "$prop")"
            done
            echo "init wchan/stack:"
            cat /proc/1/wchan /proc/1/stack
            echo "available metadata:"
            df -k /metadata
        } >> "$OUT/timeline.txt"
        sync
    fi
    if [ "$((n % 15))" -eq 0 ]; then
        dmesg > "$OUT/dmesg-latest.txt"
    fi
    sleep 2
    n=$((n + 1))
done
echo "Six-minute capture finished."
