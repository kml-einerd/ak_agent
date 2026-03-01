# ANTI-PATTERN: NFS/SMB for High-Churn Block Storage

**DOMAIN:** deployment / infrastructure
**APPEARS AS:** "I'll just redirect Docker's data directory (or database WAL, or build cache) to an NFS/SMB network share — it's already mounted and available"
**ROOT CAUSE:** NFS and SMB are file-level protocols: every metadata operation (chmod, chown, stat, fsync) is a separate RPC call over the network. High-churn workloads like Docker builds issue thousands of such calls per second — each with its own network round-trip latency. Even at 10Gbps, 106ms average RPC latency turns a 100-call operation into >10 seconds of pure latency overhead.
**RATIONALE:**
1. File-based protocols were designed for shared human-accessible file access, not for OS-level block I/O — they expose the filesystem abstraction at the network boundary, multiplying latency for every metadata call [explicit]
2. Operations like `chmod -R` or package installation during Docker builds recurse through every inode entry, issuing one RPC per file — a seemingly small directory tree becomes hundreds of serial network calls [explicit]
3. Block protocols (iSCSI, EBS) bypass the file abstraction entirely — the OS sees a raw block device and manages its own filesystem locally, collapsing all metadata ops into local operations; only actual read/write blocks traverse the network [derived]

---

## SYMPTOMS

- Docker build steps that take <1 second locally take hundreds of seconds on NFS mount
- `nfsiostat 1 10` shows avg RPC execution time >10ms and average queue time approaching execution time (e.g., `avg exe=106ms avg queue=102ms`)
- `chmod -R` or `find` operations on a mounted NFS directory are disproportionately slow even on fast networks
- Git operations on NFS-mounted project directories produce spurious permission-change diffs

## CORRECTION

Use a block-level protocol instead of a file-level protocol for high-churn workloads:
- **iSCSI**: Create a virtual LUN on the NAS, mount as a real block device on Linux (see `procedure-iscsi-block-device-setup.md`)
- **AWS EBS**: Elastic Block Store is block-level by design — use it for database volumes, build caches, container storage
- Keep NFS/SMB only for workloads with human-scale access patterns: media files, downloads, document shares where one file is opened at a time

**NOT TO CONFUSE WITH:** NFS performance tuning (e.g., increasing `rsize`/`wsize`, using `async` mount). Tuning can reduce overhead but cannot eliminate the fundamental per-file RPC cost. The anti-pattern is the architectural choice, not the specific mount options.

## SOURCE
https://akitaonrails.com/2025/04/24/acessando-seu-nas-usando-iscsi-em-vez-de-smb/
