from pathlib import Path
import os
from datetime import datetime,timezone
import httpx
from typing import Literal
from fastapi import FastAPI,HTTPException,Query
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel,Field
from .data import RULE_STORE,FA_PROFILES,BY_ID,my_book
from .services import *
from .agent import run_agent

app=FastAPI(title='Atlas Advisor Console',version='1.0.0')
STATIC=Path(__file__).parent/'static'
app.mount('/static',StaticFiles(directory=STATIC),name='static')

def valid_fa(fa):
    if fa not in FA_PROFILES: raise HTTPException(404,'Advisor not found')
    return fa
@app.get('/')
def index(): return FileResponse(STATIC/'index.html')
@app.get('/api/health')
def health(): return {'status':'ok','pack_id':RULE_STORE['pack_id'],'offerings':len(RULE_STORE['offerings']),'rules':sum(len(o['rules']) for o in RULE_STORE['offerings'].values())}
@app.get('/api/meta')
def meta(): return {'advisors':FA_PROFILES,'offerings':{k:v['label'] for k,v in RULE_STORE['offerings'].items()},'pack_id':RULE_STORE['pack_id'],'policy_status':RULE_STORE['status']}
@app.get('/api/book')
def book(fa:str='dana'): return my_book(valid_fa(fa))
@app.get('/api/household/{household_id}')
def household(household_id:str):
    try:
        record=household_or_404(household_id)
        return {**record,'program':record.get('program','IAP'),'verdicts':all_verdicts(household_id)}
    except KeyError:raise HTTPException(404,'Household not found')
@app.get('/api/verdict/{household_id}/{offering_id}')
def verdict(household_id:str,offering_id:str):
    try:return offering_result(household_id,offering_id)
    except KeyError as e:raise HTTPException(404,str(e))
@app.get('/api/composition/{household_id}')
def composition(household_id:str,offerings:str=Query(...)):
    try:return composition_result(household_id,[x for x in offerings.split(',') if x])
    except KeyError as e:raise HTTPException(404,str(e))
@app.get('/api/nba/{kind}')
def nba_endpoint(kind:Literal['meetings','drift','cio','deep'],fa:str='dana'): return nba(kind,valid_fa(fa))
@app.get('/api/tax-desk')
def tax_endpoint(fa:str='dana'): return tax_desk(valid_fa(fa))
@app.get('/api/cross-sell')
def cross_endpoint(fa:str='dana'): return cross_sell(valid_fa(fa))
class ChatRequest(BaseModel):
    fa:str='dana';message:str=Field(min_length=1,max_length=4000);history:list[dict]=[]
async def _live_chat(req: ChatRequest):
    provider=os.getenv('ATLAS_LLM_PROVIDER','').lower()
    fa=FA_PROFILES[req.fa]
    persona=f"You are Atlas, an advisor-facing book copilot for {fa['name']}. Use only the supplied book context. Never invent clients, holdings, figures, eligibility or policy. Distinguish eligible, ineligible and needs-review outcomes."
    context=book_context(req.fa)
    timeout=float(os.getenv('ATLAS_LLM_TIMEOUT','12'))
    async with httpx.AsyncClient(timeout=timeout) as client:
        if provider=='anthropic' and os.getenv('ANTHROPIC_API_KEY'):
            r=await client.post('https://api.anthropic.com/v1/messages',headers={'x-api-key':os.environ['ANTHROPIC_API_KEY'],'anthropic-version':'2023-06-01','content-type':'application/json'},json={'model':os.getenv('ATLAS_ANTHROPIC_MODEL','claude-sonnet-4-6'),'max_tokens':700,'system':persona+'\n\nBOOK DATA:\n'+context,'messages':[{'role':'user','content':req.message}]});r.raise_for_status();return r.json()['content'][0]['text'],'anthropic'
        if provider=='openai' and os.getenv('OPENAI_API_KEY'):
            r=await client.post('https://api.openai.com/v1/responses',headers={'Authorization':'Bearer '+os.environ['OPENAI_API_KEY'],'content-type':'application/json'},json={'model':os.getenv('ATLAS_OPENAI_MODEL','gpt-5.4-mini'),'instructions':persona,'input':'BOOK DATA:\n'+context+'\n\nQUESTION:\n'+req.message});r.raise_for_status();d=r.json();return d.get('output_text') or ''.join(x.get('text','') for o in d.get('output',[]) for x in o.get('content',[])),'openai'
    return None,None

@app.post('/api/chat')
async def chat(req:ChatRequest):
    valid_fa(req.fa)
    try:
        content,mode=await _live_chat(req)
        if content:return {'content':content,'mode':mode,'context_households':len(my_book(req.fa))}
    except Exception:
        pass
    return {'content':local_answer(req.fa,req.message),'mode':'local-grounded','context_households':len(my_book(req.fa))}

class DraftRequest(BaseModel):
    fa:str='dana';kind:Literal['meeting_prep']='meeting_prep'
class DraftDecisionRequest(BaseModel):
    kind:Literal['meeting_prep']='meeting_prep'
    action:Literal['approve','decline','edit']
    edited_content:str|None=None
    decided_by:str='dana'

async def _live_draft(household_id:str,kind:str,fa:str)->str|None:
    if kind!='meeting_prep':return None
    provider=os.getenv('ATLAS_LLM_PROVIDER','').lower()
    fa_p=FA_PROFILES[fa]
    persona=(f"You are Atlas, drafting a meeting-prep brief for {fa_p['name']} ahead of a specific client meeting. "
        f"Use ONLY the household data supplied below. Never invent facts, holdings, figures, or eligibility. "
        f"Write in markdown with exactly these section headers, in this order: "
        f"'### What prompted this meeting', '### Portfolio snapshot', '### Concentration & risk', "
        f"'### CIO alignment', '### Suggested talking points' (3 to 5 numbered points), '### Eligible next steps'. "
        f"Start with a single '## Meeting prep — <household name>' title line. Be specific, cite real numbers, keep it concise.")
    context=household_draft_context(household_id)
    timeout=float(os.getenv('ATLAS_LLM_TIMEOUT','12'))
    async with httpx.AsyncClient(timeout=timeout) as client:
        if provider=='anthropic' and os.getenv('ANTHROPIC_API_KEY'):
            r=await client.post('https://api.anthropic.com/v1/messages',headers={'x-api-key':os.environ['ANTHROPIC_API_KEY'],'anthropic-version':'2023-06-01','content-type':'application/json'},json={'model':os.getenv('ATLAS_ANTHROPIC_MODEL','claude-sonnet-4-6'),'max_tokens':900,'system':persona,'messages':[{'role':'user','content':context}]});r.raise_for_status();return r.json()['content'][0]['text']
        if provider=='openai' and os.getenv('OPENAI_API_KEY'):
            r=await client.post('https://api.openai.com/v1/responses',headers={'Authorization':'Bearer '+os.environ['OPENAI_API_KEY'],'content-type':'application/json'},json={'model':os.getenv('ATLAS_OPENAI_MODEL','gpt-5.4-mini'),'instructions':persona,'input':context});r.raise_for_status();d=r.json();return d.get('output_text') or ''.join(x.get('text','') for o in d.get('output',[]) for x in o.get('content',[]))
    return None

@app.post('/api/draft/{household_id}')
async def create_draft(household_id:str,req:DraftRequest):
    try:household_or_404(household_id)
    except KeyError:raise HTTPException(404,'Household not found')
    valid_fa(req.fa)
    content=None
    try:content=await _live_draft(household_id,req.kind,req.fa)
    except Exception:content=None
    mode='model-drafted' if content else 'local-grounded'
    if not content:content=generate_draft_local(household_id,req.kind)
    record={'household_id':household_id,'kind':req.kind,'content':content,'status':'pending','mode':mode,
        'created_at':datetime.now(timezone.utc).isoformat(),'decided_at':None,'decided_by':None}
    DRAFT_STORE[draft_key(household_id,req.kind)]=record
    return record

@app.get('/api/draft/{household_id}')
def get_draft(household_id:str,kind:str='meeting_prep'):
    key=draft_key(household_id,kind)
    if key not in DRAFT_STORE:raise HTTPException(404,'No draft yet for this household/kind')
    return DRAFT_STORE[key]

@app.post('/api/draft/{household_id}/decision')
def decide_draft(household_id:str,req:DraftDecisionRequest):
    key=draft_key(household_id,req.kind)
    if key not in DRAFT_STORE:raise HTTPException(404,'No draft yet for this household/kind')
    rec=DRAFT_STORE[key]
    if req.action=='approve':rec['status']='approved'
    elif req.action=='decline':rec['status']='declined'
    elif req.action=='edit':
        if not req.edited_content:raise HTTPException(422,'edited_content required for edit action')
        rec['content']=req.edited_content;rec['status']='edited_approved'
    rec['decided_at']=datetime.now(timezone.utc).isoformat();rec['decided_by']=req.decided_by
    return rec

@app.get('/api/transition/{household_id}')
def transition(household_id:str,offering:str=Query(...)):
    try: return transition_scenario(household_id,offering)
    except KeyError as ke: raise HTTPException(404,str(ke))

@app.get('/api/compare/{household_id}')
def compare(household_id:str,model:str|None=Query(None),amount:float|None=Query(None),products:str|None=Query(None)):
    pids=[p for p in (products or '').split(',') if p]
    try: return build_vehicle_brief(household_id,model,amount,pids or None)
    except KeyError as ke: raise HTTPException(404,str(ke).strip("'"))

@app.get('/api/products/search')
def products_search(q:str=Query(''),vehicle:str|None=Query(None),sleeve:str|None=Query(None),
                    max_minimum:float|None=Query(None),max_fee_bps:float|None=Query(None),
                    tlh_capable:bool|None=Query(None),limit:int=Query(10,ge=1,le=2000)):
    allrows=search_products(q,vehicle=vehicle or None,limit=100000,sleeve=sleeve or None,max_minimum=max_minimum,
                         max_fee_bps=max_fee_bps,tlh_capable=tlh_capable)
    return {'query':q,'results':allrows[:limit],'total':len(allrows)}

@app.get('/api/products/sleeves')
def products_sleeves(): return {'sleeves':shelf_sleeves()}

class AgentRequest(BaseModel):
    fa:str='dana'; message:str=Field(min_length=1,max_length=4000); history:list[dict]=[]; context:dict|None=None

@app.post('/api/agent')
async def agent_endpoint(req:AgentRequest):
    valid_fa(req.fa)
    try: return await run_agent(req.fa,req.message,req.history,req.context)
    except LookupError as e: raise HTTPException(404,str(e))

@app.get('/api/content/search')
def content_search_endpoint(q:str=Query(...),model:str|None=Query(None),topics:str|None=Query(None)):
    topic_list = topics.split(',') if topics else None
    return {'query':q,'results':content_search(q,model_id=model,topics=topic_list)}
