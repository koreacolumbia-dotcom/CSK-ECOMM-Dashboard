#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import os, re, json
from pathlib import Path
import numpy as np
import pandas as pd

OUT=Path(os.getenv('OUT_DIR','reports')); OUT.mkdir(parents=True,exist_ok=True)
PROJECT=os.getenv('GCP_PROJECT','columbia-ga4')
DATASET=os.getenv('GA4_DATASET','analytics_358593394')
SERVER=os.getenv('MSSQL_SERVER','211.239.167.185')
DB=os.getenv('MSSQL_DATABASE','columbia_crm')
USER=os.getenv('MSSQL_USER','crmdata')
PWD=os.getenv('MSSQL_PASSWORD','')
TODAY=pd.Timestamp.today().normalize(); END=pd.Timestamp(os.getenv('REPORT_END_DATE',(TODAY-pd.Timedelta(days=1)).strftime('%Y-%m-%d'))); START=pd.Timestamp(os.getenv('REPORT_START_DATE',(END-pd.Timedelta(days=30)).strftime('%Y-%m-%d')))
LY_START=START-pd.DateOffset(years=1); LY_END=END-pd.DateOffset(years=1)

def rx(t,p): return bool(re.search(p,t or '',re.I))
def classify(s,m,c=''):
    sm=f'{s or ""} / {m or ""}'; cp=c or ''
    rules=[
      (r'youtube\s*/\s*live',None,('4. Official SNS','YouTube Referral','유튜브 라이브')),
      (r'lighthouse',None,('3. Organic Traffic','Referral','라이트하우스 팝 디스플레이 존')),
      (r'instagram.*story',None,('4. Official SNS','Instagram Story','인스타그램 스토리')),
      (r'instagram.*feed',None,('4. Official SNS','Instagram Feed','인스타그램 피드')),
      (r'benz',None,('3. Organic Traffic','Referral','벤츠 러닝 프로그램')),
      (r'nap.*da',None,('2. Paid Ad','Rewarded Ads','버즈빌 회원가입 광고')),
      (r'toss',None,('2. Paid Ad','Paid Display','토스 배너 광고')),
      (r'blind',None,('2. Paid Ad','Paid Display','블라인드 배너 광고')),
      (r'kakaobs',None,('2. Paid Ad','Paid Search','카카오 브랜드검색광고')),
      (r'inhouse',None,('3. Organic Traffic','Inhouse Purchase','Inhouse Purchase')),
      (r'lms',r'lms',('5. Owned Channel','LMS','문자메시지유입')),
      (r'email|edm',None,('5. Owned Channel','Email','이메일유입')),
      (r'kakao_fridnstalk',None,('5. Owned Channel','Kakao Friendstalk','카카오톡친구톡')),
      (r'igshopping',None,('4. Official SNS','Instagram Offical Shop','인스타그램 샵')),
      (r'facebook.*referral',None,('3. Organic Traffic','Social','페이스북자연유입')),
      (r'instagram.*referral',None,('4. Official SNS','Instagram Offical Account','인스타그램 공식계정')),
      (r'meta|facebook|instagram|\big\b|\bfb\b',None,('2. Paid Ad','Paid Social','메타광고')),
      (r'google',r'디멘드젠|디멘드잰|디맨드젠|디맨드잰|dg|demand|demend',('2. Paid Ad','Paid Display','구글디멘드젠광고')),
      (r'google',r'gdn',('2. Paid Ad','Paid Display','구글GDN광고')),
      (r'google\s*/\s*cpc',r'pmax',('2. Paid Ad','Paid Omni Channel','구글피맥스광고')),
      (r'google\s*/\s*cpc',r'유튜브|yt|youtube|instream|vac|vvc',('1. Awareness','Paid Video','구글동영상광고')),
      (r'google\s*/\s*cpc',r'discovery',('1. Awareness','Paid Display','구글디스커버리광고')),
      (r'google\s*/\s*cpc',r'sa|ss|검색',('2. Paid Ad','Paid Search','구글검색광고')),
      (r'google\s*/\s*cpc',None,('2. Paid Ad','Paid Ad','구글기타광고')),
      (r'google\s*/\s*organic',None,('3. Organic Traffic','Organic Search','구글자연검색')),
      (r'google',None,('3. Organic Traffic','Referral','구글기타유입')),
      (r'youtube',None,('3. Organic Traffic','YouTube','유튜브자연유입')),
      (r'naver.*da|gfa',None,('2. Paid Ad','Paid Display','네이버배너광고')),
      (r'naverbs',None,('2. Paid Ad','Paid Search','네이버브랜드검색광고')),
      (r'naver.*shopping_ad',None,('2. Paid Ad','Paid Search','네이버쇼핑검색광고')),
      (r'naver.*cpc',None,('2. Paid Ad','Paid Search','네이버파워링크광고')),
      (r'naver.*shopping',None,('3. Organic Traffic','Organic Search','네이버쇼핑자연검색')),
      (r'naver.*organic',None,('3. Organic Traffic','Organic Search','네이버사이트자연검색')),
      (r'naver',None,('3. Organic Traffic','Referral','네이버기타유입')),
      (r'daum\s*/\s*organic',None,('3. Organic Traffic','Organic Search','다음자연검색')),
      (r'daum.*referral',None,('3. Organic Traffic','Referral','다음기타유입')),
      (r'kakao_ch',r'kakao_ch',('5. Owned Channel','Kakao Channel','카카오톡채널메시지')),
      (r'kakao_alimtalk',None,('5. Owned Channel','Kakao Alimtalk','카카오톡알림톡')),
      (r'kakao_coupon',None,('5. Owned Channel','Kakao Coupon','카카오톡쿠폰')),
      (r'kakao_chatbot',None,('5. Owned Channel','Kakao Chatbot','카카오톡챗봇')),
      (r'kakao',None,('2. Paid Ad','Paid Display','카카오광고')),
      (r'\(direct\)\s*/\s*\(none\)',None,('3. Organic Traffic','Direct','직접유입')),
      (r'signalplay|signal play|signal_play|sg_|signal|manplus',None,('2. Paid Ad','Paid Display','시그널플레이광고')),
      (r'buzzvill',None,('2. Paid Ad','Paid Display','버즈빌광고')),
      (r'criteo',None,('2. Paid Ad','Paid Display','크리테오광고')),
      (r'mobon',None,('2. Paid Ad','Paid Display','모비온광고')),
      (r'cpc',None,('2. Paid Ad','Paid Search','기타검색광고')),
      (r'organic',None,('3. Organic Traffic','Organic Search','기타자연검색')),
      (r'referral',None,('3. Organic Traffic','Referral','기타추천유입'))]
    for smp,cpp,out in rules:
        if rx(sm,smp) and (cpp is None or rx(cp,cpp)): return out
    if rx(sm,r'mkt|_bd') or rx(cp,r'mkt|\[bd'): return ('1. Awareness','Awareness','Awareness')
    return ('6. etc','미분류','미분류')

def ga4_query(a,b):
    a=a.strftime('%Y%m%d'); b=b.strftime('%Y%m%d')
    return f'''WITH base AS (SELECT PARSE_DATE('%Y%m%d',event_date) event_date,TIMESTAMP_MICROS(event_timestamp) event_ts,user_pseudo_id,event_name,(SELECT value.int_value FROM UNNEST(event_params) WHERE key='ga_session_id') ga_session_id,COALESCE(session_traffic_source_last_click.manual_campaign.source,collected_traffic_source.manual_source,traffic_source.source,'(direct)') source,COALESCE(session_traffic_source_last_click.manual_campaign.medium,collected_traffic_source.manual_medium,traffic_source.medium,'(none)') medium,COALESCE(session_traffic_source_last_click.manual_campaign.campaign_name,collected_traffic_source.manual_campaign_name,'(not set)') campaign,ecommerce.transaction_id transaction_id,COALESCE(ecommerce.purchase_revenue,0) revenue FROM `{PROJECT}.{DATASET}.events_*` WHERE _TABLE_SUFFIX BETWEEN '{a}' AND '{b}'), s AS (SELECT event_date,CONCAT(user_pseudo_id,'-',CAST(ga_session_id AS STRING)) session_key,ARRAY_AGG(source IGNORE NULLS ORDER BY event_ts LIMIT 1)[SAFE_OFFSET(0)] source,ARRAY_AGG(medium IGNORE NULLS ORDER BY event_ts LIMIT 1)[SAFE_OFFSET(0)] medium,ARRAY_AGG(campaign IGNORE NULLS ORDER BY event_ts LIMIT 1)[SAFE_OFFSET(0)] campaign,COUNT(DISTINCT IF(event_name='purchase',transaction_id,NULL)) conversions,SUM(IF(event_name='purchase',revenue,0)) revenue FROM base WHERE ga_session_id IS NOT NULL GROUP BY 1,2) SELECT event_date,source,medium,campaign,COUNT(DISTINCT session_key) sessions,SUM(conversions) conversions,SUM(revenue) revenue FROM s GROUP BY 1,2,3,4'''

def load_bq(a,b):
    from google.cloud import bigquery
    d=bigquery.Client(project=PROJECT).query(ga4_query(a,b)).to_dataframe(); d['event_date']=pd.to_datetime(d['event_date'])
    cls=[classify(s,m,c) for s,m,c in zip(d.source,d.medium,d.campaign)]; d[['channel_major','channel_middle','channel_minor']]=pd.DataFrame(cls,index=d.index); return d

def product_query(a,b):
    a=a.strftime('%Y-%m-%d'); b=(b+pd.Timedelta(days=1)).strftime('%Y-%m-%d')
    return f'''SELECT CAST(o.OrderRegdate AS date) order_date,CAST(op.ProductCode AS varchar(100)) product_code,COALESCE(NULLIF(LTRIM(RTRIM(p.ProductName)),''),op.ProductCode) product_name,SUM(CAST(ISNULL(op.ProductQuantity,0) AS float)) qty,SUM(CAST(ISNULL(op.OrderProductPrice,0) AS float)) revenue,CASE WHEN SUM(CAST(ISNULL(op.ProductPrice,0) AS float)*CAST(ISNULL(op.ProductQuantity,0) AS float))>0 THEN 1-SUM(CAST(ISNULL(op.OrderProductPrice,0) AS float))/NULLIF(SUM(CAST(ISNULL(op.ProductPrice,0) AS float)*CAST(ISNULL(op.ProductQuantity,0) AS float)),0) END discount_rate,COUNT(DISTINCT o.OrderNo) orders FROM dbo.TB_Order o JOIN dbo.TB_OrderProduct op ON o.OrderNo=op.OrderNo LEFT JOIN dbo.TB_Product p ON op.ProductNo=p.ProductNo WHERE o.OrderRegdate>='{a}' AND o.OrderRegdate<'{b}' AND ISNULL(op.ProductQuantity,0)>0 AND ISNULL(op.OrderRefundStatus,0)=0 GROUP BY CAST(o.OrderRegdate AS date),CAST(op.ProductCode AS varchar(100)),COALESCE(NULLIF(LTRIM(RTRIM(p.ProductName)),''),op.ProductCode)'''

def load_sql(a,b):
    import pyodbc
    cs=f'DRIVER={{ODBC Driver 17 for SQL Server}};SERVER={SERVER};DATABASE={DB};UID={USER};PWD={PWD};TrustServerCertificate=yes;'
    with pyodbc.connect(cs,timeout=30) as cn: d=pd.read_sql(product_query(a,b),cn)
    d['order_date']=pd.to_datetime(d['order_date']); return d

def yoy_date(d,col,ly=False):
    x=d.copy(); x['compare_date']=pd.to_datetime(x[col])+(pd.DateOffset(years=1) if ly else pd.DateOffset()); return x

def channel_yoy(c,l):
    keys=['compare_date','channel_major','channel_middle','channel_minor']
    C=yoy_date(c,'event_date').groupby(keys,dropna=False).agg(sessions_ty=('sessions','sum'),conversions_ty=('conversions','sum'),revenue_ty=('revenue','sum')).reset_index()
    L=yoy_date(l,'event_date',True).groupby(keys,dropna=False).agg(sessions_ly=('sessions','sum'),conversions_ly=('conversions','sum'),revenue_ly=('revenue','sum')).reset_index()
    x=C.merge(L,on=keys,how='outer').fillna(0); x['channel']=x.channel_minor; x['cvr_ty']=np.where(x.sessions_ty>0,x.conversions_ty/x.sessions_ty,0); x['cvr_ly']=np.where(x.sessions_ly>0,x.conversions_ly/x.sessions_ly,0)
    for m in ['sessions','conversions','revenue']: x[m+'_yoy']=np.where(x[m+'_ly']!=0,x[m+'_ty']/x[m+'_ly']-1,np.nan)
    x['cvr_yoy_pp']=(x.cvr_ty-x.cvr_ly)*100; return x

def pkey(d):
    n=d.product_name.fillna('').astype(str).str.lower().str.replace(r'\s+',' ',regex=True).str.replace(r'[^0-9a-z가-힣 ]+','',regex=True).str.strip(); return np.where(n!='','NAME:'+n,'CODE:'+d.product_code.fillna('').astype(str))
def product_yoy(c,l):
    C=yoy_date(c,'order_date'); L=yoy_date(l,'order_date',True); C['key']=pkey(C); L['key']=pkey(L); k=['compare_date','key']
    ca=C.groupby(k).agg(product_code=('product_code','first'),product_name=('product_name','first'),revenue_ty=('revenue','sum'),qty_ty=('qty','sum'),orders_ty=('orders','sum'),discount_ty=('discount_rate','mean')).reset_index(); la=L.groupby(k).agg(product_code_ly=('product_code','first'),product_name_ly=('product_name','first'),revenue_ly=('revenue','sum'),qty_ly=('qty','sum'),orders_ly=('orders','sum'),discount_ly=('discount_rate','mean')).reset_index(); x=ca.merge(la,on=k,how='outer'); x['product_name']=x.product_name.fillna(x.product_name_ly); x['product_code']=x.product_code.fillna(x.product_code_ly)
    for z in ['revenue_ty','revenue_ly','qty_ty','qty_ly','orders_ty','orders_ly']: x[z]=pd.to_numeric(x[z],errors='coerce').fillna(0)
    x['revenue_yoy']=np.where(x.revenue_ly!=0,x.revenue_ty/x.revenue_ly-1,np.nan); x['qty_yoy']=np.where(x.qty_ly!=0,x.qty_ty/x.qty_ly-1,np.nan); x['discount_delta_pp']=(x.discount_ty-x.discount_ly)*100; return x

def spikes(d):
    x=d.groupby(['order_date','product_code','product_name'],dropna=False).agg(revenue=('revenue','sum'),qty=('qty','sum'),discount_rate=('discount_rate','mean')).reset_index().sort_values(['product_code','order_date']); x['revenue_7d_avg']=x.groupby('product_code').revenue.transform(lambda s:s.shift(1).rolling(7,min_periods=3).mean()); x['spike_vs_7d']=np.where(x.revenue_7d_avg>0,x.revenue/x.revenue_7d_avg-1,np.nan); x['is_spike']=(x.spike_vs_7d>=1)&(x.revenue>=1000000); return x.sort_values(['is_spike','spike_vs_7d'],ascending=[False,False])

def summary(c,p):
    s={};
    for m in ['sessions','revenue','conversions']:
        s[m+'_ty']=float(c[m+'_ty'].sum()); s[m+'_ly']=float(c[m+'_ly'].sum()); s[m+'_yoy']=s[m+'_ty']/s[m+'_ly']-1 if s[m+'_ly'] else None
    s['cvr_ty']=s['conversions_ty']/s['sessions_ty'] if s['sessions_ty'] else 0; s['cvr_ly']=s['conversions_ly']/s['sessions_ly'] if s['sessions_ly'] else 0; s['cvr_yoy_pp']=(s['cvr_ty']-s['cvr_ly'])*100; return s

def records(d,cols=None,n=None):
    x=d.copy(); x=x[cols] if cols else x; x=x.head(n) if n else x; x=x.replace({np.nan:None}); return json.loads(x.to_json(orient='records',date_format='iso'))
def build_html(s,c,p,sp):
    rank=c.groupby('channel',dropna=False).agg(revenue_ty=('revenue_ty','sum'),revenue_ly=('revenue_ly','sum'),sessions_ty=('sessions_ty','sum'),sessions_ly=('sessions_ly','sum'),conversions_ty=('conversions_ty','sum')).reset_index(); rank['revenue_yoy']=np.where(rank.revenue_ly>0,rank.revenue_ty/rank.revenue_ly-1,np.nan); rank['cvr_ty']=np.where(rank.sessions_ty>0,rank.conversions_ty/rank.sessions_ty,0); rank=rank.sort_values('revenue_ty',ascending=False)
    movers=p.groupby(['product_code','product_name'],dropna=False).agg(revenue_ty=('revenue_ty','sum'),revenue_ly=('revenue_ly','sum'),discount_ty=('discount_ty','mean'),discount_ly=('discount_ly','mean')).reset_index(); movers['revenue_yoy']=np.where(movers.revenue_ly>0,movers.revenue_ty/movers.revenue_ly-1,np.nan); movers['discount_delta_pp']=(movers.discount_ty-movers.discount_ly)*100; movers=movers.sort_values('revenue_yoy',ascending=False)
    D=json.dumps({'summary':s,'channelDaily':records(c),'channelRank':records(rank),'productDaily':records(p),'productMovers':records(movers, n=150),'spikes':records(sp[sp.is_spike],n=150)},ensure_ascii=False)
    html=f'''<!doctype html><html lang="ko"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>Performance Dashboard</title><script src="https://cdn.jsdelivr.net/npm/chart.js"></script><style>:root{{--b:#07090c;--p:#0f1319;--l:#222a34;--t:#f7f9fc;--m:#8f9bab;--a:#0094D3;--g:#50d890;--r:#ff7373}}*{{box-sizing:border-box}}body{{margin:0;background:radial-gradient(circle at 85% 0,rgba(0,148,211,.17),transparent 30%),var(--b);color:var(--t);font-family:Inter,Arial,'Noto Sans KR',sans-serif}}.shell{{max-width:1880px;margin:auto;padding:28px}}h1{{font-size:34px;margin:0}}.sub{{color:var(--m);font-size:12px;margin-top:8px}}.kpis{{display:grid;grid-template-columns:repeat(4,1fr);gap:14px;margin-top:22px}}.k{{background:var(--p);border:1px solid var(--l);border-radius:18px;padding:20px}}.lab{{font-size:11px;color:var(--m);font-weight:800}}.val{{font-size:30px;font-weight:900;margin-top:10px}}.grid{{display:grid;grid-template-columns:2fr 1fr;gap:14px;margin-top:14px}}.card{{background:var(--p);border:1px solid var(--l);border-radius:18px;padding:16px}}.chart{{height:380px}}table{{width:100%;border-collapse:collapse;font-size:12px}}th,td{{padding:10px;border-bottom:1px solid var(--l);text-align:right}}th:first-child,td:first-child{{text-align:left}}th{{color:var(--m)}}.pos{{color:var(--g)}}.neg{{color:var(--r)}}@media(max-width:1000px){{.kpis{{grid-template-columns:repeat(2,1fr)}}.grid{{grid-template-columns:1fr}}}}</style></head><body><div class="shell"><div class="lab">COLUMBIA SPORTSWEAR KOREA</div><h1>ECOMM Performance Dashboard</h1><div class="sub">{START.date()} – {END.date()} · BigQuery + MSSQL · YoY</div><div class="kpis"><div class="k"><div class="lab">SESSIONS</div><div class="val">{s['sessions_ty']:,.0f}</div><div class="sub">YoY {((s['sessions_yoy'] or 0)*100):+.1f}%</div></div><div class="k"><div class="lab">GA4 REVENUE</div><div class="val">₩{s['revenue_ty']:,.0f}</div><div class="sub">YoY {((s['revenue_yoy'] or 0)*100):+.1f}%</div></div><div class="k"><div class="lab">CONVERSIONS</div><div class="val">{s['conversions_ty']:,.0f}</div><div class="sub">YoY {((s['conversions_yoy'] or 0)*100):+.1f}%</div></div><div class="k"><div class="lab">CVR</div><div class="val">{s['cvr_ty']*100:.2f}%</div><div class="sub">YoY Δ {s['cvr_yoy_pp']:+.2f}%p</div></div></div><div class="grid"><div class="card"><div class="lab">DAILY REVENUE · TY vs LY</div><div class="chart"><canvas id="rev"></canvas></div></div><div class="card"><div class="lab">TOP CHANNELS</div><table id="ct"></table></div></div><div class="grid"><div class="card"><div class="lab">PRODUCT MOVERS</div><table id="pt"></table></div><div class="card"><div class="lab">SPIKE FINDER</div><table id="st"></table></div></div></div><script>const D={D};const won=v=>'₩'+Math.round(v||0).toLocaleString(),pct=v=>v==null?'-':(v*100).toFixed(1)+'%';const m={{}};D.channelDaily.forEach(r=>{{const d=String(r.compare_date).slice(0,10);if(!m[d])m[d]=[0,0];m[d][0]+=+r.revenue_ty||0;m[d][1]+=+r.revenue_ly||0}});const a=Object.entries(m).sort();new Chart(rev,{{type:'line',data:{{labels:a.map(x=>x[0].slice(5)),datasets:[{{label:'TY',data:a.map(x=>x[1][0]),borderColor:'#0094D3',pointRadius:0,tension:.25}},{{label:'LY',data:a.map(x=>x[1][1]),borderColor:'#7b8794',borderDash:[5,5],pointRadius:0,tension:.25}}]}},options:{{maintainAspectRatio:false,plugins:{{legend:{{labels:{{color:'#9aa6b2'}}}}}},scales:{{x:{{ticks:{{color:'#8f9bab'}},grid:{{display:false}}}},y:{{ticks:{{color:'#8f9bab',callback:v=>'₩'+Number(v).toLocaleString()}},grid:{{color:'rgba(255,255,255,.06)'}}}}}}}}}});ct.innerHTML='<tr><th>Channel</th><th>Revenue</th><th>YoY</th></tr>'+D.channelRank.slice(0,10).map(r=>`<tr><td>${{r.channel}}</td><td>${{won(r.revenue_ty)}}</td><td class="${{(r.revenue_yoy||0)>=0?'pos':'neg'}}">${{pct(r.revenue_yoy)}}</td></tr>`).join('');pt.innerHTML='<tr><th>Product</th><th>Revenue</th><th>YoY</th></tr>'+D.productMovers.filter(r=>r.revenue_ly>0).slice(0,12).map(r=>`<tr><td>${{r.product_name}}</td><td>${{won(r.revenue_ty)}}</td><td class="${{(r.revenue_yoy||0)>=0?'pos':'neg'}}">${{pct(r.revenue_yoy)}}</td></tr>`).join('');st.innerHTML='<tr><th>Product</th><th>Revenue</th><th>Spike</th></tr>'+D.spikes.slice(0,12).map(r=>`<tr><td>${{r.product_name}}</td><td>${{won(r.revenue)}}</td><td>${{pct(r.spike_vs_7d)}}</td></tr>`).join('');</script></body></html>'''
    (OUT/'performance_dashboard.html').write_text(html,encoding='utf-8')

def export_xlsx(s,c,p,sp):
    with pd.ExcelWriter(OUT/'performance_export.xlsx',engine='openpyxl') as w:
        pd.DataFrame([s]).to_excel(w,'Summary',index=False); c.to_excel(w,'Channel YoY',index=False); p.to_excel(w,'Product YoY',index=False); sp.to_excel(w,'Spikes',index=False)

def main():
    if not PWD: raise RuntimeError('MSSQL_PASSWORD is required')
    cy=load_bq(START,END); ly=load_bq(LY_START,LY_END); cp=load_sql(START,END); lp=load_sql(LY_START,LY_END); c=channel_yoy(cy,ly); p=product_yoy(cp,lp); sp=spikes(cp); s=summary(c,p); export_xlsx(s,c,p,sp); build_html(s,c,p,sp); print('Built performance_dashboard.html / performance_export.xlsx')
if __name__=='__main__': main()
