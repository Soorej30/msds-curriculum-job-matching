#!/usr/bin/env python3
"""
Generate per-course professor feedback reports.

Outputs:
  course_reports/DTSA_5509.html  (one per course)
  course_reports/index.html      (navigation index)
"""

import json
import os
import math
from pathlib import Path
from collections import defaultdict
from html import escape as he

# ── Load data ─────────────────────────────────────────────────────────────────
BASE = Path(__file__).parent
with open(BASE / 'msds_suggestions.json') as f:
    SUGG = json.load(f)
with open(BASE / 'cu_boulder_msds_courses.json') as f:
    CDATA = json.load(f)

ROLES = SUGG['meta']['role_labels']
OUTDIR = BASE / 'course_reports'
OUTDIR.mkdir(exist_ok=True)

# Build course metadata lookup
ALL_COURSES = []
for c in CDATA['courses']['online_dtsa']:
    ALL_COURSES.append({**c, 'format_label': 'Online (DTSA)'})
for c in CDATA['courses']['on_campus_electives']:
    ALL_COURSES.append({**c, 'format_label': 'On-Campus'})
META = {c['course_code']: c for c in ALL_COURSES}

# ── Keyword → Topic mapping ───────────────────────────────────────────────────
TOPIC_MAP = {
    # Model lifecycle
    'deployment':         'Model Deployment & Serving',
    'deploy':             'Model Deployment & Serving',
    'serving':            'Model Deployment & Serving',
    'inference':          'Model Deployment & Serving',
    'production':         'Model Deployment & Serving',
    'endpoint':           'Model Deployment & Serving',
    'api':                'Model Deployment & Serving',
    'rest':               'Model Deployment & Serving',
    'flask':              'Model Deployment & Serving',
    'fastapi':            'Model Deployment & Serving',
    'microservice':       'Model Deployment & Serving',
    # MLOps
    'mlops':              'MLOps & Pipeline Engineering',
    'mlflow':             'MLOps & Pipeline Engineering',
    'kubeflow':           'MLOps & Pipeline Engineering',
    'airflow':            'MLOps & Pipeline Engineering',
    'pipeline':           'MLOps & Pipeline Engineering',
    'orchestration':      'MLOps & Pipeline Engineering',
    'kubernetes':         'MLOps & Pipeline Engineering',
    'docker':             'MLOps & Pipeline Engineering',
    'container':          'MLOps & Pipeline Engineering',
    'cicd':               'MLOps & Pipeline Engineering',
    'monitoring':         'MLOps & Pipeline Engineering',
    'workflow':           'MLOps & Pipeline Engineering',
    'drift':              'MLOps & Pipeline Engineering',
    # Cloud
    'aws':                'Cloud Platforms',
    'azure':              'Cloud Platforms',
    'gcp':                'Cloud Platforms',
    'cloud':              'Cloud Platforms',
    'sagemaker':          'Cloud Platforms',
    'vertex':             'Cloud Platforms',
    'databricks':         'Cloud Platforms',
    'snowflake':          'Cloud Platforms',
    's3':                 'Cloud Platforms',
    'lambda':             'Cloud Platforms',
    'ec2':                'Cloud Platforms',
    # Deep Learning
    'neural':             'Deep Learning',
    'deep':               'Deep Learning',
    'cnn':                'Deep Learning',
    'rnn':                'Deep Learning',
    'lstm':               'Deep Learning',
    'transformer':        'Deep Learning',
    'attention':          'Deep Learning',
    'backpropagation':    'Deep Learning',
    'gradient':           'Deep Learning',
    'pytorch':            'Deep Learning',
    'tensorflow':         'Deep Learning',
    'keras':              'Deep Learning',
    'training':           'Deep Learning',
    'epoch':              'Deep Learning',
    'batch':              'Deep Learning',
    # LLMs & GenAI
    'llm':                'LLMs & Generative AI',
    'gpt':                'LLMs & Generative AI',
    'generative':         'LLMs & Generative AI',
    'prompt':             'LLMs & Generative AI',
    'fine-tuning':        'LLMs & Generative AI',
    'rag':                'LLMs & Generative AI',
    'embedding':          'LLMs & Generative AI',
    'foundation':         'LLMs & Generative AI',
    'bert':               'LLMs & Generative AI',
    'language model':     'LLMs & Generative AI',
    'chatgpt':            'LLMs & Generative AI',
    'langchain':          'LLMs & Generative AI',
    # Data Engineering
    'spark':              'Data Engineering & Scalability',
    'kafka':              'Data Engineering & Scalability',
    'etl':                'Data Engineering & Scalability',
    'streaming':          'Data Engineering & Scalability',
    'hadoop':             'Data Engineering & Scalability',
    'hive':               'Data Engineering & Scalability',
    'ingestion':          'Data Engineering & Scalability',
    'distributed':        'Data Engineering & Scalability',
    'scalab':             'Data Engineering & Scalability',
    # Experimentation
    'experiment':         'Experiment Tracking & Reproducibility',
    'tracking':           'Experiment Tracking & Reproducibility',
    'versioning':         'Experiment Tracking & Reproducibility',
    'reproducib':         'Experiment Tracking & Reproducibility',
    'wandb':              'Experiment Tracking & Reproducibility',
    # Evaluation
    'evaluation':         'Model Evaluation & Testing',
    'benchmark':          'Model Evaluation & Testing',
    'validation':         'Model Evaluation & Testing',
    'accuracy':           'Model Evaluation & Testing',
    'precision':          'Model Evaluation & Testing',
    'recall':             'Model Evaluation & Testing',
    'auc':                'Model Evaluation & Testing',
    'f1':                 'Model Evaluation & Testing',
    'bias':               'Model Evaluation & Testing',
    'fairness':           'Model Evaluation & Testing',
    # Feature engineering
    'feature':            'Feature Engineering & Data Preparation',
    'engineering':        'Feature Engineering & Data Preparation',
    'preprocessing':      'Feature Engineering & Data Preparation',
    'encoding':           'Feature Engineering & Data Preparation',
    'imputation':         'Feature Engineering & Data Preparation',
    'normalization':      'Feature Engineering & Data Preparation',
    'scaling':            'Feature Engineering & Data Preparation',
    # Business & Communication
    'stakeholder':        'Business Communication & Leadership',
    'communication':      'Business Communication & Leadership',
    'business':           'Business Communication & Leadership',
    'strategy':           'Business Communication & Leadership',
    'leadership':         'Business Communication & Leadership',
    'presentation':       'Business Communication & Leadership',
    'storytelling':       'Business Communication & Leadership',
    'insight':            'Business Communication & Leadership',
    'decision':           'Business Communication & Leadership',
    # Statistics
    'hypothesis':         'Statistical Analysis & Inference',
    'inference':          'Statistical Analysis & Inference',
    'bayesian':           'Statistical Analysis & Inference',
    'significance':       'Statistical Analysis & Inference',
    'distribution':       'Statistical Analysis & Inference',
    'sampling':           'Statistical Analysis & Inference',
    'causal':             'Statistical Analysis & Inference',
    # NLP
    'nlp':                'Natural Language Processing',
    'text':               'Natural Language Processing',
    'sentiment':          'Natural Language Processing',
    'tokenization':       'Natural Language Processing',
    'named entity':       'Natural Language Processing',
    # Computer Vision
    'vision':             'Computer Vision',
    'image':              'Computer Vision',
    'object detection':   'Computer Vision',
    'segmentation':       'Computer Vision',
    'opencv':             'Computer Vision',
    # SQL & Data
    'sql':                'SQL & Database Skills',
    'query':              'SQL & Database Skills',
    'database':           'SQL & Database Skills',
    'postgres':           'SQL & Database Skills',
    'nosql':              'SQL & Database Skills',
    # Software engineering
    'software':           'Software Engineering Practices',
    'git':                'Software Engineering Practices',
    'testing':            'Software Engineering Practices',
    'debugging':          'Software Engineering Practices',
    'refactor':           'Software Engineering Practices',
    'clean code':         'Software Engineering Practices',
    # Optimization
    'optimization':       'Optimization & Hyperparameter Tuning',
    'hyperparameter':     'Optimization & Hyperparameter Tuning',
    'tuning':             'Optimization & Hyperparameter Tuning',
    'search':             'Optimization & Hyperparameter Tuning',
    'regularization':     'Optimization & Hyperparameter Tuning',
    # Systems / Architecture
    'architecture':       'System Design & Scalability',
    'design':             'System Design & Scalability',
    'systems':            'System Design & Scalability',
    'real-time':          'System Design & Scalability',
    'latency':            'System Design & Scalability',
    'throughput':         'System Design & Scalability',
    'scale':              'System Design & Scalability',
}

def find_topic(word):
    wl = word.lower()
    for kw, topic in TOPIC_MAP.items():
        if kw in wl or wl.startswith(kw):
            return topic
    return None

def score_bar(score, max_score=100):
    pct = min(100, (score / max_score) * 100)
    color = '#16A34A' if score >= 70 else '#D97706' if score >= 40 else '#CC3333'
    return (
        f'<div class="bar-wrap">'
        f'<div class="bar" style="width:{pct:.1f}%;background:{color}"></div>'
        f'</div>'
        f'<span class="bar-num" style="color:{color}">{score:.1f}</span>'
    )

def priority_label(delta):
    if delta >= 30:
        return '<span class="pri high">HIGH</span>'
    elif delta >= 15:
        return '<span class="pri medium">MEDIUM</span>'
    else:
        return '<span class="pri low">LOW</span>'

def analyse_course(code, entry, meta):
    """Return structured analysis for one course."""
    roles_data = entry['roles']

    # Per-role summary
    role_rows = []
    for role in ROLES:
        rd = roles_data.get(role)
        if rd:
            role_rows.append({
                'role': role,
                'before': rd['before'],
                'after':  rd['after'],
                'delta':  rd['delta'],
                'kw_count': len(rd.get('keywords', [])),
            })

    role_rows.sort(key=lambda r: -r['before'])
    best_role = role_rows[0]['role'] if role_rows else 'N/A'
    best_score = role_rows[0]['before'] if role_rows else 0
    avg_before = sum(r['before'] for r in role_rows) / len(role_rows) if role_rows else 0
    avg_potential = sum(r['after'] for r in role_rows) / len(role_rows) if role_rows else 0
    max_delta = max((r['delta'] for r in role_rows), default=0)

    # Cross-role keyword priority
    kw_role_map = defaultdict(lambda: {'total_demand': 0.0, 'roles': [], 'role_count': 0})
    for role in ROLES:
        rd = roles_data.get(role)
        if not rd:
            continue
        for kw_entry in rd.get('keywords', []):
            word = kw_entry['word']
            demand = kw_entry['demand']
            kw_role_map[word]['total_demand'] += demand
            kw_role_map[word]['roles'].append(role)
            kw_role_map[word]['role_count'] += 1

    # Sort by (role_count DESC, total_demand DESC)
    sorted_kws = sorted(
        kw_role_map.items(),
        key=lambda x: (-x[1]['role_count'], -x[1]['total_demand'])
    )

    # Group into topics
    topic_kws = defaultdict(list)
    unclassified = []
    for word, data in sorted_kws:
        topic = find_topic(word)
        if topic:
            topic_kws[topic].append({
                'word': word,
                'role_count': data['role_count'],
                'total_demand': data['total_demand'],
                'roles': data['roles'],
            })
        else:
            unclassified.append({
                'word': word,
                'role_count': data['role_count'],
                'total_demand': data['total_demand'],
                'roles': data['roles'],
            })

    # Sort topics by total demand
    topic_summary = []
    for topic, kws in topic_kws.items():
        total = sum(k['total_demand'] for k in kws)
        max_rc = max(k['role_count'] for k in kws)
        topic_summary.append({
            'topic': topic,
            'keywords': sorted(kws, key=lambda k: -k['role_count']),
            'total_demand': total,
            'max_role_count': max_rc,
        })
    topic_summary.sort(key=lambda t: (-t['max_role_count'], -t['total_demand']))

    return {
        'role_rows': role_rows,
        'best_role': best_role,
        'best_score': best_score,
        'avg_before': avg_before,
        'avg_potential': avg_potential,
        'max_delta': max_delta,
        'topic_summary': topic_summary[:8],       # top 8 topics
        'top_cross_kws': sorted_kws[:20],         # top 20 cross-role keywords
        'unclassified_kws': unclassified[:10],
        'all_kws_count': len(sorted_kws),
    }

# ── Shared CSS ────────────────────────────────────────────────────────────────
COMMON_CSS = """
* { box-sizing: border-box; margin: 0; padding: 0; }
body {
  font-family: 'Segoe UI', system-ui, -apple-system, sans-serif;
  font-size: 13.5px; line-height: 1.6;
  color: #1A2035; background: #fff;
  max-width: 860px; margin: 0 auto; padding: 2.5rem 2rem;
}
@media print {
  body { padding: 1rem; max-width: 100%; }
  .no-print { display: none !important; }
  a { color: inherit; text-decoration: none; }
}

/* Header */
.report-header {
  border-left: 5px solid #CFB87C;
  padding: 1rem 1.25rem 1rem 1.5rem;
  background: #FAFAF7;
  margin-bottom: 1.75rem;
  border-radius: 0 8px 8px 0;
}
.report-header h1 {
  font-size: 1.3rem; color: #1B2A4A; font-weight: 700; margin-bottom: .25rem;
}
.report-header h1 span { color: #CFB87C; }
.report-header .meta-row {
  display: flex; gap: 1.5rem; flex-wrap: wrap; font-size: .8rem; color: #5A6A8A;
}
.report-header .meta-row strong { color: #1A2035; }

.watermark {
  font-size: .7rem; color: #aaa; margin-bottom: 1.5rem;
  padding-bottom: .75rem; border-bottom: 1px solid #eee;
}

/* Section headings */
h2 {
  font-size: .95rem; font-weight: 700; color: #1B2A4A;
  text-transform: uppercase; letter-spacing: .08em;
  margin: 1.75rem 0 .75rem; padding-bottom: .35rem;
  border-bottom: 2px solid #CFB87C;
}
h3 {
  font-size: .88rem; font-weight: 600; color: #2A3D6A;
  margin: 1rem 0 .4rem;
}

/* Summary badges */
.summary-grid {
  display: grid; grid-template-columns: repeat(3, 1fr); gap: .75rem;
  margin-bottom: 1.5rem;
}
.summary-card {
  border: 1px solid #E0E6F0; border-radius: 8px; padding: .75rem 1rem;
  text-align: center;
}
.summary-card .val {
  font-size: 1.6rem; font-weight: 800; color: #1B2A4A;
  font-variant-numeric: tabular-nums;
}
.summary-card .val.gold { color: #CFB87C; }
.summary-card .val.green { color: #16A34A; }
.summary-card .val.amber { color: #D97706; }
.summary-card .lbl { font-size: .7rem; color: #7A8AAA; text-transform: uppercase; letter-spacing: .06em; margin-top: .15rem; }
.summary-card .sub { font-size: .72rem; color: #5A6A8A; margin-top: .2rem; }

/* Alignment table */
table { width: 100%; border-collapse: collapse; font-size: .82rem; margin: .5rem 0 1.25rem; }
th {
  background: #F0F4FA; color: #2A3D6A;
  text-align: left; padding: .45rem .7rem;
  font-size: .72rem; letter-spacing: .06em; text-transform: uppercase;
  border: 1px solid #DDE3EF;
}
td { padding: .4rem .7rem; border: 1px solid #DDE3EF; vertical-align: middle; }
tr:hover td { background: #F7F9FC; }

/* Bar */
.bar-wrap { display: inline-block; width: 90px; height: 8px; background: #E8EDF5; border-radius: 4px; vertical-align: middle; margin-right: 6px; }
.bar { height: 100%; border-radius: 4px; transition: width .3s; }
.bar-num { font-variant-numeric: tabular-nums; font-weight: 700; font-size: .83rem; }

/* Priority badge */
.pri { font-size: .65rem; font-weight: 700; letter-spacing: .06em;
       padding: .1rem .4rem; border-radius: 99px; text-transform: uppercase; }
.pri.high   { background: #FEF2F2; color: #991B1B; }
.pri.medium { background: #FFFBEB; color: #92400E; }
.pri.low    { background: #F0FDF4; color: #166534; }

/* Topic cards */
.topic-grid { display: grid; grid-template-columns: 1fr 1fr; gap: .75rem; margin: .5rem 0 1.25rem; }
@media (max-width: 600px) { .topic-grid { grid-template-columns: 1fr; } }
.topic-card {
  border: 1px solid #E0E6F0; border-radius: 8px; padding: .75rem;
}
.topic-card .topic-name {
  font-size: .78rem; font-weight: 700; color: #1B2A4A; margin-bottom: .4rem;
  display: flex; align-items: center; gap: .4rem;
}
.topic-card .topic-name .roles-badge {
  background: #CFB87C22; border: 1px solid #CFB87C66;
  color: #7A5C1A; font-size: .62rem; padding: .05rem .35rem; border-radius: 99px;
}
.kw-chips { display: flex; flex-wrap: wrap; gap: .3rem; }
.kw-chip {
  background: #F0F4FA; border: 1px solid #DDE3EF;
  color: #2A3D6A; font-size: .68rem; padding: .12rem .4rem; border-radius: 4px;
}
.kw-chip.cross { background: #FEF9EE; border-color: #CFB87C; color: #7A5C1A; }

/* Recommendations */
.rec-list { list-style: none; margin: .5rem 0 1.25rem; }
.rec-list li {
  display: flex; gap: .6rem; align-items: flex-start;
  padding: .6rem .75rem; border-left: 3px solid #CFB87C;
  background: #FDFCF8; margin-bottom: .5rem; border-radius: 0 6px 6px 0;
  font-size: .83rem;
}
.rec-list li .rec-num {
  background: #CFB87C; color: #1B2A4A; font-size: .65rem; font-weight: 800;
  min-width: 1.3rem; height: 1.3rem; border-radius: 50%;
  display: flex; align-items: center; justify-content: center; flex-shrink: 0;
  margin-top: .05rem;
}
.rec-list li .rec-body { flex: 1; }
.rec-list li .rec-body strong { color: #1B2A4A; }
.rec-list li .rec-body .rec-kws {
  margin-top: .2rem; font-size: .73rem; color: #5A6A8A;
}

/* Role-specific section */
.role-section { margin-bottom: 1rem; }
.role-section h3 { margin: 0; }
.role-section .role-kws { margin-top: .35rem; }

/* Description box */
.desc-box {
  background: #F7F9FC; border: 1px solid #DDE3EF;
  border-radius: 6px; padding: .7rem 1rem; font-size: .81rem;
  color: #3D4A6B; margin-bottom: 1.25rem; line-height: 1.6;
}

/* Footer */
.report-footer {
  margin-top: 2rem; padding-top: .75rem; border-top: 1px solid #E0E6F0;
  font-size: .72rem; color: #9AAABA; text-align: center;
}

/* Back link */
.back-link {
  display: inline-block; margin-bottom: 1.5rem; font-size: .78rem;
  color: #CFB87C; text-decoration: none; border: 1px solid #CFB87C;
  padding: .25rem .6rem; border-radius: 4px;
}
.back-link:hover { background: #CFB87C; color: #1B2A4A; }
"""

def generate_course_report(code, entry, meta):
    an = analyse_course(code, entry, meta)

    title = he(entry.get('title', code))
    section = he(meta.get('program_section', ''))
    spec = he(meta.get('specialization', ''))
    fmt = he(meta.get('format_label', ''))
    credits = meta.get('credits', '—')
    description = he((meta.get('description') or meta.get('catalog_description') or '').strip())

    # ── summary cards ──────────────────────────────────────────────────────────
    avg_col = 'green' if an['avg_before'] >= 70 else 'amber' if an['avg_before'] >= 40 else ''
    pot_col = 'green' if an['avg_potential'] >= 70 else ''
    delta_col = 'amber' if an['max_delta'] >= 30 else 'green'
    summary_cards = f"""
<div class="summary-grid">
  <div class="summary-card">
    <div class="val {avg_col}">{an['avg_before']:.0f}</div>
    <div class="lbl">Avg Alignment Score</div>
    <div class="sub">across all 6 roles</div>
  </div>
  <div class="summary-card">
    <div class="val {pot_col}">{an['avg_potential']:.0f}</div>
    <div class="lbl">Avg Potential Score</div>
    <div class="sub">with recommended additions</div>
  </div>
  <div class="summary-card">
    <div class="val {delta_col}">+{an['max_delta']:.0f}</div>
    <div class="lbl">Max Score Gain</div>
    <div class="sub">best single-role improvement</div>
  </div>
</div>"""

    # ── alignment table ────────────────────────────────────────────────────────
    rows_html = ''
    for r in an['role_rows']:
        rows_html += f"""<tr>
  <td><strong>{he(r['role'])}</strong></td>
  <td>{score_bar(r['before'])}</td>
  <td>{score_bar(r['after'])}</td>
  <td style="font-weight:700;color:#D97706">+{r['delta']:.1f}</td>
  <td>{priority_label(r['delta'])}</td>
</tr>"""
    align_table = f"""
<table>
  <thead><tr>
    <th>Job Role</th><th>Current Score</th><th>After Additions</th><th>Gain</th><th>Priority</th>
  </tr></thead>
  <tbody>{rows_html}</tbody>
</table>"""

    # ── topic recommendations ─────────────────────────────────────────────────
    topic_cards = ''
    for t in an['topic_summary'][:8]:
        top_kws = t['keywords'][:8]
        kw_html = ''.join(
            f'<span class="kw-chip {"cross" if k["role_count"] >= 3 else ""}">'
            f'{he(k["word"])}</span>'
            for k in top_kws
        )
        roles_count = t['max_role_count']
        topic_cards += f"""
<div class="topic-card">
  <div class="topic-name">
    {he(t['topic'])}
    <span class="roles-badge">{roles_count} of 6 roles</span>
  </div>
  <div class="kw-chips">{kw_html}</div>
</div>"""

    # ── action recommendations ─────────────────────────────────────────────────
    recs = []
    priority_topics = [t for t in an['topic_summary'] if t['max_role_count'] >= 3]
    medium_topics = [t for t in an['topic_summary'] if t['max_role_count'] == 2]
    low_topics = [t for t in an['topic_summary'] if t['max_role_count'] == 1]

    for t in priority_topics[:4]:
        kw_sample = ', '.join(k['word'] for k in t['keywords'][:6])
        roles_affected = list({r for k in t['keywords'] for r in k['roles']})[:4]
        recs.append(('HIGH', t['topic'],
                     f'Needed by {len(roles_affected)}+ job roles. '
                     f'Consider adding coverage of: <em>{he(kw_sample)}</em>.',
                     kw_sample))

    for t in medium_topics[:2]:
        kw_sample = ', '.join(k['word'] for k in t['keywords'][:5])
        recs.append(('MEDIUM', t['topic'],
                     f'Relevant to 2 industry roles. '
                     f'Could be introduced through labs or case studies: <em>{he(kw_sample)}</em>.',
                     kw_sample))

    for t in low_topics[:2]:
        kw_sample = ', '.join(k['word'] for k in t['keywords'][:4])
        recs.append(('LOW', t['topic'],
                     f'Optional but would broaden student appeal. '
                     f'May fit as optional reading/project: <em>{he(kw_sample)}</em>.',
                     kw_sample))

    # Fallback if no topics matched
    if not recs and an['top_cross_kws']:
        top_words = ', '.join(w for w, _ in an['top_cross_kws'][:8])
        recs.append(('MEDIUM', 'Industry-Relevant Terminology',
                     f'Incorporate the following industry terms into lectures, assignments, or readings: <em>{he(top_words)}</em>.',
                     top_words))

    recs_html = ''
    for i, (pri, topic, body, kws) in enumerate(recs, 1):
        pri_class = pri.lower()
        recs_html += f"""<li>
  <div class="rec-num">{i}</div>
  <div class="rec-body">
    <strong>{he(topic)}</strong>
    <span class="pri {pri_class}">{pri}</span><br>
    {body}
  </div>
</li>"""

    # ── per-role keyword breakdown ─────────────────────────────────────────────
    role_sections = ''
    for r in an['role_rows']:
        if r['delta'] < 5:
            continue
        rd = entry['roles'].get(r['role'], {})
        kws = rd.get('keywords', [])[:10]
        if not kws:
            continue
        kw_chips = ''.join(
            f'<span class="kw-chip">{he(k["word"])}</span>'
            for k in kws
        )
        role_sections += f"""
<div class="role-section">
  <h3>{he(r['role'])} — gap keywords <small style="font-weight:400;color:#7A8AAA">(current: {r['before']:.1f} → potential: {r['after']:.1f})</small></h3>
  <div class="role-kws kw-chips">{kw_chips}</div>
</div>"""

    # ── assemble HTML ──────────────────────────────────────────────────────────
    safe_code = code.replace(' ', '_')
    is_core = 'section 4' not in section.lower() and 'elective' not in section.lower()
    cat_badge = '🔵 Core' if is_core else '🟡 Elective'

    html = f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>Curriculum Feedback: {he(code)}</title>
<style>{COMMON_CSS}</style>
</head>
<body>

<a href="index.html" class="back-link no-print">← Back to all courses</a>

<div class="report-header">
  <h1><span>{he(code)}</span> – {title}</h1>
  <div class="meta-row">
    <span><strong>Format:</strong> {fmt}</span>
    <span><strong>Section:</strong> {section or 'N/A'}</span>
    <span><strong>Credits:</strong> {credits}</span>
    <span><strong>Category:</strong> {cat_badge}</span>
    <span><strong>Best Role Match:</strong> {he(an['best_role'])} ({an['best_score']:.1f})</span>
  </div>
  {f'<div class="meta-row" style="margin-top:.4rem"><span><strong>Specialization:</strong> {spec}</span></div>' if spec else ''}
</div>

<div class="watermark">
  MSDS Curriculum × Industry Alignment Report · CU Boulder Data Science Program ·
  Based on analysis of 100 data science job postings (LinkedIn, June 2026)
</div>

{summary_cards}

{'<h2>Current Course Description</h2><div class="desc-box">' + description + '</div>' if description else ''}

<h2>Industry Alignment by Job Role</h2>
<p style="font-size:.8rem;color:#7A8AAA;margin-bottom:.75rem">
  Scores (0–100) measure TF-IDF cosine similarity between course content and job description vocabulary.
  "After Additions" shows the score if the top suggested keywords were integrated.
</p>
{align_table}

<h2>Recommended Topics to Add</h2>
<p style="font-size:.8rem;color:#7A8AAA;margin-bottom:.75rem">
  Topics below appear as gaps between this course and industry job postings.
  Highlighted chips (<span class="kw-chip cross" style="display:inline">example</span>) appear across 3+ job roles.
</p>
<div class="topic-grid">{topic_cards if topic_cards else '<p style="color:#9AA">No significant gaps identified — course is already well-aligned.</p>'}</div>

<h2>Priority Recommendations</h2>
<ul class="rec-list">{recs_html if recs_html else '<li><div class="rec-num">✓</div><div class="rec-body">This course is already well-aligned with industry expectations. Focus on maintaining currency with evolving tools and frameworks.</div></li>'}</ul>

{('<h2>Gap Keywords by Job Role</h2>' + role_sections) if role_sections else ''}

<div class="report-footer">
  Generated by the CU Boulder MSDS Curriculum Alignment Analysis · 2026 ·
  Contact the data science program team for methodology details.
</div>

</body>
</html>"""
    return html

# ── Generate all course reports ───────────────────────────────────────────────
print(f"Generating reports for {len(SUGG['courses'])} courses …")
index_rows = []

for code, entry in sorted(SUGG['courses'].items()):
    meta = META.get(code, {})
    html = generate_course_report(code, entry, meta)

    safe_code = code.replace(' ', '_').replace('/', '_')
    fname = f"{safe_code}.html"
    (OUTDIR / fname).write_text(html, encoding='utf-8')

    section = meta.get('program_section', '')
    is_core = 'section 4' not in section.lower() and 'elective' not in section.lower()
    avg_b = sum(entry['roles'][r]['before'] for r in ROLES if r in entry['roles']) / len(ROLES)
    max_d = max((entry['roles'][r]['delta'] for r in ROLES if r in entry['roles']), default=0)

    index_rows.append({
        'code': code,
        'title': entry.get('title', code),
        'fname': fname,
        'format': meta.get('format_label', ''),
        'section': section,
        'is_core': is_core,
        'avg_score': avg_b,
        'max_delta': max_d,
    })
    print(f"  ✓ {fname}")

print(f"\nGenerating index …")

# Sort index: Core first, then by avg_score desc
index_rows.sort(key=lambda r: (not r['is_core'], -r['avg_score']))

def score_chip(score):
    color = '#16A34A' if score >= 70 else '#D97706' if score >= 40 else '#CC3333'
    return f'<span style="font-weight:700;color:{color}">{score:.0f}</span>'

idx_rows_html = ''
for i, r in enumerate(index_rows, 1):
    cat = '🔵 Core' if r['is_core'] else '🟡 Elective'
    delta_col = '#CC3333' if r['max_delta'] >= 30 else '#D97706' if r['max_delta'] >= 15 else '#16A34A'
    idx_rows_html += f"""<tr>
  <td style="color:#9AA;font-size:.75rem">{i}</td>
  <td><a href="{r['fname']}" style="color:#1B2A4A;font-weight:600;text-decoration:none">{he(r['code'])}</a></td>
  <td style="font-size:.8rem">{he(r['title'][:55])}{'…' if len(r['title'])>55 else ''}</td>
  <td style="font-size:.75rem;color:#5A6A8A">{cat}</td>
  <td style="font-size:.75rem;color:#5A6A8A">{he(r['format'])}</td>
  <td>{score_chip(r['avg_score'])}</td>
  <td><span style="color:{delta_col};font-weight:700">+{r['max_delta']:.0f}</span></td>
  <td><a href="{r['fname']}" style="color:#CFB87C;font-size:.75rem;text-decoration:none">View →</a></td>
</tr>"""

index_html = f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>MSDS Curriculum Alignment — All Course Reports</title>
<style>
{COMMON_CSS}
body {{ max-width: 1100px; }}
.hero {{
  text-align: center; padding: 2.5rem 1rem 2rem;
  background: linear-gradient(135deg, #1B2A4A 0%, #2A3D6A 100%);
  border-radius: 12px; margin-bottom: 2rem; color: #fff;
}}
.hero h1 {{ font-size: 1.6rem; color: #CFB87C; margin-bottom: .5rem; }}
.hero p  {{ font-size: .88rem; opacity: .8; max-width: 55ch; margin: 0 auto; }}
.stat-row {{
  display: grid; grid-template-columns: repeat(4, 1fr); gap: 1rem; margin-bottom: 1.75rem;
}}
.stat-card {{
  border: 1px solid #E0E6F0; border-radius: 8px; padding: .75rem 1rem; text-align: center;
}}
.stat-card .v {{ font-size: 1.8rem; font-weight: 800; color: #CFB87C; }}
.stat-card .l {{ font-size: .7rem; color: #7A8AAA; text-transform: uppercase; letter-spacing: .06em; }}
input#search {{
  width: 100%; padding: .6rem 1rem; border: 1.5px solid #DDE3EF; border-radius: 8px;
  font-size: .85rem; margin-bottom: 1rem; outline: none;
  transition: border-color .15s;
}}
input#search:focus {{ border-color: #CFB87C; }}
table {{ font-size: .8rem; }}
th {{ cursor: pointer; user-select: none; }}
th:hover {{ background: #E5EAFA; }}
tbody tr:hover td {{ background: #F7F9FC; }}
</style>
</head>
<body>
<div class="hero">
  <h1>MSDS Curriculum Alignment Reports</h1>
  <p>Individual course feedback based on analysis of 100 data science job postings (LinkedIn, June 2026).
     Select a course below to view detailed industry alignment scores and recommended additions.</p>
</div>

<div class="stat-row">
  <div class="stat-card"><div class="v">{len(index_rows)}</div><div class="l">Courses Analysed</div></div>
  <div class="stat-card"><div class="v">6</div><div class="l">Job Roles</div></div>
  <div class="stat-card"><div class="v">100</div><div class="l">Job Postings</div></div>
  <div class="stat-card"><div class="v">{sum(1 for r in index_rows if r['is_core'])}</div><div class="l">Core Courses</div></div>
</div>

<h2>All Course Reports</h2>
<input id="search" type="search" placeholder="Search by code, title, or format…"
       oninput="filterTable(this.value)">

<table id="course-table">
  <thead>
    <tr>
      <th>#</th>
      <th onclick="sortBy(1)">Code ↕</th>
      <th onclick="sortBy(2)">Title ↕</th>
      <th onclick="sortBy(3)">Category ↕</th>
      <th onclick="sortBy(4)">Format ↕</th>
      <th onclick="sortBy(5)">Avg Score ↕</th>
      <th onclick="sortBy(6)">Max Gap ↕</th>
      <th>Report</th>
    </tr>
  </thead>
  <tbody>{idx_rows_html}</tbody>
</table>

<div class="report-footer">
  CU Boulder MSDS Curriculum Alignment Analysis · 2026 ·
  {len(index_rows)} courses · 6 job roles · 100 LinkedIn job postings
</div>

<script>
function filterTable(q) {{
  q = q.toLowerCase();
  document.querySelectorAll('#course-table tbody tr').forEach(tr => {{
    tr.style.display = tr.textContent.toLowerCase().includes(q) ? '' : 'none';
  }});
}}
let lastCol = -1, lastAsc = true;
function sortBy(col) {{
  const tbody = document.querySelector('#course-table tbody');
  const rows = [...tbody.querySelectorAll('tr')];
  const asc = (lastCol === col) ? !lastAsc : true;
  lastCol = col; lastAsc = asc;
  rows.sort((a, b) => {{
    const av = a.cells[col]?.textContent.trim() || '';
    const bv = b.cells[col]?.textContent.trim() || '';
    const an = parseFloat(av), bn = parseFloat(bv);
    if (!isNaN(an) && !isNaN(bn)) return asc ? an-bn : bn-an;
    return asc ? av.localeCompare(bv) : bv.localeCompare(av);
  }});
  rows.forEach(r => tbody.appendChild(r));
}}
</script>
</body>
</html>"""

(OUTDIR / 'index.html').write_text(index_html, encoding='utf-8')

print(f"\n✓ Done! {len(index_rows)} course reports + index.html")
print(f"  Output: {OUTDIR}/")
