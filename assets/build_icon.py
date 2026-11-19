"""Rasteriza la geometría de icon_windows.svg, sin alterar el logo comercial."""
from pathlib import Path
from PIL import Image,ImageDraw


def build():
    root=Path(__file__).resolve().parent
    scale=4
    canvas=Image.new('RGBA',(256*scale,256*scale),(0,0,0,0))
    draw=ImageDraw.Draw(canvas)
    navy='#203F78';orange='#F47724'
    draw.rounded_rectangle(tuple(v*scale for v in (4,4,252,252)),radius=52*scale,fill='white')
    draw.rounded_rectangle(tuple(v*scale for v in (12,12,244,244)),radius=44*scale,fill=navy)
    draw.polygon([(x*scale,y*scale) for x,y in ((49,198),(109,54),(151,54),(207,198),(164,198),(154,168),(101,168),(90,198))],fill=orange)
    draw.polygon([(x*scale,y*scale) for x,y in ((113,133),(142,133),(128,88))],fill=navy)
    canvas.save(root/'icon_windows.png')
    canvas.save(root/'logo_alonso.ico',format='ICO',sizes=[(16,16),(20,20),(24,24),(32,32),(40,40),(48,48),(64,64),(128,128),(256,256)])


if __name__=='__main__':build()
