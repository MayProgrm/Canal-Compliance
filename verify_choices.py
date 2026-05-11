
import os
import django
from django.conf import settings

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'canal_denuncias.settings')
django.setup()

from denuncias.models import Complaint
from denuncias.forms import ComplaintForm

print("Checking Complaint.CATEGORY_CHOICES:")
for key, label in Complaint.CATEGORY_CHOICES:
    print(f"  Key: '{key}', Label: '{label}'")

print("\nChecking compute_severity logic:")
test_cases = [
    'Acoso laboral (mobbing)',
    'Extorsión',
    'Fraude y corrupción',
    'Consulta general'
]

c = Complaint()
for cat in test_cases:
    c.category = cat
    sev = c.compute_severity()
    print(f"  Category: '{cat}' -> Severity: '{sev}'")

print("\nChecking ComplaintForm choices:")
form = ComplaintForm()
choices = form.fields['category'].choices
for group_name, options in choices:
    if isinstance(options, list):
        print(f"  Group: '{group_name}'")
        for key, label in options:
            print(f"    Key: '{key}', Label: '{label}'")
    else:
        print(f"  Option: '{group_name}', Label: '{options}'")
