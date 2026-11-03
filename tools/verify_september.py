"""Check public aggregate consistency and release integrity, without private inputs."""
from pathlib import Path
import hashlib
import json
import math

ROOT = Path(__file__).resolve().parents[1]


def verify():
    checks = 0

    def check(condition, message):
        nonlocal checks
        if not condition:
            raise ValueError(message)
        checks += 1

    d = json.loads((ROOT / 'evidence/september_2026.json').read_text())
    check(d['evaluation_freeze'] == '2026-09-30', 'Wrong evaluation cutoff')
    check(d['model_version'] == 'bertopic_percountry_v1', 'Wrong model version')
    counts = {r['figure']: r['value'] for r in d['tables']['46_21_corpus_counts']}
    check(int(counts['documents']) == d['input_counts']['documents'] == 10537, 'Document count')
    check(int(counts['chunks']) == d['input_counts']['chunks'] == 77356, 'Passage count')
    check(int(counts['sources']) == 63, 'Source count')
    sizes = {cc: int(counts[f'{cc} categorised documents']) for cc in ('eng', 'sco', 'irl')}
    check(sum(sizes.values()) == int(counts['categorised documents']) == 10528, 'Category denominator')
    for cc, n in sizes.items():
        check(abs(float(counts[f'{cc} share of categorised %']) - n / 10528 * 100) < .0051, f'{cc} volume share')
    for cc in sizes:
        rows = [r for r in d['npmi'] if r['cc'] == cc]
        check(len(rows) == 2 and {r['model'] for r in rows} == {'NMF', 'BERTopic'}, f'{cc} coherence pair')
        check(len({r['reference_documents'] for r in rows}) == 1, f'{cc} common reference')
        for r in rows:
            check(-1 <= r['npmi'] <= 1 and 0 <= r['diversity'] <= 1, 'Coherence/diversity domain')
        rows = [r for r in d['bootstrap_fractional'] if r['cc'] == cc]
        check(len(rows) == 20, f'{cc} category coverage')
        check(abs(sum(r['share_pct'] for r in rows) - 100) < 1e-8, f'{cc} fractional shares sum')
        for r in rows:
            check(r['measure'] == 'fractional_document_share' and r['n'] == sizes[cc] and r['draws'] == 2000,
                  'Bootstrap measure, denominator or draws')
            check(0 <= r['ci_lo'] <= r['share_pct'] <= r['ci_hi'] <= 100, 'Bootstrap range')
    rows = [r for r in d['remapping'] if r['rule'] == 'production_outlier_excluded']
    check(len(rows) == 3, 'Mapping comparisons')
    for r in rows:
        check(r['n'] == 10528 and r['unmatched_docs'] == 0, 'Mapping coverage')
        check(abs(r['changed_pct'] - 100*r['changed_docs']/r['n']) < 1e-9, 'Mapping arithmetic')
        check(r['forced_change_pct'] <= r['changed_pct'] <= r['possible_change_pct'], 'Tie bounds')
    v = d['remapping_validation']
    check(v['non_tie_category_mismatches'] == 0 and v['category_mismatches'] == 20, 'Stored tie differences')
    stats = d['tables']['46_24_chi_square_v']
    chi = next(r for r in stats if r['figure'] == 'chi-square')
    cv = next(r for r in stats if r['figure'] == "Cramer's V")
    check(abs(math.sqrt(chi['value']/(2*chi['n'])) - cv['value']) < .000051, 'Association arithmetic')

    def no_document_payload(value):
        if isinstance(value, dict):
            check(not ({'doc_id', 'document_id', 'text', 'full_text', 'url', 'chunk_index'} & value.keys()),
                  'Document-level or text payload in aggregate projection')
            for child in value.values(): no_document_payload(child)
        elif isinstance(value, list):
            for child in value: no_document_payload(child)
    no_document_payload(d)
    manifest = ROOT / 'PUBLIC_SHA256SUMS'
    check(manifest.is_file(), 'Missing public checksum manifest')
    for line in manifest.read_text().splitlines():
        digest, name = line.split('  ', 1)
        p = (ROOT / name).resolve()
        check(ROOT.resolve() in p.parents, 'Checksum path outside release')
        check(p.is_file() and hashlib.sha256(p.read_bytes()).hexdigest() == digest, f'Checksum mismatch: {name}')
    print(f'Passed {checks} aggregate and release-integrity checks. Private-input reproduction and live deployment were not tested.')


if __name__ == '__main__':
    verify()
