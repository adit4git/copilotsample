from fastapi.testclient import TestClient
from app.main import app
c=TestClient(app)
def test_health():
 r=c.get('/api/health');assert r.status_code==200;assert r.json()['rules']==112
def test_book_isolated():
 d=c.get('/api/book?fa=marcus').json();assert len(d)==6;assert {x['advisor_id'] for x in d}=={'marcus'}
def test_household_payload():
 d=c.get('/api/household/henderson').json();assert d['id']=='henderson';assert d['program']=='IAP';assert 'transition' in d['verdicts']

def test_every_household_has_program_and_displayable_verdicts():
 for advisor in ('dana','marcus'):
  for row in c.get(f'/api/book?fa={advisor}').json():
   d=c.get(f'/api/household/{row["id"]}').json()
   expected=['taxManagedSMA','qlhOverlay','dtlhOverlay','transition','directIndexing','temSms','alternatives','privateBanking','lending','trustEstate','insurance','charitable'] if d['program']=='IAP' else ['mgiTer','mgiQlh','mgiDtlh']
   assert all(d['verdicts'].get(offering,{}).get('label') for offering in expected)
def test_composition(): assert c.get('/api/composition/henderson?offerings=transition,dtlhOverlay').json()['verdict']=='CONFIRMED_INELIGIBLE'
def test_chat_grounded():
 d=c.post('/api/chat',json={'fa':'dana','message':'Tell me about Henderson'}).json();assert 'Henderson' in d['content'];assert d['mode']=='local-grounded'
def test_unknown_fa(): assert c.get('/api/book?fa=missing').status_code==404
def test_static_app():
 r=c.get('/');assert r.status_code==200;assert 'Atlas' in r.text
