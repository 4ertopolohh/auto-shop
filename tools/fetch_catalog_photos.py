"""Download selected catalog photographs; retain exact source and content hashes."""
import concurrent.futures, hashlib, io, json
from pathlib import Path
import httpx
from PIL import Image, ImageOps, ImageDraw
ROOT=Path(__file__).resolve().parents[1]
SOURCES=ROOT/'assets/product-photos/sources.json'
OUT=ROOT/'backend/media/catalog-photos';OUT.mkdir(parents=True,exist_ok=True)
def fetch(row):
    options=[row['selected']]  # Keep the visually reviewed source; never silently change SKU.
    failures=[]
    for candidate in options:
        if any(word in candidate['title'].lower() for word in ('diagram','drawing','схема')):continue
        try:
            response=httpx.get(candidate['url'],timeout=25,follow_redirects=True,headers={'User-Agent':'Mozilla/5.0'})
            response.raise_for_status();image=Image.open(io.BytesIO(response.content))
            if min(image.size)<180:raise ValueError('insufficient resolution')
            if image.mode in ('RGBA','LA') or 'transparency' in image.info:
                original=image.convert('RGBA');white=Image.new('RGBA',original.size,'white');white.alpha_composite(original);image=white.convert('RGB')
            else:image=image.convert('RGB')
            image=ImageOps.exif_transpose(image);image.thumbnail((1500,1500))
            path=OUT/(row['slug']+'.webp');image.save(path,'WEBP',quality=93,method=6)
            return {**row,'selected':candidate,'file':str(path.relative_to(ROOT)).replace('\\','/'),'width':image.width,'height':image.height,'sha256':hashlib.sha256(path.read_bytes()).hexdigest()}
        except Exception as error:failures.append(str(error)[:90])
    return {**row,'error':failures}
rows=json.loads(SOURCES.read_text(encoding='utf-8'))
with concurrent.futures.ThreadPoolExecutor(max_workers=3) as pool:results=list(pool.map(fetch,rows))
SOURCES.write_text(json.dumps(results,ensure_ascii=False,indent=2),encoding='utf-8')
sheet=Image.new('RGB',(1500,((len(results)+4)//5)*250),'#eee');draw=ImageDraw.Draw(sheet)
for i,row in enumerate(results):
    if 'file' not in row:print(row['slug'],row.get('error'));continue
    im=Image.open(ROOT/row['file']);im.thumbnail((280,215));x=(i%5)*300;y=(i//5)*250
    sheet.paste(im,(x+(300-im.width)//2,y));draw.text((x+8,y+225),row['slug'],fill='#222')
sheet.save(ROOT/'backend/.local/catalog-photos-review.jpg',quality=92)
print(json.dumps({r['slug']:[r.get('width'),r.get('height'),r.get('error')] for r in results}))
