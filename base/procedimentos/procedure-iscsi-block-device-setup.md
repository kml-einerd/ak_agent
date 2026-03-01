# PROCEDURE: iSCSI Block Device Linux Setup

**TRIGGER:** Need to mount remote NAS storage as a block device on Linux (for high-churn workloads like Docker build cache, databases, or any I/O-intensive application)
**DOMAIN:** deployment / infrastructure
**PRE-CONDITIONS:**
- NAS device with iSCSI target support (e.g., Synology DSM SAN Manager)
- Linux host with `open-iscsi` available in package manager
- Network connectivity between host and NAS (ideally 10Gbps for performance)
- Target drive size determined before creation (cannot resize easily after formatting)

---

## STEPS

1. Create iSCSI LUN on NAS — Use NAS management UI (e.g., Synology SAN Manager wizard): set name, size, optionally enable CHAP for authentication → LUN and target IQN are created

2. Install and enable iSCSI initiator on Linux host:
   ```
   yay -S open-iscsi          # or: apt install open-iscsi / dnf install iscsi-initiator-utils
   sudo systemctl enable --now iscsi
   ```
   → iSCSI service starts and is registered for boot

3. Discover target on the network:
   ```
   sudo iscsiadm -m discovery -t sendtargets -p <NAS_IP>
   ```
   → Returns IQN string(s) like `iqn.2000-01.com.synology:HOSTNAME.lun-name.xxxxxx`

4. Log in to target:
   ```
   sudo iscsiadm -m node --login
   ```
   → New block device appears as `/dev/sdX` (verify with `lsblk`)

5. Set node startup to automatic so it mounts on every boot:
   ```
   sudo iscsiadm -m node \
     -T <IQN> \
     -o update -n node.startup -v automatic
   ```
   → `iscsiadm -m node -o show | grep node.startup` shows `automatic`

6. Format the new block device (use lazy init to avoid 2-hour wait):
   ```
   mkfs.ext4 -v -E lazy_itable_init=1,lazy_journal_init=1 /dev/sdX
   ```
   → Filesystem created on device

7. Add to `/etc/fstab` for persistent mount using by-path identifier (stable across reboots):
   ```
   /dev/disk/by-path/ip-<NAS_IP>:3260-iscsi-<IQN>-lun-1  /media/mountpoint  ext4  _netdev,nofail,x-systemd.automount,x-systemd.requires=iscsid.service,noatime,nodiratime,commit=60  0  2
   ```
   → Mount point survives reboot; `_netdev` ensures network is up before mount attempt

8. Reload systemd and mount:
   ```
   sudo systemctl daemon-reload
   sudo mount -a
   ```
   → Device mounted at target path

9. Redirect application storage (e.g., Docker):
   - Create directory with correct permissions: `sudo mkdir -p /media/mountpoint/docker && sudo chown root:docker /media/mountpoint/docker && sudo chmod 771 /media/mountpoint/docker`
   - Edit `/etc/docker/daemon.json`: `{ "data-root": "/media/mountpoint/docker" }`
   - Restart service: `sudo systemctl restart docker`
   → Application now writes to iSCSI block device

**ON_FAILURE[step-4]:** If login fails with CHAP auth error, verify CHAP credentials match exactly in NAS UI and initiator config at `/etc/iscsi/iscsid.conf`. If no devices appear after login, run `lsblk` and check kernel logs with `dmesg | grep -i scsi`.

**ON_FAILURE[step-7]:** If mount fails at boot, verify `iscsid.service` is enabled, `_netdev` flag is present in fstab, and `x-systemd.requires=iscsid.service` is set. Without `_netdev`, systemd may attempt mount before network is up.

---

## DONE WHEN
- `lsblk` shows the iSCSI device mounted at the configured path
- Application (e.g., Docker) uses the new path: `docker info | grep "Docker Root Dir"` returns iSCSI mount path
- Build/write operations complete in <1 second per step (vs hundreds of seconds on NFS)
- After reboot, device auto-mounts and service starts without manual intervention

## SOURCE
https://akitaonrails.com/2025/04/24/acessando-seu-nas-usando-iscsi-em-vez-de-smb/
