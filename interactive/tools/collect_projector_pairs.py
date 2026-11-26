#!/usr/bin/env python3
"""Collect the seven native source/output pairs for the CUT! projector material.

Run where the supplied project manifests and their original videos live.
The archive contains videos and a clean index. There are no model calls,
network requests, environment dumps, or copies of the original run manifests.
"""
import argparse
import hashlib
import json
from pathlib import Path
import shutil
import subprocess
import tempfile
import zipfile

# Public sample identities checked against the supplied manifests and showcase selections.
CASES = (
    ('grandtour-flooded-mud', 'grandtour_show4_depth/norobot', 'b12c0e6dac0d3e7a6bc7', 'flooded_mud', 202),
    ('grandtour-umbrellas-to-snow', 'grandtour_depth_b200/main', '5b3a48238f412039d031', 'blizzard_whiteout', 101),
    ('impala-blue-hour', 'commons_show4_depth/main', 'd019c3c7d8cafb5442bc', 'blue_hour_dusk', 303),
    ('winter-road-night-rain', 'commons_show4_depth/main', '9e90724a94b76d04ad83', 'night_rain', 101),
    ('goose-flooded-mud-walkthrough', 'goose_show4_depth/main', '87dabe390a3e2f4d6b17', 'flooded_mud', 101),
    ('goose-night-rain-audit', 'goose_show4_depth/main', '315464a22d1ebec3ee86', 'night_rain', 303),
    ('goose-striped-hood-audit', 'goose_show4_depth/main', '88959458ef3e47d4c208', 'frost_dawn', 202),
)


def media_path(root, recorded, kind):
    """Resolve the recorded tree layout relative to the requested project root."""
    parts = Path(recorded).parts
    required = ('data', 'prepared') if kind == 'source' else ('runs',)
    indexes = [i for i in range(len(parts)) if tuple(parts[i:i + len(required)]) == required]
    if not indexes:
        raise ValueError(f'Unexpected {kind} media layout in the stored record.')
    path = root.joinpath(*parts[indexes[-1]:]).resolve(strict=True)
    if not path.is_relative_to(root) or not path.is_file() or path.suffix.lower() != '.mp4':
        raise ValueError(f'Expected a project-local MP4 for {kind}.')
    return path


def inputs(root):
    cache = {}
    for slug, ns, rid, condition, seed in CASES:
        if ns not in cache:
            manifest = root / 'runs' / ns / 'manifest.jsonl'
            with manifest.open(encoding='utf-8') as f:
                cache[ns] = {p['request_id']: p for line in f if line.strip() for p in [json.loads(line)] if p.get('request_id')}
        row = cache[ns].get(rid)
        if not row or row.get('condition') != condition or int(row.get('seed', -1)) != seed:
            raise ValueError(f'Missing or mismatched record: {slug} ({rid}).')
        yield dict(slug=slug, request_id=rid, condition=condition, seed=seed), {
            'source': media_path(root, row['clip_path'], 'source'),
            'generated': media_path(root, row['output_path'], 'generated')}


def describe(path):
    if not shutil.which('ffprobe'):
        return None
    result = subprocess.run(['ffprobe', '-v', 'error', '-select_streams', 'v:0',
                             '-show_entries', 'stream=width,height,r_frame_rate,nb_frames',
                             '-of', 'json', str(path)], check=True, capture_output=True, text=True)
    return json.loads(result.stdout)['streams'][0]


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--root', type=Path, required=True, help='Project storage directory containing data/ and runs/.')
    parser.add_argument('--output', type=Path, default=Path('CUT_projector_masters.zip'))
    args = parser.parse_args()
    pairs = list(inputs(args.root.resolve(strict=True)))  # Require every exact pair before opening the output.
    output = args.output.resolve()
    if output.exists():
        parser.exit(2, f'Existing output left unchanged: {output.name}\n')
    rows = []
    with tempfile.TemporaryDirectory(dir=output.parent) as tmp:
        staged = Path(tmp) / 'masters.zip'
        with zipfile.ZipFile(staged, 'x', compression=zipfile.ZIP_STORED) as archive:
            for rec, paths in pairs:
                meta = dict(rec, media={})
                for role, file in paths.items():
                    name = f"pairs/{rec['slug']}/{role}.mp4"
                    digest = hashlib.sha256()
                    with file.open('rb') as a, archive.open(name, 'w', force_zip64=True) as b:
                        while chunk := a.read(1024 * 1024):
                            digest.update(chunk)
                            b.write(chunk)
                    meta['media'][role] = dict(file=name, sha256=digest.hexdigest(),
                                               video=describe(file))
                rows.append(meta)
        # Append a sanitized index with relative names only.
        with zipfile.ZipFile(staged, 'a') as archive:
            archive.writestr('pairs.json', json.dumps(rows, indent=2) + '\n')
        # Exclusive output prevents replacement even if another process races the check.
        with staged.open('rb') as a, output.open('xb') as b:
            shutil.copyfileobj(a, b)
    print(f'Created {output.name}: {len(rows)} matched pairs, {output.stat().st_size:,} bytes.')


if __name__ == '__main__':
    main()
