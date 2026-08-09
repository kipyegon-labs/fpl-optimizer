-- 001_raw.sql — append-only fetch log. Run once, as superuser/owner.
-- Nothing in this schema is ever UPDATEd or DELETEd. Two layers enforce that:
-- (1) the ingest role has no UPDATE/DELETE grant, (2) a statement trigger raises.

create schema if not exists raw;

create table if not exists raw.fetch (
    fetch_id       bigserial primary key,
    endpoint       text        not null,   -- logical name, e.g. 'bootstrap-static'
    url            text        not null,   -- exact URL hit
    requested_at   timestamptz not null,   -- clock before the request
    fetched_at     timestamptz not null,   -- clock after the response landed
    http_status    int,                    -- null if the request never completed
    ok             boolean     not null,
    error          text,                   -- populated iff not ok
    payload_sha256 char(64),               -- of the raw response bytes, pre-gzip
    payload_gzip   bytea,                  -- gzip of raw response bytes
    payload_bytes  int,                    -- uncompressed length
    event_id       int,                    -- FPL gameweek id, if endpoint is GW-scoped
    ingest_version text        not null
);

create index if not exists fetch_endpoint_time_idx
    on raw.fetch (endpoint, fetched_at desc);
create index if not exists fetch_event_idx
    on raw.fetch (endpoint, event_id, fetched_at desc)
    where event_id is not null;

create or replace function raw.deny_mutation() returns trigger
language plpgsql as $$
begin
    raise exception 'raw.fetch is append-only (attempted %)', tg_op;
end
$$;

drop trigger if exists fetch_append_only on raw.fetch;
create trigger fetch_append_only
    before update or delete or truncate on raw.fetch
    for each statement execute function raw.deny_mutation();

-- Least-privilege ingest role. Password comes from your secret store, not this file.
-- create role fpl_ingest login password :'ingest_password';
-- grant usage on schema raw to fpl_ingest;
-- grant select, insert on raw.fetch to fpl_ingest;
-- grant usage on sequence raw.fetch_fetch_id_seq to fpl_ingest;
-- No update. No delete. Not an oversight.
