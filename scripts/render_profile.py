#!/usr/bin/env python3
"""Render the profile card using only public GitHub data and the Python standard library."""
import argparse
from datetime import date, datetime, timezone
from html import escape
import json
from pathlib import Path
from urllib.request import Request, urlopen

ROOT = Path(__file__).resolve().parents[1]
USER = 'MeinhartThomas'


def github(path):
    request = Request('https://api.github.com/' + path, headers={
        'Accept': 'application/vnd.github+json',
        'X-GitHub-Api-Version': '2022-11-28',
        'User-Agent': USER + '-profile',
    })
    with urlopen(request, timeout=30) as response:
        return json.load(response)


def load_public_data():
    user = github('users/' + USER)
    repos = []
    page = 1
    while True:
        batch = github(f'users/{USER}/repos?type=owner&per_page=100&page={page}')
        repos.extend(batch)
        if len(batch) < 100:
            break
        page += 1
    return user, repos


def render(user, repos, today):
    portrait = json.loads((ROOT / 'assets/portrait.json').read_text())
    own = [repo for repo in repos if not repo['fork'] and repo['name'].lower() != USER.lower()]
    languages = sorted({repo['language'] for repo in own if repo.get('language')})
    joined = date.fromisoformat(user['created_at'][:10])
    years = today.year - joined.year - ((today.month, today.day) < (joined.month, joined.day))
    blog = (user.get('blog') or 'meinhart.dev').removeprefix('https://').removeprefix('http://').rstrip('/')
    chunks = ['''<svg xmlns="http://www.w3.org/2000/svg" width="1120" height="600" viewBox="0 0 1120 600" role="img" aria-labelledby="title description">
  <title id="title">Thomas Meinhart — terminal profile</title>
  <desc id="description">ASCII portrait of Thomas Meinhart, Latoo.labs, TypeScript and Swift projects, contact links and public GitHub statistics.</desc>
  <rect width="1120" height="600" rx="12" fill="#0d1117"/>
  <rect x="1" y="1" width="1118" height="598" rx="11" fill="none" stroke="#30363d"/>
  <g font-family="'DejaVu Sans Mono', 'Liberation Mono', Consolas, monospace" font-size="14" fill="#c9d1d9">''']

    def text(x, y, value, color='#c9d1d9', size=14, anchor=None, weight=None):
        attrs = f'x="{x}" y="{y}" fill="{color}" font-size="{size}"'
        if anchor:
            attrs += f' text-anchor="{anchor}"'
        if weight:
            attrs += f' font-weight="{weight}"'
        chunks.append(f'    <text {attrs}>{escape(str(value))}</text>')

    for i, row in enumerate(portrait):
        chunks.append(f'    <text x="30" y="{56 + i * 13}" font-size="12.5" letter-spacing="0" xml:space="preserve" fill="#b8c2cc">{escape(row)}</text>')
    # A fixed character grid keeps labels, dotted leaders and values aligned.
    left, right = 405, 1080

    def section(y, label):
        text(left, y, label, '#e6edf3', weight='600')
        start = left + len(label) * 8.5 + 16
        chunks.append(f'    <path d="M{start} {y-4}H{right}" stroke="#30363d"/>')

    def field(y, label, value):
        value = str(value)
        label_end = left + len(label) * 8.5 + 10
        value_start = right - len(value) * 8.5 - 12
        if value_start > label_end:
            chunks.append(f'    <path d="M{label_end} {y-4}H{value_start}" stroke="#30363d" stroke-dasharray="1 6" stroke-linecap="round"/>')
        text(left, y, label, '#c99a77')
        text(right, y, value, '#a9bfd1', anchor='end')

    section(54, 'thomas@github')
    field(85, 'Name:', user.get('name') or 'Thomas Meinhart')
    field(111, 'Company:', user.get('company') or 'Latoo.labs')
    field(137, 'On GitHub:', f'{years} years / since {joined.year}')
    field(163, 'Languages:', ', '.join(languages) or 'TypeScript, Swift')
    field(189, 'Builds:', 'Developer tools, macOS apps')

    section(236, 'Contact')
    field(267, 'Website:', blog)
    field(293, 'GitHub:', '@' + USER)

    section(340, 'Projects')
    field(371, 'better-scripts:', 'A better npm scripts sidebar')
    field(397, 'ClickUpTimerGuard:', 'Keep your work timer in check')

    section(444, 'GitHub Stats / public')
    field(475, 'Repositories:', user['public_repos'])
    field(501, 'Stars:', sum(repo.get('stargazers_count', 0) for repo in repos))
    field(527, 'Followers / following:', f"{user['followers']} / {user['following']}")
    for i, color in enumerate(['#c99a77', '#d7ba7d', '#98b78b', '#8db5ca', '#b8a1c9', '#c9d1d9']):
        chunks.append(f'    <rect x="{left + i * 20}" y="553" width="20" height="10" fill="{color}"/>')
    text(right, 562, f'updated {today.isoformat()} UTC', '#7d8590', 11, anchor='end')
    chunks.append('  </g>\n</svg>\n')
    (ROOT / 'assets/profile.svg').write_text('\n'.join(chunks))


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--fixture', type=Path, help='Use saved public API data for local rendering')
    parser.add_argument('--date', type=date.fromisoformat, help='Override render date')
    args = parser.parse_args()
    if args.fixture:
        data = json.loads(args.fixture.read_text())
        user, repos = data['user'], data['repos']
    else:
        user, repos = load_public_data()
    render(user, repos, args.date or datetime.now(timezone.utc).date())
