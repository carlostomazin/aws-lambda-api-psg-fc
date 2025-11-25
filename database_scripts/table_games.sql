create table public.games (
  id uuid not null default gen_random_uuid (),
  created_at timestamp with time zone not null default now(),
  updated_at timestamp without time zone null,
  game_date date not null,
  players_total integer not null default 0,
  players_paid integer not null default 0,
  players_visitors integer not null default 0,
  game_price numeric(10,2) NOT NULL DEFAULT 0.00,
  constraint game_pkey primary key (id),
  constraint game_date_key unique (game_date)
) TABLESPACE pg_default;