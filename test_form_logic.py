import os
import django
from django.conf import settings

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'canal_denuncias.settings')
django.setup()

from denuncias.forms import ComplaintForm

def test_consulta():
    print("Testing Consulta logic...")
    data = {
        'relationship': 'Colaborador',
        'action_type': 'consulta',
        'reporting_mode': 'anonimo',
        'password': 'pass',
        'password_confirm': 'pass',
        # category is empty
        # incident fields empty
        'description': 'Consulta test',
        # other required bools
        'knows_actor': False,
        'has_witnesses': False,
        # Terms
        'terms_accept': 'on', # Not in form fields but checked in view? Form doesn't have terms_accept in fields list? 
        # Form fields: 'name', 'email', 'phone', 'reporter_matricula', 'category', 'relationship', ...
        # 'terms_accept' is likely handled in template/view or not in form class. 
        # Looking at ComplaintForm, it doesn't have terms_accept.
    }
    form = ComplaintForm(data=data)
    if form.is_valid():
        print("Consulta Form is Valid")
        print(f"Category: {form.cleaned_data.get('category')}")
        if form.cleaned_data.get('category') == 'Consulta general':
            print("SUCCESS: Category set to Consulta general")
        else:
            print(f"FAILURE: Category is {form.cleaned_data.get('category')}")
    else:
        print("Consulta Form is Invalid")
        print(form.errors)

def test_denuncia_missing_category():
    print("\nTesting Denuncia missing category...")
    data = {
        'relationship': 'Colaborador',
        'action_type': 'denuncia',
        'reporting_mode': 'anonimo',
        'password': 'pass',
        'password_confirm': 'pass',
        'description': 'Denuncia test',
        'knows_actor': False,
        'has_witnesses': False,
    }
    form = ComplaintForm(data=data)
    if not form.is_valid():
        if 'category' in form.errors:
            print("SUCCESS: Category is required for Denuncia")
        else:
            print(f"FAILURE: Unexpected errors: {form.errors}")
    else:
        print("FAILURE: Form should be invalid")

def test_denuncia_valid():
    print("\nTesting Denuncia valid...")
    data = {
        'relationship': 'Colaborador',
        'action_type': 'denuncia',
        'reporting_mode': 'anonimo',
        'password': 'pass',
        'password_confirm': 'pass',
        'category': 'Extorsión', # Valid choice
        'incident_state': 'CDMX',
        'incident_branch': 'Matriz',
        'incident_date': '2023-01-01',
        'incident_time': '12:00',
        'knows_actor': False,
        'has_witnesses': False,
        'description': 'Denuncia valid test',
    }
    form = ComplaintForm(data=data)
    if form.is_valid():
        print("Denuncia Form is Valid")
    else:
        print("Denuncia Form is Invalid")
        print(form.errors)

if __name__ == '__main__':
    test_consulta()
    test_denuncia_missing_category()
    test_denuncia_valid()
