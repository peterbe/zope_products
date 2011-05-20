from PIL import Image, ImageDraw, ImageFont
import os
base = r"C:\Documents and Settings\peterbe\Skrivbord\receptsamling\tabs"


fontBold = ImageFont.load("pilfonts/helvB10.pil") #helvB10.pil
fontReg = ImageFont.load("pilfonts/helvR10.pil") #helvB10.pil


texts = {'Kött':{'b':28,'r':30},
         'Vegetarisk':{'b':9,'r':10},
         'Fisk':{'b':29,'r':30},
         'Fågel':{'b':24,'r':26},
         'Förrätt':{'b':19,'r':22},
         'Efterrätt':{'b':17,'r':19},
         '5 senaste':{'b':14,'r':16}
         }


show_or_save = 0   # 1 for show, 0 for save

def safeid(sid):
    for k, v in {'Å':'A', 'Ä':'A', 'Ö':'O',
                 'å':'a', 'ä':'a', 'ö':'o'}.items():
        sid = sid.replace(k,v)
    return sid.replace(' ','')

imagebases = ({'imagebase':'checkedblank.jpg',
               'filenamestart':'checked-',
               'color':(102, 102, 102),
               'font':fontBold,
               'xmeasure':'b'},
              {'imagebase':'uncheckedblank.jpg',
               'filenamestart':'unchecked-',
               'color':(204, 204, 102),
               'font':fontReg,
               'xmeasure':'r'}
              )
              
for imagebase in imagebases:
    blank = imagebase['imagebase']
    filestart = imagebase['filenamestart']
    color = imagebase['color']
    font = imagebase['font']
    xmeasure = imagebase['xmeasure']
    for each, xdict in texts.items():
        x = xdict[xmeasure]
        im = Image.open(os.path.join(base, blank))
        draw = ImageDraw.Draw(im)

        
        draw.text((x, 4), each, font=font, fill=color)

        if show_or_save:
            im.show()
        else:
            filename= filestart+safeid(each).lower()+'.gif'
            im.save(os.path.join(base, 'gen', filename), format='GIF')


