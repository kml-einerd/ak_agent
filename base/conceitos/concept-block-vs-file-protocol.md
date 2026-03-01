# CONCEPT: Block-Level vs File-Level Protocol

**DOMAIN:** deployment / infrastructure / architecture
**DEFINITION:** A **file-level protocol** (NFS, SMB/Samba) exposes a filesystem abstraction over the network — every file metadata operation (open, stat, chmod, chown, readdir) is a discrete network RPC call. A **block-level protocol** (iSCSI, AWS EBS, Fibre Channel) exposes raw storage blocks over the network — the receiving OS formats and manages its own filesystem locally, so all metadata operations are local; only actual data blocks traverse the network.
**NOT:**
- Not a distinction between "fast" and "slow" protocols in general — NFS on 10Gbps is fast for sequential large-file reads; the difference is catastrophic only for metadata-heavy workloads
- Not equivalent to "network storage" vs "local storage" — iSCSI is network storage but behaves like a local block device from the OS perspective
- Not related to encryption or authentication capabilities — both protocol families support security layers

**RATIONALE:** Without this distinction, engineers apply NFS/SMB to high-churn workloads expecting "network storage" behavior, not realizing that each chmod or stat in a recursive operation becomes a serialized network call. This produces 100x+ latency regressions on workloads that are routine on local disks. The concept is also the prerequisite for understanding why AWS EBS is used for databases and EC2 root volumes rather than EFS (which is file-level NFS).

---

## REFERENCED BY

- base/anti-patterns/antipattern-nfs-smb-high-churn-storage.md
- base/procedimentos/procedure-iscsi-block-device-setup.md

## SOURCE
https://akitaonrails.com/2025/04/24/acessando-seu-nas-usando-iscsi-em-vez-de-smb/
