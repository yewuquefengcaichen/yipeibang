from pathlib import Path
from PIL import Image, ImageDraw
files = [
 ('dashboard', Path('tmp_screens/paper-dashboard.png')),
 ('prepare', Path('tmp_screens/paper-prepare.png')),
 ('report', Path('tmp_screens/paper-report.png')),
 ('followup', Path('tmp_screens/paper-followup.png')),
 ('family', Path('tmp_screens/paper-family.png')),
]
imgs=[]
for name,p in files:
    im=Image.open(p).convert('RGB')
    im.thumbnail((360,250))
    imgs.append((name,im))
w,h=760,620
canvas=Image.new('RGB',(w,h),'white')
d=ImageDraw.Draw(canvas)
for i,(name,im) in enumerate(imgs):
    x=20+(i%2)*370
    y=25+(i//2)*190
    d.text((x,y),name,fill=(0,0,0))
    canvas.paste(im,(x,y+22))
out=Path('tmp_screens/paper-contact.jpg')
canvas.save(out,quality=92)
print(out)