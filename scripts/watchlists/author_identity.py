"""Names and author-owned links; these helpers do not change roster identities."""
import re,unicodedata
from urllib.parse import urljoin,urlsplit
from bs4 import BeautifulSoup

TRANSLITERATION=str.maketrans({'ı':'i','İ':'I','ø':'o','Ø':'O','ł':'l','Ł':'L','đ':'d','Đ':'D','ß':'ss','æ':'ae','Æ':'Ae','œ':'oe','Œ':'Oe'})

def search_alias_names(name):
    """Search hints only; nickname expansion alone does not prove identity."""
    groups=[['alex','alexander'],['ben','benjamin'],['dan','daniel'],['bill','will','william'],
            ['greg','gregory'],['jim','james'],['mike','michael'],['tom','thomas'],
            ['steve','steven','stephen'],['dave','david'],['bob','robert'],['sam','samuel'],['joe','joseph'],
            ['brad','bradley'],['doug','douglas'],['cami','camelia'],['andy','andrew'],['rick','richard'],
            ['ed','edward'],['phil','philip','philippe'],['kate','katherine'],['liz','elizabeth']]
    words=[w for w in re.findall(r'[^\W\d_]+',name)if len(w)>1]
    aliases={name}
    if len(words)>=2:
        for group in groups:
            if words[0].lower()in group:
                aliases.update(re.sub(r'\b'+re.escape(words[0])+r'\b',alias,name,count=1,flags=re.I)for alias in group)
    return aliases

def identity_key(text):
    return re.sub('[^a-z0-9]','',unicodedata.normalize('NFKD',str(text).translate(TRANSLITERATION)).encode('ascii','ignore').decode().lower())

def name_variants(name):
    plain=re.sub(r'\([^)]*\)|\{[^}]*\}','',name).strip()
    tokens=re.findall(r'[^\W\d_]+',plain,flags=re.U)
    words=[t for t in tokens if len(t)>1]
    full_given=bool(words and words[0].lower()not in {'van','von','de','del','da','di','der','den','la','le','du','dos','das'})
    german=plain.translate(str.maketrans({'ä':'ae','ö':'oe','ü':'ue','Ä':'Ae','Ö':'Oe','Ü':'Ue'}))
    forms={identity_key(name),identity_key(plain),identity_key(german)}
    if len(words)>=2 and full_given:forms.add(identity_key(' '.join(words)))
    if len(words)>=3 and full_given:forms.add(identity_key(words[0]+' '+words[-1]))
    if len(words)>=2 and full_given:forms.add(identity_key(words[-1]+' '+words[0]))
    if words:
        for nickname in re.findall(r'\(([^)]+)\)',name)+re.findall(r'[“\"]([^”\"]+)[”\"]',name):
            if re.fullmatch(r'[^\W\d_]+',nickname,flags=re.U):forms.add(identity_key(nickname+' '+words[-1]))
    return forms-{''}

def name_in_text(name,text):
    """Allow omitted/inserted middle initials and surname-first headings."""
    if any(form in identity_key(text)for form in name_variants(name)):return True
    words=[identity_key(t)for t in re.findall(r'[^\W\d_]+',name)if len(t)>1]
    tokens=[identity_key(t)for t in re.findall(r'[^\W\d_]+',text)]
    if len(words)<2 or words[0]in {'van','von','de','del','da','di','der','den','la','le','du','dos','das'}:return False
    first,last=words[0],words[-1]
    for i,token in enumerate(tokens):
        if token==first and last in tokens[i+1:i+5]:return True
        if token==last and first in tokens[i+1:i+4]:return True
    return False

def personal_site_links(body,base_url):
    """Recognize explicit personal links even when the anchor label is a URL."""
    soup=BeautifulSoup(body,'html.parser');links=[]
    label=re.compile(r'\b(?:personal|academic|my|new|research|external)\s+(?:web\s*site|web\s*page|home\s*page)|\bwebsite\s+(?:has\s+)?moved\b|\b(?:website|homepage|webpage|www)\s*:',re.I)
    for a in soup.find_all('a',href=True):
        url=urljoin(base_url,a['href']).split('#')[0]
        p=urlsplit(url)
        if p.scheme not in ('https','http')or not p.hostname:continue
        if re.search(r'linkedin|twitter|facebook|scholar\.google|ssrn|orcid',p.hostname,re.I):continue
        own=a.get_text(' ',strip=True)
        labelled=' '.join([own,a.get('title',''),a.get('aria-label','')])
        parent=a.find_parent(['p','li','td'])
        context=parent.get_text(' ',strip=True) if parent else ''
        generic=bool(re.fullmatch(r'\s*(?:website|webpage|homepage)\s*',own,re.I)and not a.find_parent(['footer','nav']))
        explicit=bool(label.search(labelled)or(len(context)<350 and label.search(context))or generic)
        if explicit and url.rstrip('/')!=base_url.rstrip('/'):
            links.append(url)
    return list(dict.fromkeys(links))


def author_profile_link_evidence(body,base_url,name):
    """Keep a profile button with its own named card, not a neighbouring person."""
    links=[];forms=name_variants(name)
    button=re.compile(r'(?:personal|visit|view|full|read|more|research|academic)?\s*(?:web\s*site|web\s*page|home\s*page|profile|biography|bio|details)|read more',re.I)
    for a in BeautifulSoup(body,'html.parser').find_all('a',href=True):
        url=urljoin(base_url,a['href']).split('#')[0]
        label=' '.join([a.get_text(' ',strip=True),a.get('aria-label',''),' '.join(x.get('alt','')for x in a.find_all('img'))]).strip()
        if urlsplit(url).scheme not in ('http','https')or url.rstrip('/')==base_url.rstrip('/'):continue
        named_label=len(label)<120 and name_in_text(name,label)
        named_url=any(f in identity_key(url)for f in forms)
        context='';named_card=False
        if not named_label and not named_url and len(label)<80 and button.search(label):
            for parent in a.parents:
                if parent.name not in ['article','li','tr','div','section','td']:continue
                text=parent.get_text(' ',strip=True)
                if len(text)>700:break
                heading=' '.join(x.get_text(' ',strip=True)for x in parent.find_all(['h1','h2','h3','h4','h5','h6']))
                heading+=' '+' '.join(x.get('alt','')for x in parent.find_all('img'))
                semantic=parent.name in ['article','li','tr']or bool(re.search(r'(?:^|[-_ ])(?:card|person|profile|member)(?:[-_ ]|$)',' '.join(parent.get('class',[]))))
                if heading.strip()or semantic:
                    named_card=name_in_text(name,heading or text)
                    if named_card:context=text[:600]
                    break
        if named_label or named_url or named_card:
            links.append({'url':url,'label':label,'name_evidence':'named anchor'if named_label else'named URL'if named_url else'named individual card','context':context})
    return list({r['url']:r for r in links}.values())[:8]


def author_profile_links(body,base_url,name):
    """Discovery candidates still need their own identity/evidence check."""
    return [r['url']for r in author_profile_link_evidence(body,base_url,name)]
