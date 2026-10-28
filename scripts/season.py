"""Archive completed, independently confirmed schedule days for seasonal statistics.

These are forecasts from published schedules, never measured electricity availability.
Unknown/stale/unpublished dates are NOT treated as zero-hour outage days.
"""
import json
from datetime import date, timedelta
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
STATE_PATH = ROOT / 'state' / 'season.json'
OUTPUT_PATH = ROOT / 'site' / 'season.json'
LOCATIONS = {'dacha': 'Дача', 'home': 'Дім', 'solovky': 'Соловки', 'naumenky': 'Науменки'}


def season_for(day):
    """October-March winter season; April-September refers to the last winter."""
    year = day.year if day.month >= 10 else day.year - 1
    return f'{year}/{str(year + 1)[-2:]}', date(year, 10, 1), date(year + 1, 3, 31)


def minutes(value):
    if not isinstance(value, str) or len(value) != 5 or value[2] != ':':
        raise ValueError('Invalid clock')
    h, m = int(value[:2]), int(value[3:])
    if not 0 <= h <= 24 or not 0 <= m < 60 or (h == 24 and m):
        raise ValueError('Invalid clock')
    return h * 60 + m


def confirmed_record(iso, entry):
    """Return a day record only when at least two named sources confirm it."""
    if not isinstance(entry, dict) or entry.get('date') != iso or entry.get('status') != 'normal':
        return None
    sources = entry.get('sources')
    outages = entry.get('outages')
    if not isinstance(sources, list) or len(set(sources)) < 2 or not isinstance(outages, list):
        return None
    try:
        normalized = []
        prev = 0
        for pair in outages:
            if not isinstance(pair, list) or len(pair) != 2:
                return None
            a, b = minutes(pair[0]), minutes(pair[1])
            if not 0 <= a < b <= 1440 or a < prev:
                return None
            prev = b
            normalized.append(pair)
        total = sum(minutes(b) - minutes(a) for a, b in normalized)
        longest = max(normalized, key=lambda p: minutes(p[1]) - minutes(p[0]), default=None)
        return {
            'outages': normalized,
            'total_minutes': total,
            'longest_minutes': minutes(longest[1]) - minutes(longest[0]) if longest else 0,
            'longest_interval': longest,
        }
    except (ValueError, TypeError):
        return None


def archive_completed(archive, old_state, today):
    """Idempotently upsert verified completed days before the short state history expires."""
    seasons = archive.setdefault('seasons', {})
    for key in LOCATIONS:
        entries = (old_state.get('days', {}) if key == 'dacha'
                   else old_state.get('locations', {}).get(key, {}).get('days', {}))
        if not isinstance(entries, dict):
            continue
        for iso, entry in entries.items():
            try:
                completed = date.fromisoformat(iso)
            except (ValueError, TypeError):
                continue
            if completed >= today:
                continue
            season_id, start, end = season_for(completed)
            if not start <= completed <= end:
                continue
            record = confirmed_record(iso, entry)
            if record is None:
                continue
            season = seasons.setdefault(season_id, {'start': start.isoformat(), 'end': end.isoformat(), 'locations': {}})
            season.setdefault('locations', {}).setdefault(key, {})[iso] = record
    return archive


def location_summary(records):
    days = sorted(records)
    if not days:
        return {'recorded_days': 0, 'total_minutes': 0, 'average_minutes': None,
                'max_daily': None, 'longest': None, 'days': {}}
    total = sum(records[d]['total_minutes'] for d in days)
    largest_daily = max(days, key=lambda d: (records[d]['total_minutes'], -date.fromisoformat(d).toordinal()))
    longest = max(days, key=lambda d: (records[d]['longest_minutes'], -date.fromisoformat(d).toordinal()))
    return {
        'recorded_days': len(days),
        'total_minutes': total,
        'average_minutes': round(total / len(days)),
        'max_daily': {'date': largest_daily, 'minutes': records[largest_daily]['total_minutes']},
        'longest': {'date': longest, 'minutes': records[longest]['longest_minutes'],
                    'interval': records[longest]['longest_interval']},
        'days': {d: {'total_minutes': records[d]['total_minutes'],
                      'longest_minutes': records[d]['longest_minutes']} for d in days}
    }


def season_payload(archive, today):
    season_id, start, end = season_for(today)
    season = archive.get('seasons', {}).get(season_id, {})
    stored = season.get('locations', {})
    return {
        'season': season_id, 'start': start.isoformat(), 'end': end.isoformat(),
        'through': min(today - timedelta(days=1), end).isoformat(),
        'basis': 'confirmed_schedules_not_actual_outages',
        'locations': {key: {'name': label, **location_summary(stored.get(key, {}))}
                      for key, label in LOCATIONS.items()}
    }


def update_season(old_state, today):
    try:
        archive = json.loads(STATE_PATH.read_text(encoding='utf-8'))
        if not isinstance(archive.get('seasons'), dict):
            raise ValueError('invalid archive')
    except FileNotFoundError:
        archive = {'seasons': {}}
    # Corrupt archives must halt refresh, not silently erase historical statistics.
    archive_completed(archive, old_state, today)
    content = json.dumps(archive, ensure_ascii=False, indent=2, sort_keys=True) + '\n'
    STATE_PATH.parent.mkdir(exist_ok=True, parents=True)
    if not STATE_PATH.exists() or STATE_PATH.read_text(encoding='utf-8') != content:
        STATE_PATH.write_text(content, encoding='utf-8')
    OUTPUT_PATH.parent.mkdir(exist_ok=True, parents=True)
    OUTPUT_PATH.write_text(json.dumps(season_payload(archive, today), ensure_ascii=False, indent=2) + '\n',
                           encoding='utf-8')
