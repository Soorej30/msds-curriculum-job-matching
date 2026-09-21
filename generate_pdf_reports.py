#!/usr/bin/env python3
"""
Generate professional PDF reports for each MSDS course.
Uses Playwright (Chromium) for pixel-perfect rendering.

Output: course_reports/pdf/DTSA_5509.pdf  (one per course)
"""

import json
import sys
import time
from pathlib import Path
from html import escape as he
from collections import defaultdict

# ── Load data ─────────────────────────────────────────────────────────────────
BASE = Path(__file__).parent
with open(BASE / 'msds_suggestions.json') as f:
    SUGG = json.load(f)
with open(BASE / 'cu_boulder_msds_courses.json') as f:
    CDATA = json.load(f)

ROLES = SUGG['meta']['role_labels']
PDF_DIR = BASE / 'course_reports' / 'pdf'
PDF_DIR.mkdir(parents=True, exist_ok=True)

# Course metadata
META = {}
for c in CDATA['courses']['online_dtsa']:
    META[c['course_code']] = {**c, 'format_label': 'Online (DTSA)'}
for c in CDATA['courses']['on_campus_electives']:
    META[c['course_code']] = {**c, 'format_label': 'On-Campus'}

# ── Keyword → Topic mapping ───────────────────────────────────────────────────
TOPIC_MAP = {
    'deploy': 'Model Deployment & Serving', 'deployment': 'Model Deployment & Serving',
    'serving': 'Model Deployment & Serving', 'inference': 'Model Deployment & Serving',
    'production': 'Model Deployment & Serving', 'endpoint': 'Model Deployment & Serving',
    'api': 'Model Deployment & Serving', 'rest': 'Model Deployment & Serving',
    'flask': 'Model Deployment & Serving', 'fastapi': 'Model Deployment & Serving',
    'microservice': 'Model Deployment & Serving',
    'mlops': 'MLOps & Pipeline Engineering', 'mlflow': 'MLOps & Pipeline Engineering',
    'kubeflow': 'MLOps & Pipeline Engineering', 'airflow': 'MLOps & Pipeline Engineering',
    'pipeline': 'MLOps & Pipeline Engineering', 'orchestration': 'MLOps & Pipeline Engineering',
    'kubernetes': 'MLOps & Pipeline Engineering', 'docker': 'MLOps & Pipeline Engineering',
    'container': 'MLOps & Pipeline Engineering', 'monitoring': 'MLOps & Pipeline Engineering',
    'drift': 'MLOps & Pipeline Engineering', 'cicd': 'MLOps & Pipeline Engineering',
    'aws': 'Cloud Platforms', 'azure': 'Cloud Platforms', 'gcp': 'Cloud Platforms',
    'cloud': 'Cloud Platforms', 'sagemaker': 'Cloud Platforms', 'vertex': 'Cloud Platforms',
    'databricks': 'Cloud Platforms', 'snowflake': 'Cloud Platforms',
    'neural': 'Deep Learning', 'deep': 'Deep Learning', 'cnn': 'Deep Learning',
    'rnn': 'Deep Learning', 'lstm': 'Deep Learning', 'transformer': 'Deep Learning',
    'attention': 'Deep Learning', 'backpropagation': 'Deep Learning', 'gradient': 'Deep Learning',
    'pytorch': 'Deep Learning', 'tensorflow': 'Deep Learning', 'keras': 'Deep Learning',
    'training': 'Deep Learning',
    'llm': 'LLMs & Generative AI', 'gpt': 'LLMs & Generative AI',
    'generative': 'LLMs & Generative AI', 'prompt': 'LLMs & Generative AI',
    'embedding': 'LLMs & Generative AI', 'rag': 'LLMs & Generative AI',
    'bert': 'LLMs & Generative AI', 'langchain': 'LLMs & Generative AI',
    'spark': 'Data Engineering', 'kafka': 'Data Engineering', 'etl': 'Data Engineering',
    'streaming': 'Data Engineering', 'hadoop': 'Data Engineering',
    'distributed': 'Data Engineering',
    'experiment': 'Experiment Tracking', 'tracking': 'Experiment Tracking',
    'versioning': 'Experiment Tracking', 'reproducib': 'Experiment Tracking',
    'evaluation': 'Model Evaluation', 'benchmark': 'Model Evaluation',
    'accuracy': 'Model Evaluation', 'precision': 'Model Evaluation',
    'recall': 'Model Evaluation', 'fairness': 'Model Evaluation', 'bias': 'Model Evaluation',
    'feature': 'Feature Engineering', 'preprocessing': 'Feature Engineering',
    'encoding': 'Feature Engineering',
    'stakeholder': 'Business Communication', 'communication': 'Business Communication',
    'business': 'Business Communication', 'strategy': 'Business Communication',
    'leadership': 'Business Communication', 'insight': 'Business Communication',
    'hypothesis': 'Statistical Analysis', 'bayesian': 'Statistical Analysis',
    'causal': 'Statistical Analysis',
    'nlp': 'Natural Language Processing', 'sentiment': 'Natural Language Processing',
    'tokenization': 'Natural Language Processing',
    'vision': 'Computer Vision', 'opencv': 'Computer Vision',
    'sql': 'SQL & Database Skills', 'database': 'SQL & Database Skills',
    'optimization': 'Optimization & Tuning', 'hyperparameter': 'Optimization & Tuning',
    'architecture': 'System Design', 'systems': 'System Design', 'scale': 'System Design',
}

def find_topic(word):
    w = word.lower()
    for kw, topic in TOPIC_MAP.items():
        if kw in w or w.startswith(kw):
            return topic
    return None

# ── Analysis helpers ──────────────────────────────────────────────────────────
def analyse(code, entry, meta):
    roles_data = entry['roles']
    role_rows = []
    for role in ROLES:
        rd = roles_data.get(role)
        if rd:
            role_rows.append({'role': role, 'b': rd['before'], 'a': rd['after'],
                               'd': rd['delta'], 'k': rd.get('keywords', [])})
    role_rows.sort(key=lambda r: -r['b'])

    avg_b = sum(r['b'] for r in role_rows) / len(role_rows) if role_rows else 0
    avg_a = sum(r['a'] for r in role_rows) / len(role_rows) if role_rows else 0
    max_d = max((r['d'] for r in role_rows), default=0)

    # Build topics
    kw_map = defaultdict(lambda: {'total': 0.0, 'roles': set()})
    for role in ROLES:
        rd = roles_data.get(role, {})
        for k in rd.get('keywords', []):
            kw_map[k['word']]['total'] += k['demand']
            kw_map[k['word']]['roles'].add(role)

    topic_data = defaultdict(lambda: {'kws': [], 'roles': set()})
    for word, data in kw_map.items():
        topic = find_topic(word)
        if topic:
            topic_data[topic]['kws'].append((word, len(data['roles'])))
            topic_data[topic]['roles'].update(data['roles'])

    topics = sorted(
        [{'topic': t, 'role_count': len(d['roles']),
          'kws': sorted(d['kws'], key=lambda x: -x[1])[:8]}
         for t, d in topic_data.items()],
        key=lambda x: (-x['role_count'], -len(x['kws']))
    )[:8]

    return {'role_rows': role_rows, 'avg_b': avg_b, 'avg_a': avg_a,
            'max_d': max_d, 'topics': topics}

# ── Score helpers ─────────────────────────────────────────────────────────────
def score_color(s):
    return '#16A34A' if s >= 70 else '#D97706' if s >= 40 else '#CC3333'

def pri_label(d):
    return ('HIGH', '#991B1B', '#FEE2E2') if d >= 30 else \
           ('MEDIUM', '#92400E', '#FEF3C7') if d >= 15 else \
           ('LOW', '#166534', '#DCFCE7')

# ── Build recommendation bullets ─────────────────────────────────────────────
def build_recs(topics, entry):
    recs = []
    for t in topics:
        if len(recs) >= 5:
            break
        kw_str = ', '.join(k[0] for k in t['kws'][:6])
        rc = t['role_count']
        if rc >= 3:
            recs.append(('HIGH',
                f'<strong>Add {he(t["topic"])} coverage</strong> — required vocabulary in {rc} of 6 target roles. '
                f'Integrate through lectures, assignments, or lab exercises. '
                f'Key terms: <em>{he(kw_str)}</em>.'))
        elif rc == 2:
            recs.append(('MEDIUM',
                f'<strong>Consider {he(t["topic"])} content</strong> — relevant to {rc} industry roles. '
                f'Could be introduced via case studies or optional readings. '
                f'Key terms: <em>{he(kw_str)}</em>.'))
        else:
            recs.append(('LOW',
                f'<strong>Optional: {he(t["topic"])}</strong> — would broaden appeal to one additional role. '
                f'Candidate terms: <em>{he(kw_str)}</em>.'))
    return recs

# ── HTML template for each course PDF ────────────────────────────────────────
def build_html(code, entry, meta, an):
    title = he(entry.get('title', code))
    section = he(meta.get('program_section', ''))
    spec = he(meta.get('specialization', ''))
    fmt = he(meta.get('format_label', ''))
    credits = meta.get('credits', '—')
    desc = (meta.get('description') or meta.get('catalog_description') or '').strip()
    is_core = 'section 4' not in section.lower() and 'elective' not in section.lower()
    cat = 'Core' if is_core else 'Elective'

    avg_col = score_color(an['avg_b'])
    pot_col = score_color(an['avg_a'])
    delta_col = '#D97706' if an['max_d'] >= 30 else '#CFB87C' if an['max_d'] >= 15 else '#16A34A'

    # ── Role rows HTML ─────────────────────────────────────────────────────────
    role_rows_html = ''
    for r in an['role_rows']:
        pl, pc, pbg = pri_label(r['d'])
        bc = score_color(r['b'])
        ac = score_color(r['a'])
        b_pct = min(100, r['b'])
        a_pct = min(100, r['a'])
        role_rows_html += f"""
        <tr>
          <td class="role-cell">{he(r['role'])}</td>
          <td class="score-cell">
            <div class="bar-row">
              <div class="bar-bg"><div class="bar-fill" style="width:{b_pct:.1f}%;background:{bc}"></div></div>
              <span class="score-num" style="color:{bc}">{r['b']:.1f}</span>
            </div>
          </td>
          <td class="score-cell">
            <div class="bar-row">
              <div class="bar-bg"><div class="bar-fill" style="width:{a_pct:.1f}%;background:{ac}"></div></div>
              <span class="score-num" style="color:{ac}">{r['a']:.1f}</span>
            </div>
          </td>
          <td class="delta-cell"><span style="color:{delta_col};font-weight:700">+{r['d']:.1f}</span></td>
          <td><span class="pri-badge" style="color:{pc};background:{pbg}">{pl}</span></td>
        </tr>"""

    # ── Topics HTML ────────────────────────────────────────────────────────────
    topics_html = ''
    for t in an['topics'][:8]:
        chips = ''.join(
            f'<span class="kw-chip{"" if k[1] < 3 else " cross"}">{he(k[0])}</span>'
            for k in t['kws']
        )
        topics_html += f"""
        <div class="topic-card">
          <div class="topic-name">
            {he(t['topic'])}
            <span class="role-count">{t['role_count']} of 6 roles</span>
          </div>
          <div class="kw-chips">{chips}</div>
        </div>"""

    if not topics_html:
        topics_html = '<div class="aligned-notice">✓ Course vocabulary is well-aligned with industry job descriptions.</div>'

    # ── Recommendations HTML ───────────────────────────────────────────────────
    recs = build_recs(an['topics'], entry)
    recs_html = ''
    for i, (pri, body) in enumerate(recs, 1):
        pl, pc, pbg = pri_label(35 if pri == 'HIGH' else 20 if pri == 'MEDIUM' else 5)
        recs_html += f"""
        <li class="rec-item">
          <div class="rec-num">{i}</div>
          <div class="rec-body">
            <span class="pri-badge" style="color:{pc};background:{pbg}">{pl}</span>
            {body}
          </div>
        </li>"""

    if not recs_html:
        recs_html = '<li class="rec-item"><div class="rec-num">✓</div><div class="rec-body">This course is already well-aligned with industry expectations. Continue monitoring for emerging tools and frameworks.</div></li>'

    # ── Per-role gap keywords ─────────────────────────────────────────────────
    gap_html = ''
    for r in an['role_rows']:
        if r['d'] < 5 or not r['k']:
            continue
        chips = ''.join(f'<span class="kw-chip">{he(k["word"])}</span>'
                        for k in r['k'][:10])
        gap_html += f"""
        <div class="gap-role">
          <div class="gap-role-head">
            <span class="gap-role-name">{he(r['role'])}</span>
            <span class="gap-scores">{r['b']:.1f} → {r['a']:.1f}
              <span style="color:{delta_col}">(+{r['d']:.1f} pts)</span>
            </span>
          </div>
          <div class="kw-chips">{chips}</div>
        </div>"""

    return f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>{he(code)} – Curriculum Alignment Report</title>
<link rel="preconnect" href="https://fonts.googleapis.com">
<link href="https://fonts.googleapis.com/css2?family=IBM+Plex+Mono:wght@400;600&family=IBM+Plex+Sans:ital,wght@0,300;0,400;0,600;0,700;1,400&family=IBM+Plex+Serif:wght@400;600;700&display=swap" rel="stylesheet">
<style>
* {{ box-sizing: border-box; margin: 0; padding: 0; }}

@page {{
  size: Letter;
  margin: 0.75in 0.85in 0.85in 0.85in;
  @top-center {{
    content: "CU Boulder MSDS · Curriculum Alignment Report";
    font-family: 'IBM Plex Mono', monospace;
    font-size: 7pt;
    color: #9AAABA;
    letter-spacing: .05em;
  }}
  @bottom-right {{
    content: "Page " counter(page) " of " counter(pages);
    font-family: 'IBM Plex Mono', monospace;
    font-size: 7pt;
    color: #9AAABA;
  }}
  @bottom-left {{
    content: "{he(code)} · {title[:50]}{'…' if len(entry.get('title',''))>50 else ''}";
    font-family: 'IBM Plex Mono', monospace;
    font-size: 7pt;
    color: #9AAABA;
  }}
}}

body {{
  font-family: 'IBM Plex Sans', system-ui, sans-serif;
  font-size: 9.5pt;
  line-height: 1.55;
  color: #1A2035;
  background: #fff;
}}

/* ── Document header ─────────────────────────────────────────────────── */
.doc-header {{
  border-bottom: 2px solid #CFB87C;
  padding-bottom: 14pt;
  margin-bottom: 18pt;
}}
.institution-line {{
  font-family: 'IBM Plex Mono', monospace;
  font-size: 7pt;
  color: #9AAABA;
  letter-spacing: .1em;
  text-transform: uppercase;
  margin-bottom: 10pt;
}}
.doc-header h1 {{
  font-family: 'IBM Plex Serif', serif;
  font-size: 17pt;
  font-weight: 700;
  color: #1B2A4A;
  line-height: 1.25;
  margin-bottom: 6pt;
  text-wrap: balance;
}}
.course-code-badge {{
  font-family: 'IBM Plex Mono', monospace;
  font-size: 9pt;
  font-weight: 600;
  color: #CFB87C;
  letter-spacing: .04em;
  margin-bottom: 6pt;
  display: block;
}}
.meta-grid {{
  display: grid;
  grid-template-columns: repeat(3, 1fr);
  gap: 6pt 18pt;
  margin-top: 10pt;
  padding: 10pt 12pt;
  background: #F5F7FB;
  border-radius: 5pt;
  border: 1px solid #DDE3EF;
}}
.meta-item {{ font-size: 8pt; }}
.meta-label {{
  font-family: 'IBM Plex Mono', monospace;
  font-size: 6.5pt;
  color: #9AAABA;
  text-transform: uppercase;
  letter-spacing: .09em;
  display: block;
  margin-bottom: 1pt;
}}
.meta-value {{ font-weight: 600; color: #1B2A4A; }}
.spec-line {{
  grid-column: 1 / -1;
  font-size: 7.5pt;
  color: #5A6A8A;
  padding-top: 5pt;
  border-top: 1px solid #DDE3EF;
  margin-top: 3pt;
}}

/* ── Stat tiles ──────────────────────────────────────────────────────── */
.stat-row {{
  display: grid;
  grid-template-columns: repeat(3, 1fr);
  gap: 8pt;
  margin-bottom: 18pt;
}}
.stat-tile {{
  border: 1px solid #DDE3EF;
  border-radius: 6pt;
  padding: 9pt 11pt;
  text-align: center;
  background: #FAFBFD;
}}
.stat-val {{
  font-family: 'IBM Plex Mono', monospace;
  font-size: 22pt;
  font-weight: 600;
  line-height: 1;
  margin-bottom: 3pt;
}}
.stat-lbl {{
  font-size: 6.5pt;
  color: #7A8AAA;
  text-transform: uppercase;
  letter-spacing: .09em;
  margin-bottom: 1pt;
}}
.stat-sub {{ font-size: 7pt; color: #9AAABA; }}

/* ── Section headings ────────────────────────────────────────────────── */
h2 {{
  font-family: 'IBM Plex Mono', monospace;
  font-size: 7.5pt;
  font-weight: 600;
  color: #5A6A8A;
  text-transform: uppercase;
  letter-spacing: .12em;
  margin: 18pt 0 8pt;
  padding-bottom: 4pt;
  border-bottom: 1.5px solid #DDE3EF;
  page-break-after: avoid;
}}

/* ── Description ─────────────────────────────────────────────────────── */
.desc-box {{
  background: #F8F9FC;
  border: 1px solid #DDE3EF;
  border-left: 3px solid #CFB87C;
  border-radius: 0 5pt 5pt 0;
  padding: 9pt 11pt;
  font-size: 9pt;
  color: #3D4E72;
  line-height: 1.65;
  margin-bottom: 16pt;
}}

/* ── Alignment table ─────────────────────────────────────────────────── */
table {{
  width: 100%;
  border-collapse: collapse;
  font-size: 8.5pt;
  margin-bottom: 16pt;
  page-break-inside: avoid;
}}
thead th {{
  background: #1B2A4A;
  color: #C8D5E8;
  font-family: 'IBM Plex Mono', monospace;
  font-size: 6.5pt;
  font-weight: 600;
  letter-spacing: .09em;
  text-transform: uppercase;
  padding: 6pt 8pt;
  text-align: left;
}}
tbody td {{
  padding: 5.5pt 8pt;
  border-bottom: 1px solid #EEF1F8;
  vertical-align: middle;
}}
tbody tr:last-child td {{ border-bottom: none; }}
tbody tr:nth-child(even) td {{ background: #FAFBFD; }}
.role-cell {{ font-weight: 600; color: #1B2A4A; }}
.score-cell {{ width: 120pt; }}
.delta-cell {{ width: 45pt; font-family: 'IBM Plex Mono', monospace; }}
.bar-row {{ display: flex; align-items: center; gap: 6pt; }}
.bar-bg {{
  width: 70pt; height: 6pt;
  background: #E8EDF5; border-radius: 3pt;
  flex-shrink: 0; overflow: hidden;
}}
.bar-fill {{ height: 100%; border-radius: 3pt; }}
.score-num {{
  font-family: 'IBM Plex Mono', monospace;
  font-size: 8pt; font-weight: 600;
  min-width: 24pt; text-align: right;
}}
.pri-badge {{
  font-family: 'IBM Plex Mono', monospace;
  font-size: 6.5pt; font-weight: 700;
  padding: 1.5pt 4pt;
  border-radius: 99pt;
  text-transform: uppercase;
  letter-spacing: .06em;
  white-space: nowrap;
}}

/* ── Topics ──────────────────────────────────────────────────────────── */
.topics-grid {{
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 7pt;
  margin-bottom: 16pt;
}}
.topic-card {{
  border: 1px solid #DDE3EF;
  border-radius: 5pt;
  padding: 8pt 9pt;
  page-break-inside: avoid;
  background: #FAFBFD;
}}
.topic-name {{
  font-size: 8pt;
  font-weight: 700;
  color: #1B2A4A;
  margin-bottom: 5pt;
  display: flex;
  align-items: center;
  gap: 5pt;
  flex-wrap: wrap;
}}
.role-count {{
  font-family: 'IBM Plex Mono', monospace;
  font-size: 6.5pt;
  font-weight: 600;
  background: #CFB87C20;
  border: 1px solid #CFB87C55;
  color: #7A5C1A;
  padding: 1pt 4pt;
  border-radius: 99pt;
}}
.kw-chips {{ display: flex; flex-wrap: wrap; gap: 3pt; }}
.kw-chip {{
  font-family: 'IBM Plex Mono', monospace;
  font-size: 7pt;
  background: #EEF1F8;
  border: 1px solid #D8E0EF;
  color: #2A3D6A;
  padding: 1.5pt 5pt;
  border-radius: 3pt;
}}
.kw-chip.cross {{
  background: #FDF5E6;
  border-color: #CFB87C88;
  color: #7A5C1A;
}}
.aligned-notice {{
  background: #F0FDF4;
  border: 1px solid #BBF7D0;
  border-radius: 5pt;
  padding: 9pt 11pt;
  font-size: 8.5pt;
  color: #166534;
  margin-bottom: 16pt;
}}

/* ── Recommendations ─────────────────────────────────────────────────── */
.rec-list {{ list-style: none; margin-bottom: 16pt; }}
.rec-item {{
  display: flex;
  gap: 9pt;
  align-items: flex-start;
  padding: 9pt 11pt;
  border-left: 3px solid #CFB87C;
  border-radius: 0 5pt 5pt 0;
  margin-bottom: 6pt;
  background: #FFFEF8;
  font-size: 8.5pt;
  page-break-inside: avoid;
}}
.rec-item:nth-child(even) {{ background: #FDFCF5; }}
.rec-num {{
  background: #CFB87C;
  color: #1B2A4A;
  font-family: 'IBM Plex Mono', monospace;
  font-size: 7pt;
  font-weight: 700;
  min-width: 16pt; height: 16pt;
  border-radius: 50%;
  display: flex; align-items: center; justify-content: center;
  flex-shrink: 0;
  margin-top: 1pt;
}}
.rec-body {{ flex: 1; line-height: 1.6; }}
.rec-body strong {{ color: #1B2A4A; }}
.rec-body em {{ color: #5A6A8A; font-style: normal; font-size: 8pt; }}

/* ── Gap keywords ────────────────────────────────────────────────────── */
.gap-role {{ margin-bottom: 10pt; page-break-inside: avoid; }}
.gap-role-head {{
  display: flex; align-items: baseline;
  justify-content: space-between;
  margin-bottom: 4pt;
}}
.gap-role-name {{ font-size: 8.5pt; font-weight: 700; color: #1B2A4A; }}
.gap-scores {{
  font-family: 'IBM Plex Mono', monospace;
  font-size: 7.5pt; color: #7A8AAA;
}}

/* ── Methodology note ────────────────────────────────────────────────── */
.methodology {{
  background: #F5F7FB;
  border: 1px solid #DDE3EF;
  border-radius: 5pt;
  padding: 9pt 11pt;
  font-size: 7.5pt;
  color: #5A6A8A;
  line-height: 1.6;
  margin-top: 20pt;
  page-break-inside: avoid;
}}
.methodology strong {{ color: #2A3D6A; }}

/* ── Footer ──────────────────────────────────────────────────────────── */
.doc-footer {{
  margin-top: 20pt;
  padding-top: 9pt;
  border-top: 1px solid #DDE3EF;
  font-size: 7.5pt;
  color: #9AAABA;
  display: flex;
  justify-content: space-between;
}}
.page-break {{ page-break-before: always; }}
</style>
</head>
<body>

<!-- Document header -->
<div class="doc-header">
  <div class="institution-line">
    University of Colorado Boulder · Master of Science in Data Science ·
    Curriculum–Industry Alignment Report · September 2026
  </div>
  <span class="course-code-badge">{he(code)}</span>
  <h1>{title}</h1>
  <div class="meta-grid">
    <div class="meta-item">
      <span class="meta-label">Format</span>
      <span class="meta-value">{fmt}</span>
    </div>
    <div class="meta-item">
      <span class="meta-label">Category</span>
      <span class="meta-value">{cat}</span>
    </div>
    <div class="meta-item">
      <span class="meta-label">Credits</span>
      <span class="meta-value">{credits}</span>
    </div>
    <div class="meta-item">
      <span class="meta-label">Section</span>
      <span class="meta-value">{section or '—'}</span>
    </div>
    <div class="meta-item">
      <span class="meta-label">Best Role Match</span>
      <span class="meta-value" style="color:{score_color(an['role_rows'][0]['b'] if an['role_rows'] else 0)}">
        {he(an['role_rows'][0]['role'] if an['role_rows'] else '—')}
        ({an['role_rows'][0]['b']:.1f} / 100)
      </span>
    </div>
    <div class="meta-item">
      <span class="meta-label">Avg Alignment</span>
      <span class="meta-value" style="color:{avg_col}">{an['avg_b']:.1f} / 100</span>
    </div>
    {f'<div class="spec-line"><span class="meta-label" style="display:inline">Specialization</span> {spec}</div>' if spec else ''}
  </div>
</div>

<!-- Stat tiles -->
<div class="stat-row">
  <div class="stat-tile">
    <div class="stat-val" style="color:{avg_col}">{an['avg_b']:.0f}</div>
    <div class="stat-lbl">Current Avg Score</div>
    <div class="stat-sub">across 6 job roles</div>
  </div>
  <div class="stat-tile">
    <div class="stat-val" style="color:{pot_col}">{an['avg_a']:.0f}</div>
    <div class="stat-lbl">Potential Score</div>
    <div class="stat-sub">with recommended additions</div>
  </div>
  <div class="stat-tile">
    <div class="stat-val" style="color:{delta_col}">+{an['max_d']:.0f}</div>
    <div class="stat-lbl">Max Score Gain</div>
    <div class="stat-sub">best single-role improvement</div>
  </div>
</div>

<!-- Current description -->
{f'<h2>Current Course Description</h2><div class="desc-box">{he(desc)}</div>' if desc else ''}

<!-- Alignment table -->
<h2>Industry Alignment by Job Role</h2>
<table>
  <thead>
    <tr>
      <th>Job Role</th>
      <th>Current Score</th>
      <th>Projected Score</th>
      <th>Point Gain</th>
      <th>Priority</th>
    </tr>
  </thead>
  <tbody>{role_rows_html}</tbody>
</table>

<!-- Recommended topics -->
<h2>Recommended Topics to Add</h2>
<p style="font-size:8pt;color:#7A8AAA;margin-bottom:9pt">
  Keywords highlighted in gold (
  <span style="font-family:IBM Plex Mono,monospace;font-size:7pt;background:#FDF5E6;border:1px solid #CFB87C88;color:#7A5C1A;padding:1pt 4pt;border-radius:3pt">example</span>
  ) appear as gaps across 3 or more job roles.
</p>
<div class="topics-grid">{topics_html}</div>

<!-- Priority recommendations -->
<h2>Priority Recommendations for Instructors</h2>
<ul class="rec-list">{recs_html}</ul>

<!-- Gap keywords by role -->
{('<h2>Gap Keywords by Role</h2>' + gap_html) if gap_html else ''}

<!-- Methodology note -->
<div class="methodology">
  <strong>Methodology:</strong> Scores (0–100) reflect TF-IDF cosine similarity between course catalog
  descriptions and a corpus of 100 LinkedIn data science job postings (collected June 2026, filtered to
  postings with ≥200 applicants). Gap keywords are terms that appear frequently in job postings for a given
  role but are absent or underrepresented in the current course description. "Projected score" shows the
  estimated alignment after integrating the top 5 suggested keywords. Analysis was conducted by the CU
  Boulder MSDS Curriculum–Industry Alignment project team.
</div>

<div class="doc-footer">
  <span>CU Boulder MSDS · Curriculum Alignment Analysis · September 2026</span>
  <span>Analysis of 100 LinkedIn job postings · 6 job roles · 130 courses</span>
</div>

</body>
</html>"""


# ── Generate PDFs ─────────────────────────────────────────────────────────────
def generate_all(limit=None):
    from playwright.sync_api import sync_playwright

    codes = list(SUGG['courses'].keys())
    if limit:
        codes = codes[:limit]

    total = len(codes)
    errors = []

    with sync_playwright() as p:
        browser = p.chromium.launch()
        context = browser.new_context()
        page = context.new_page()

        for i, code in enumerate(codes, 1):
            entry = SUGG['courses'][code]
            meta = META.get(code, {})
            an = analyse(code, entry, meta)
            html = build_html(code, entry, meta, an)

            safe_code = code.replace(' ', '_').replace('/', '_')
            out_path = PDF_DIR / f"{safe_code}.pdf"

            try:
                page.set_content(html, wait_until='networkidle', timeout=15000)
                # Wait for fonts
                page.wait_for_timeout(800)

                page.pdf(
                    path=str(out_path),
                    format='Letter',
                    print_background=True,
                    margin={
                        'top': '0.75in',
                        'bottom': '0.85in',
                        'left': '0.85in',
                        'right': '0.85in',
                    },
                    display_header_footer=True,
                    header_template='''
                        <div style="width:100%;font-family:monospace;font-size:8px;
                                    color:#9AAABA;text-align:center;padding-top:6px;
                                    letter-spacing:.05em">
                          CU BOULDER MSDS &nbsp;·&nbsp; CURRICULUM–INDUSTRY ALIGNMENT REPORT
                        </div>''',
                    footer_template='''
                        <div style="width:100%;font-family:monospace;font-size:8px;
                                    color:#9AAABA;display:flex;justify-content:space-between;
                                    padding:6px 40px 0">
                          <span class="title" style="max-width:60%;overflow:hidden;white-space:nowrap;text-overflow:ellipsis"></span>
                          <span>Page <span class="pageNumber"></span> of <span class="totalPages"></span></span>
                        </div>''',
                )
                size_kb = out_path.stat().st_size // 1024
                print(f"  [{i:3d}/{total}] ✓  {safe_code}.pdf  ({size_kb} KB)")
            except Exception as e:
                print(f"  [{i:3d}/{total}] ✗  {safe_code}: {e}")
                errors.append((code, str(e)))

        browser.close()

    return errors


if __name__ == '__main__':
    limit = int(sys.argv[1]) if len(sys.argv) > 1 else None
    print(f"Generating PDF reports → {PDF_DIR}")
    print(f"Courses: {limit or len(SUGG['courses'])}")
    t0 = time.time()

    errors = generate_all(limit)

    elapsed = time.time() - t0
    pdfs = list(PDF_DIR.glob('*.pdf'))
    total_mb = sum(f.stat().st_size for f in pdfs) / 1024 / 1024

    print(f"\n{'='*50}")
    print(f"Generated: {len(pdfs)} PDFs")
    print(f"Total size: {total_mb:.1f} MB")
    print(f"Time: {elapsed:.0f}s ({elapsed/len(pdfs):.1f}s avg)" if pdfs else "")
    if errors:
        print(f"Errors ({len(errors)}):")
        for code, err in errors:
            print(f"  {code}: {err}")
    else:
        print("No errors.")
    print(f"Output: {PDF_DIR}/")
