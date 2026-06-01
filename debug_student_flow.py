from app import create_app, db
from app.models import Student

app = create_app()
with app.app_context():
    print('App created')
    student = Student.query.filter_by(student_number='S000').first()
    print('Student:', student)

    client = app.test_client()
    rv = client.post('/student/login', data={'student_number': 'S000', 'password': 'pass123'}, follow_redirects=True)
    print('/student/login status', rv.status_code)
    print(rv.data.decode('utf-8')[:800])
    rv2 = client.get('/student')
    print('/student GET status', rv2.status_code)
    print(rv2.data.decode('utf-8')[:800])
    rv3 = client.post('/student', data={
        'action': 'submit',
        'company_name': 'Test Co',
        'business_nature': 'IT',
        'validity': '1 year',
        'expiration_date': '2030-01-01',
        'has_resume': 'on',
        'has_med_cert': 'on',
        'has_consent_form': 'on',
        'has_moa': 'on',
        'has_insurance': 'on',
        'has_intent_letter': 'on',
        'has_endorsement_letter': 'on',
    }, follow_redirects=True)
    print('/student POST status', rv3.status_code)
    print(rv3.data.decode('utf-8')[:800])
