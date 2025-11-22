create table public.game_players (
  id uuid not null default gen_random_uuid (),
  game_id uuid not null,
  player_id uuid not null,
  created_at timestamp with time zone not null default now(),
  updated_at timestamp with time zone null,
  is_goalkeeper boolean not null default false,
  is_visitor boolean not null default false,
  invited_by uuid null,
  paid boolean not null default false,
  team text null,
  constraint game_players_pkey primary key (id),
  constraint game_players_game_id_player_id_key unique (game_id, player_id),
  constraint game_players_game_id_fkey foreign KEY (game_id) references games (id) on delete CASCADE,
  constraint game_players_invited_by_fkey foreign KEY (invited_by) references players (id) on delete set null,
  constraint game_players_player_id_fkey foreign KEY (player_id) references players (id) on delete CASCADE
) TABLESPACE pg_default;