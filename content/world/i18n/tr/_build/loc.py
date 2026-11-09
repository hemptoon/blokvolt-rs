import re
BACK='aıou'; FRONT='eiöü'; VOW=BACK+FRONT+'AIOUEİÖÜâîû'
HARD=set('fstkçşhp')
TRMAP=str.maketrans({'ç':'c','ğ':'g','ı':'i','ö':'o','ş':'s','ü':'u','â':'a','î':'i','û':'u','İ':'i','Ç':'c','Ğ':'g','Ö':'o','Ş':'s','Ü':'u'})
def lower_tr(s): return s.replace('I','ı').replace('İ','i').lower()
POSS=re.compile(r'(leri|ları|ası|esi|isi|ısı|usu|üsü|yeti|ği|ğı|liği|lığı|si|sı|su|sü|ları|leri|i|ı|u|ü)$')
def loc(name, poss=None):
    w=lower_tr(name.split()[-1].split('-')[-1])
    vs=[c for c in w if c in 'aıoueiöüâîû']
    if not vs: return None
    v=vs[-1]; back = v in 'aıouâû'
    multi = (' ' in name.strip())
    if poss is None: poss = multi and w[-1] in 'iıuü'
    if poss:
        return f"{name}'n{'da' if back else 'de'}"
    last=w[-1]
    cons = 't' if last in HARD else 'd'
    return f"{name}'{cons}{'a' if back else 'e'}"
def slug(s):
    s=s.translate(TRMAP).lower()
    import unicodedata
    s=unicodedata.normalize('NFKD',s).encode('ascii','ignore').decode()
    return re.sub(r'[^a-z0-9]+','-',s).strip('-')

VN=str.maketrans({'á':'a','à':'a','â':'a','ã':'a','å':'o','é':'e','è':'e','ê':'e','ë':'e','í':'i','ì':'i','î':'i','ï':'i',
  'ó':'o','ò':'o','ô':'o','õ':'o','ő':'ö','ú':'u','ù':'u','û':'u','ů':'u','ű':'ü','ý':'i','ø':'ö','æ':'e'})
def loc_x(n, cc):
    w=lower_tr(n)
    if cc in ('DE','AT'):
        w=w.replace('ie','i').replace('ei','a').replace('ey','a').replace('ai','a').replace('eu','o').replace('äu','o').replace('ä','e')
    if cc=='FI': w=w.replace('ä','e').replace('y','ü')
    w2=w.translate(VN)
    vset='aıoueiöü' if cc in ('HU','DE','AT') else 'aıoueiöüy'
    if cc not in ('FI','HU','DE','AT'): w2=w2.replace('ä','e')
    vs=[c for c in w2 if c in vset]
    if not vs: return None
    v=vs[-1]; back = v in 'aıouy' and v!='y' or (v=='y' and False)
    back = v in 'aıou'
    last=w2[-1]
    hard=set('fstkçşhpčšćś')
    if cc in ('CZ','SK','HU','HR','SI','BA','RS','ME','PL'): hard|=set('c')
    if cc=='HU' and w2.endswith(('sz','cs')): last='s'
    if cc=='HU' and w2.endswith('s') and not w2.endswith('zs'): last='ş'
    cons='t' if last in hard else 'd'
    return f"{n}'{cons}{'a' if back else 'e'}"
