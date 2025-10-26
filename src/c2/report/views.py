import os
import json
import datetime
import subprocess
import tempfile

from django.http import HttpResponse, JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.template import engines

# Django template engine for Jinja2
jinja_env = engines['jinja2']

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
LATEX_TEMPLATE_PATH = os.path.join(BASE_DIR, 'c2', 'report', 'templates', 'report_template.tex')

# Folder to save generated PDFs permanently
OUTPUT_DIR = os.path.join(BASE_DIR, 'generated_reports')
os.makedirs(OUTPUT_DIR, exist_ok=True)


def generate_chart(data_list, labels, out_path, chart_type='pie', title=None):
    """Generate bar or pie chart and save as PNG"""
    # Lazy import matplotlib only when needed
    import matplotlib
    matplotlib.use('Agg')
    import matplotlib.pyplot as plt
    
    plt.figure(figsize=(6,3))
    if chart_type == 'pie':
        plt.pie(data_list, labels=labels, autopct='%1.1f%%', colors=['#ff6b6b','#4b0082','#ffb347'])
    elif chart_type == 'bar':
        plt.bar(labels, data_list, color='#ff6b6b')
    if title:
        plt.title(title)
    plt.tight_layout()
    os.makedirs(os.path.dirname(out_path), exist_ok=True)
    plt.savefig(out_path, bbox_inches='tight', transparent=True)
    plt.close()


@csrf_exempt
def generate_report(request):
    if request.method != 'POST':
        return JsonResponse({'error': 'POST JSON only'}, status=405)
    
    try:
        payload = json.loads(request.body)
    except Exception as e:
        return JsonResponse({'error': 'Invalid JSON', 'detail': str(e)}, status=400)

    # Prepare context
    context = {
        "target_name": payload.get('recon_data', {}).get('hostname', 'UNKNOWN'),
        "generated_at": datetime.datetime.now(datetime.timezone.utc).strftime('%Y-%m-%d %H:%M UTC'),
        "sim_start": payload.get('sim_start', 'TBD'),
        "sim_end": payload.get('sim_end', 'TBD'),
        "exec_summary": payload.get('exec_summary', {}),
        "scope": payload.get('scope', {}),
        "recon_data": payload.get('recon_data', {}),
        "findings": payload.get('findings', []),
        "evasion": payload.get('evasion', {}),
        "attacks": payload.get('attacks', []),
        "mitigations": payload.get('mitigations', []),
        "raw_data": json.dumps(payload, indent=2),
        "charts": {},
    }

    # Generate evasion chart if data is present
    evasion_data = payload.get('evasion', {}).get('chart_data')
    if evasion_data:
        labels = [d['label'] for d in evasion_data]
        values = [d['value'] for d in evasion_data]

        chart_path = os.path.join(OUTPUT_DIR, 'evasion_chart.png')
        generate_chart(values, labels, chart_path, chart_type='pie', title='Evasion Success')
        context['charts']['evasion_chart'] = chart_path

    # Render LaTeX template
    template = jinja_env.get_template('report_template.tex')
    rendered_tex = template.render(context)

    tex_file = os.path.join(OUTPUT_DIR, f'report_{context["target_name"]}.tex')
    pdf_file = os.path.join(OUTPUT_DIR, f'RedTeamReport_{context["target_name"]}.pdf')

    # Move chart to OUTPUT_DIR if exists and use relative path
    if 'evasion_chart' in context['charts']:
        chart_dst = os.path.join(OUTPUT_DIR, 'evasion_chart.png')
        context['charts']['evasion_chart'] = 'evasion_chart.png'  # relative path for LaTeX

        # Write tex file
        with open(tex_file, 'w', encoding='utf-8') as f:
            f.write(template.render(context))
    else:
        with open(tex_file, 'w', encoding='utf-8') as f:
            f.write(rendered_tex)

    # Compile LaTeX
    try:
        subprocess.run(
            ['pdflatex', '-interaction=nonstopmode', tex_file],
            cwd=OUTPUT_DIR,
            check=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE
        )
    except subprocess.CalledProcessError as e:
        return JsonResponse({
            'error': 'LaTeX compilation failed',
            'stdout': e.stdout.decode(),
            'stderr': e.stderr.decode()
        }, status=500)

    # Return PDF
    with open(pdf_file, 'rb') as f:
        pdf_bytes = f.read()

    response = HttpResponse(pdf_bytes, content_type='application/pdf')
    response['Content-Disposition'] = f'attachment; filename="RedTeamReport_{context["target_name"]}.pdf"'
    return response
