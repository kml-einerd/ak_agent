# PROTOCOL: SQLite vs PostgreSQL Decision

**DOMAIN:** architecture / database
**APPLIES TO:** Choosing a database for a new web application, especially when evaluating whether the project truly needs the complexity of a client-server database
**RATIONALE:** The vast majority of web applications never need horizontal scaling, streaming replication, or parallel query execution. SQLite with WAL mode handles tens of thousands of requests per day with microsecond read latency (local disk, not network round-trip). Rails 8 made SQLite a production-ready option with SolidQueue, SolidCache, and SolidCable — replacing PostgreSQL + Redis + Memcached with three .sqlite3 files. The infrastructure cost drops from ~$84/month (VPS + RDS + ElastiCache) to ~$12/month (single VPS). The cognitive cost drops even more: no connection pooling, no "is PostgreSQL accepting connections?", no Redis data loss on restart.

---

## EVALUATION

| SIGNAL | DIAGNOSE | INTERVENE |
|--------|----------|-----------|
| Application runs on a single server with moderate traffic (tens of thousands req/day) | Standard web app, no horizontal scaling needed | Use SQLite. Configure WAL mode. Use SolidQueue for jobs, SolidCache for cache. Deploy with Kamal on a single VPS. |
| Multiple web servers need to write to the same database concurrently | SQLite is single-writer — this is a hard limitation | Use PostgreSQL. SQLite cannot support multi-node write concurrency. |
| Dataset exceeds hundreds of GB | PostgreSQL has better query planning and parallelism for large datasets | Use PostgreSQL with appropriate indexing and query optimization. |
| Need replication and high availability (99.99%+ uptime SLA) | SQLite has no built-in replication | Use PostgreSQL with streaming replication or managed database service. |
| Team insists on PostgreSQL "because production" | Cargo cult — evaluating based on reputation, not requirements | Challenge: "What specific capability of PostgreSQL does this project need that SQLite can't provide?" If no concrete answer, SQLite is simpler and sufficient. |

**TRADE-OFFS:** SQLite eliminates infrastructure complexity but limits horizontal scaling. For the ~95% of apps that never scale beyond one server, this is a massive win. For the ~5% that genuinely need multi-node, PostgreSQL is the correct choice.

**ESCALATE WHEN:** Traffic grows beyond what a single server can handle and adding more CPU/RAM to the VPS is no longer cost-effective. At that point, migrating to PostgreSQL is a one-time investment with well-documented tooling.

## SOURCE
https://akitaonrails.com/2026/02/20/sqlite-kamal-deploy-de-rails-sem-drama-bastidores-do-the-m-akita-chronicles/
