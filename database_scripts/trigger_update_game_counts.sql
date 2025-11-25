-- Keep games.players_* counters in sync with game_players changes
create or replace function public.refresh_game_player_counts(p_game uuid)
returns void
language plpgsql
as $$
declare
  totals record;
begin
  select
    count(*) as total,
    count(*) filter (where paid) as paid,
    count(*) filter (where is_visitor) as visitors
  into totals
  from public.game_players
  where game_id = p_game;

  update public.games g
  set players_total     = coalesce(totals.total, 0),
      players_paid      = coalesce(totals.paid, 0),
      players_visitors  = coalesce(totals.visitors, 0),
      total_amount      = coalesce(totals.paid, 0) * g.price_per_player,
      updated_at        = now()
  where g.id = p_game;
end;
$$;

create or replace function public.trg_refresh_game_player_counts()
returns trigger
language plpgsql
as $$
begin
  if (TG_OP = 'INSERT') then
    perform public.refresh_game_player_counts(NEW.game_id);
  elsif (TG_OP = 'UPDATE') then
    if NEW.game_id is distinct from OLD.game_id then
      perform public.refresh_game_player_counts(OLD.game_id);
    end if;
    perform public.refresh_game_player_counts(NEW.game_id);
  elsif (TG_OP = 'DELETE') then
    perform public.refresh_game_player_counts(OLD.game_id);
  end if;

  return null;
end;
$$;

drop trigger if exists trg_refresh_game_player_counts on public.game_players;
create trigger trg_refresh_game_player_counts
after insert or update or delete on public.game_players
for each row execute function public.trg_refresh_game_player_counts();
