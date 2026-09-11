-- HARNESS — initial Supabase schema
--
-- Paste this whole file into the Supabase dashboard SQL Editor and Run.
-- The SQL Editor goes over HTTPS (port 443), so it works from a network that
-- blocks the Postgres ports 6543/5432 — which is how you create the schema
-- without ever connecting a database client from this machine.
--
-- Derived by hand from backend/app/models/*.py. Every enum type name, member,
-- column name, type, nullability and foreign key mirrors what SQLAlchemy would
-- emit for those models, so the ORM binds to these tables without translation.
--
-- Safe to re-run: every statement is guarded (IF NOT EXISTS / DO block).
-- It creates nothing it does not need and drops nothing, ever.

-- ---------------------------------------------------------------------------
-- Enum types
--
-- CREATE TYPE has no IF NOT EXISTS in Postgres, hence the DO blocks. Member
-- values are the Python enum NAMES, which is what SQLAlchemy's Enum() persists
-- by default -- in app/models/enums.py name == value for every member, so the
-- two agree either way.
-- ---------------------------------------------------------------------------

DO $$ BEGIN
    CREATE TYPE app_type AS ENUM ('CHATBOT', 'RAG', 'AGENT', 'MCP', 'WORKFLOW');
EXCEPTION WHEN duplicate_object THEN NULL; END $$;

DO $$ BEGIN
    CREATE TYPE app_status AS ENUM ('DRAFT', 'ACTIVE', 'ARCHIVED');
EXCEPTION WHEN duplicate_object THEN NULL; END $$;

DO $$ BEGIN
    CREATE TYPE suite_source AS ENUM ('SEEDED', 'CUSTOM', 'MIXED');
EXCEPTION WHEN duplicate_object THEN NULL; END $$;

DO $$ BEGIN
    CREATE TYPE test_category AS ENUM (
        'PROMPT_INJECTION',
        'SYSTEM_PROMPT_LEAKAGE',
        'SCOPE_ESCAPE',
        'HALLUCINATION_TRAP',
        'UNSUPPORTED_CLAIMS',
        'UNAUTHORIZED_TOOL_REQUEST',
        'UNSAFE_PARAMETERS'
    );
EXCEPTION WHEN duplicate_object THEN NULL; END $$;

DO $$ BEGIN
    CREATE TYPE severity_level AS ENUM ('INFO', 'LOW', 'MEDIUM', 'HIGH', 'CRITICAL');
EXCEPTION WHEN duplicate_object THEN NULL; END $$;

DO $$ BEGIN
    CREATE TYPE run_type AS ENUM ('BASELINE', 'RETEST');
EXCEPTION WHEN duplicate_object THEN NULL; END $$;

DO $$ BEGIN
    CREATE TYPE run_status AS ENUM ('PENDING', 'RUNNING', 'COMPLETED', 'FAILED');
EXCEPTION WHEN duplicate_object THEN NULL; END $$;

DO $$ BEGIN
    CREATE TYPE result_status AS ENUM ('PASS', 'FAIL', 'REVIEW', 'ERROR');
EXCEPTION WHEN duplicate_object THEN NULL; END $$;

DO $$ BEGIN
    CREATE TYPE finding_status AS ENUM ('OPEN', 'IN_PROGRESS', 'RESOLVED', 'ACCEPT_RISK');
EXCEPTION WHEN duplicate_object THEN NULL; END $$;

DO $$ BEGIN
    CREATE TYPE release_decision_enum AS ENUM ('READY', 'READY_WITH_CONDITIONS', 'NOT_READY');
EXCEPTION WHEN duplicate_object THEN NULL; END $$;

DO $$ BEGIN
    CREATE TYPE notification_channel AS ENUM ('EMAIL');
EXCEPTION WHEN duplicate_object THEN NULL; END $$;

DO $$ BEGIN
    CREATE TYPE notification_trigger AS ENUM (
        'CRITICAL_FOUND', 'RUN_COMPLETED', 'RELEASE_DECISION_MADE'
    );
EXCEPTION WHEN duplicate_object THEN NULL; END $$;

DO $$ BEGIN
    CREATE TYPE notification_status AS ENUM ('PENDING', 'SENT', 'FAILED');
EXCEPTION WHEN duplicate_object THEN NULL; END $$;

DO $$ BEGIN
    CREATE TYPE automation_type AS ENUM ('WEBHOOK_TRIGGER', 'CALLBACK');
EXCEPTION WHEN duplicate_object THEN NULL; END $$;


-- ---------------------------------------------------------------------------
-- Tables, in dependency order
-- ---------------------------------------------------------------------------

CREATE TABLE IF NOT EXISTS workspaces (
    id              uuid PRIMARY KEY,
    name            varchar NOT NULL,
    owner_email     varchar NOT NULL,
    created_at      timestamp NOT NULL,
    updated_at      timestamp NOT NULL
);

CREATE TABLE IF NOT EXISTS applications (
    id                        uuid PRIMARY KEY,
    workspace_id              uuid NOT NULL REFERENCES workspaces (id),
    name                      varchar NOT NULL,
    app_type                  app_type NOT NULL,
    description               varchar,
    expected_behavior         varchar NOT NULL,
    forbidden_behavior        varchar NOT NULL,
    endpoint_url              varchar NOT NULL,
    auth_header_name          varchar,
    auth_header_value         varchar,
    request_template          json,
    response_path             varchar NOT NULL,
    timeout_seconds           integer NOT NULL,
    status                    app_status NOT NULL,
    last_connection_test_at   timestamp,
    last_connection_test_ok   boolean,
    created_at                timestamp NOT NULL,
    updated_at                timestamp NOT NULL
);

CREATE TABLE IF NOT EXISTS test_suites (
    id              uuid PRIMARY KEY,
    application_id  uuid NOT NULL REFERENCES applications (id),
    name            varchar NOT NULL,
    description     varchar,
    generated_at    timestamp NOT NULL,
    source          suite_source NOT NULL,
    is_active       boolean NOT NULL,
    created_at      timestamp NOT NULL,
    updated_at      timestamp NOT NULL
);

CREATE TABLE IF NOT EXISTS test_cases (
    id                      uuid PRIMARY KEY,
    test_suite_id           uuid NOT NULL REFERENCES test_suites (id),
    category                test_category NOT NULL,
    attack_prompt           varchar NOT NULL,
    severity_if_failed      severity_level NOT NULL,
    expected_safe_behavior  varchar NOT NULL,
    version                 integer NOT NULL,
    is_locked               boolean NOT NULL,
    applicable_app_types    json,
    enabled                 boolean NOT NULL,
    created_at              timestamp NOT NULL,
    updated_at              timestamp NOT NULL
);

CREATE TABLE IF NOT EXISTS test_runs (
    id               uuid PRIMARY KEY,
    application_id   uuid NOT NULL REFERENCES applications (id),
    test_suite_id    uuid NOT NULL REFERENCES test_suites (id),
    run_type         run_type NOT NULL,
    triggered_by     varchar NOT NULL,
    status           run_status NOT NULL,
    started_at       timestamp,
    completed_at     timestamp,
    assurance_score  double precision,
    created_at       timestamp NOT NULL,
    updated_at       timestamp NOT NULL
);

CREATE TABLE IF NOT EXISTS test_results (
    id                    uuid PRIMARY KEY,
    test_run_id           uuid NOT NULL REFERENCES test_runs (id),
    test_case_id          uuid NOT NULL REFERENCES test_cases (id),
    test_case_version     integer NOT NULL,
    execution_prompt      varchar NOT NULL,
    model_response        varchar,
    raw_request_payload   json,
    raw_response_payload  json,
    http_status           integer,
    latency_ms            integer,
    result                result_status NOT NULL,
    severity              severity_level NOT NULL,
    confidence            double precision NOT NULL,
    evidence              json,
    evaluator_version     varchar NOT NULL,
    evaluated_at          timestamp NOT NULL,
    created_at            timestamp NOT NULL
);

CREATE TABLE IF NOT EXISTS findings (
    id                  uuid PRIMARY KEY,
    application_id      uuid NOT NULL REFERENCES applications (id),
    test_result_id      uuid NOT NULL REFERENCES test_results (id),
    category            test_category NOT NULL,
    severity            severity_level NOT NULL,
    title               varchar NOT NULL,
    root_cause          varchar NOT NULL,
    recommendation      varchar NOT NULL,
    status              finding_status NOT NULL,
    first_seen_run_id   uuid NOT NULL REFERENCES test_runs (id),
    last_seen_run_id    uuid NOT NULL REFERENCES test_runs (id),
    created_at          timestamp NOT NULL,
    resolved_at         timestamp,
    updated_at          timestamp NOT NULL
);

CREATE TABLE IF NOT EXISTS remediations (
    id          uuid PRIMARY KEY,
    finding_id  uuid NOT NULL REFERENCES findings (id),
    status      finding_status NOT NULL,
    note        varchar,
    changed_by  varchar NOT NULL,
    changed_at  timestamp NOT NULL
);

CREATE TABLE IF NOT EXISTS retest_comparisons (
    id                uuid PRIMARY KEY,
    application_id    uuid NOT NULL REFERENCES applications (id),
    baseline_run_id   uuid NOT NULL REFERENCES test_runs (id),
    retest_run_id     uuid NOT NULL REFERENCES test_runs (id),
    fixed_count       integer NOT NULL,
    remaining_count   integer NOT NULL,
    regression_count  integer NOT NULL,
    new_count         integer NOT NULL,
    details           json,
    created_at        timestamp NOT NULL
);

CREATE TABLE IF NOT EXISTS release_decisions (
    id                       uuid PRIMARY KEY,
    application_id           uuid NOT NULL REFERENCES applications (id),
    test_run_id              uuid NOT NULL REFERENCES test_runs (id),
    decision                 release_decision_enum NOT NULL,
    blocking_findings_count  integer NOT NULL,
    conditions               json,
    assurance_score          double precision NOT NULL,
    rationale                varchar NOT NULL,
    decided_at               timestamp NOT NULL
);

CREATE TABLE IF NOT EXISTS notifications (
    id                uuid PRIMARY KEY,
    application_id    uuid NOT NULL REFERENCES applications (id),
    finding_id        uuid REFERENCES findings (id),
    channel           notification_channel NOT NULL,
    trigger_event     notification_trigger NOT NULL,
    status            notification_status NOT NULL,
    n8n_execution_id  varchar,
    sent_at           timestamp,
    created_at        timestamp NOT NULL
);

CREATE TABLE IF NOT EXISTS issue_exports (
    id                 uuid PRIMARY KEY,
    application_id     uuid NOT NULL REFERENCES applications (id),
    test_run_id        uuid REFERENCES test_runs (id),
    file_path_or_url   varchar NOT NULL,
    generated_by       varchar NOT NULL,
    generated_at       timestamp NOT NULL,
    sheet_summary      json
);

CREATE TABLE IF NOT EXISTS automation_errors (
    id                uuid PRIMARY KEY,
    automation_type   automation_type NOT NULL,
    application_id    uuid REFERENCES applications (id),
    notification_id   uuid REFERENCES notifications (id),
    error_message     varchar NOT NULL,
    payload_snapshot  json,
    occurred_at       timestamp NOT NULL
);

CREATE TABLE IF NOT EXISTS automation_events (
    event_id      uuid PRIMARY KEY,
    processed_at  timestamp NOT NULL
);


-- ---------------------------------------------------------------------------
-- Indexes on the foreign keys the services actually filter by.
-- Postgres does NOT index foreign keys automatically.
-- ---------------------------------------------------------------------------

CREATE INDEX IF NOT EXISTS ix_applications_workspace_id   ON applications (workspace_id);
CREATE INDEX IF NOT EXISTS ix_test_suites_application_id  ON test_suites (application_id);
CREATE INDEX IF NOT EXISTS ix_test_cases_test_suite_id    ON test_cases (test_suite_id);
CREATE INDEX IF NOT EXISTS ix_test_runs_application_id    ON test_runs (application_id);
CREATE INDEX IF NOT EXISTS ix_test_results_test_run_id    ON test_results (test_run_id);
CREATE INDEX IF NOT EXISTS ix_test_results_test_case_id   ON test_results (test_case_id);
CREATE INDEX IF NOT EXISTS ix_findings_application_id     ON findings (application_id);
CREATE INDEX IF NOT EXISTS ix_findings_status             ON findings (status);
CREATE INDEX IF NOT EXISTS ix_remediations_finding_id     ON remediations (finding_id);
CREATE INDEX IF NOT EXISTS ix_retest_comparisons_retest_run_id
    ON retest_comparisons (retest_run_id);
CREATE INDEX IF NOT EXISTS ix_release_decisions_test_run_id
    ON release_decisions (test_run_id);
CREATE INDEX IF NOT EXISTS ix_notifications_application_id ON notifications (application_id);


-- ---------------------------------------------------------------------------
-- OPTIONAL — closes defect #6 in docs/qa-review.md.
--
-- comparison_service.classify() keys results by test_case_id in a plain dict.
-- Two rows for the same (test_run_id, test_case_id) would make it silently keep
-- whichever it visited last, with no warning. run_service and retest_service
-- only ever insert one row per case per run, so this is unreachable today, but
-- nothing in the schema prevents it. Uncomment to enforce it in the database.
--
-- ALTER TABLE test_results
--     ADD CONSTRAINT uq_test_results_run_case UNIQUE (test_run_id, test_case_id);
-- ---------------------------------------------------------------------------


-- ---------------------------------------------------------------------------
-- Row Level Security
--
-- Deliberately NOT enabled. The backend connects as the postgres/service role
-- over DATABASE_URL and is the only writer; the browser never talks to Postgres
-- directly (every call goes through the FastAPI API). Enabling RLS without
-- policies would lock out the service role's own queries for no security gain.
-- If the frontend is ever pointed at Supabase's REST API directly, RLS becomes
-- mandatory and needs real policies written first.
-- ---------------------------------------------------------------------------

SELECT 'HARNESS schema applied. Tables: ' || count(*)::text AS result
FROM information_schema.tables
WHERE table_schema = 'public'
  AND table_name IN (
    'workspaces','applications','test_suites','test_cases','test_runs',
    'test_results','findings','remediations','retest_comparisons',
    'release_decisions','notifications','issue_exports','automation_errors',
    'automation_events'
  );
