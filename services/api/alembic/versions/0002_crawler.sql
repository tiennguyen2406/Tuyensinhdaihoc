CREATE TABLE crawl_runs (
	id UUID DEFAULT gen_random_uuid() NOT NULL,
	profile_id TEXT NOT NULL,
	profile JSONB NOT NULL,
	status TEXT DEFAULT 'running' NOT NULL,
	url_budget INTEGER NOT NULL,
	requests_used INTEGER DEFAULT 0 NOT NULL,
	stop_reason TEXT,
	created_at TIMESTAMP WITH TIME ZONE DEFAULT now() NOT NULL,
	PRIMARY KEY (id),
	CONSTRAINT crawl_runs_budget_check CHECK (url_budget > 0 AND requests_used >= 0 AND requests_used <= url_budget),
	CONSTRAINT crawl_runs_status_check CHECK (status IN ('running','paused','completed','needs_review','failed'))
);

CREATE TABLE crawl_host_states (
	host TEXT NOT NULL,
	owner_token UUID,
	busy_until TIMESTAMP WITH TIME ZONE,
	next_allowed_at TIMESTAMP WITH TIME ZONE DEFAULT now() NOT NULL,
	blocked_until TIMESTAMP WITH TIME ZONE,
	needs_review BOOLEAN DEFAULT false NOT NULL,
	failures INTEGER DEFAULT 0 NOT NULL,
	robots_cache JSONB DEFAULT '{}'::jsonb NOT NULL,
	PRIMARY KEY (host),
	CONSTRAINT crawl_host_states_failures_check CHECK (failures >= 0)
);

CREATE TABLE crawl_schedules (
	source_id UUID NOT NULL,
	profile_id TEXT NOT NULL,
	resource_kind TEXT NOT NULL,
	interval_seconds INTEGER NOT NULL,
	due_at TIMESTAMP WITH TIME ZONE NOT NULL,
	last_unconditional_at TIMESTAMP WITH TIME ZONE,
	PRIMARY KEY (source_id),
	CONSTRAINT crawl_schedules_kind_check CHECK (resource_kind IN ('html','attachment','robots')),
	CONSTRAINT crawl_schedules_interval_check CHECK (interval_seconds >= 3600),
	FOREIGN KEY(source_id) REFERENCES sources (id)
);
