"""Four-corner iRacing pit tire readings, in explicit fixed units."""
from shared.overlay import dashboard, panel, text, write_package, binding
import shared.overlay as style
CONNECTED = "[DataCorePlugin.GameRunning] && [DataCorePlugin.CurrentGame] == 'IRacing'"
RAW = "DataCorePlugin.GameRawData.Telemetry."
GLYPHS = {'0':'abcdef','1':'bc','2':'abdeg','3':'abcdg','4':'bcfg','5':'acdfg','6':'acdefg','7':'abc','8':'abcdefg','9':'abcdfg','-':'g'}

def reading(corner, pressure=False):
    props = [RAW + corner + 'coldPressure'] if pressure else [RAW + corner + 'tempC' + side for side in 'LMR']
    valid = ' && '.join(f"isnull([{p}],-1) >= 0" for p in props)
    value = f"[{props[0]}] / 6.894757293168" if pressure else '(' + ' + '.join(f'[{p}]' for p in props) + ') / 3.0'
    limit = 99.9 if pressure else 999
    valid += f" && ({value}) <= {limit}"
    if pressure: valid += f" && [{props[0]}] > 0"
    expr = f"if({CONNECTED},if({valid},format({value},'{ '00.0' if pressure else '000'}'),'---'),'---')"
    return expr, value

def build_tires(root, name, dash_id, screen_id, retro=False):
    if retro:
        style.DEFAULTS['panelAlpha']='FF'
        style.DEFAULTS['cornerRadius']=0
        monokai=next(t for t in style.THEMES if t['key']=='monokai')
        monokai['colors']['muted']=monokai['colors']['heading']
        monokai['colors']['primary']='#C8E69A'
    def rect(name,x,y,w,h,role='panel'):
        item=panel(w,h); item.update(Name=name,Left=x,Top=y)
        if role!='panel': style.themed(item,'BackgroundColor',role)
        return item
    items=[rect('Panel background',0,0,320,240)]
    if retro:
        items[0]['BackgroundColor']='#FF242725'; items[0].pop('Bindings',None)
        items.append(rect('LCD face',7,7,306,226))
    items += [text('Connection status','Waiting for iRacing',14,8,292,20,13,f"if({CONNECTED},'TIRE TEMP / PRESSURE','Waiting for iRacing')",role='heading'),
              text('Units label','AVG TEMP °C / COLD PSI',14,30,292,16,10,role='muted')]
    samples={'Connection status':'TIRE TEMP / PRESSURE'}
    for c,x,y,temp,psi in [('LF',14,54,'087','23.5'),('RF',170,54,'091','23.8'),('LR',14,137,'084','22.6'),('RR',170,137,'089','22.9')]:
        items.append(text(c+' label',c,x,y,136,18,12,role='heading'))
        for pressure,dx,sample in [(False,0,temp),(True,70,psi)]:
            n=c+(' pressure' if pressure else ' temperature'); expr,value=reading(c,pressure)
            item=text(n,'---',x+dx,y+21,66,32,24,expr)
            items.append(item); samples[n]=sample
            if retro:
                item['Visible']=False
                layout='00.0' if pressure else '000'; advance=16; h=24; dw=12; t=2
                geo={'a':(t,0,dw-2*t,t),'g':(t,11,dw-2*t,t),'d':(t,22,dw-2*t,t),'f':(0,t,t,8),'b':(10,t,t,8),'e':(0,14,t,7),'c':(10,14,t,7)}
                xpos=x+dx; ordinal=0
                for pos,ch in enumerate(layout):
                    if ch=='.':
                        items.append(rect(n+' decimal',xpos,y+44,2,2,'primary')); xpos+=5; continue
                    cell=rect(n+f' cell {pos}',xpos-1,y+20,14,28); cell.pop('Bindings',None);cell['BackgroundColor']='#28000000';items.append(cell)
                    divisor=10**(2-ordinal); ordinal+=1
                    digit=f'Floor(Round(({value}) * {10 if pressure else 1},0) / {divisor}) % 10'
                    for seg,(sx,sy,w,hh) in geo.items():
                        match=' || '.join(f'({digit}) == {d}' for d in '0123456789' if seg in GLYPHS[d])
                        active=f"if(({expr}) == '---',{'true' if seg=='g' else 'false'},({match}))"
                        part=rect(n+f' digit {pos} {seg}',xpos+sx,y+22+sy,w,hh,'primary')
                        part['Bindings']['Opacity']=binding(f'if({active},100,10)','Opacity')
                        part['Opacity']=100 if seg in GLYPHS[sample[pos]] else 10
                        items.append(part)
                    xpos+=advance
            items.append(text(n+' label','PSI' if pressure else '°C',x+dx,y+55,66,14,10,role='muted'))
    items.append(text('Update label','TEMPS: PIT READINGS',14,220,292,14,10,role='muted'))
    if retro:
        items += [rect('Horizontal rule',14,132,292,1,'muted'),rect('Vertical rule',158,54,1,159,'muted')]
    definition=dashboard(items,320,240,dash_id,screen_id,'Retro tire instruments' if retro else 'Tire readings')
    write_package(root,name,definition,'Four-corner average carcass temperature (°C) and garage cold pressure (PSI). Temperatures are pit readings.','0.1.0',samples)
