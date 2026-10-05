"""Native seven-segment readouts. No external font or image dependencies."""
from shared.overlay import binding

GLYPHS = {'0':'abcdef', '1':'bc', '2':'abdeg', '3':'abcdg',
          '4':'bcfg', '5':'acdfg', '6':'acdefg', '7':'abc',
          '8':'abcdefg', '9':'abcdfg', '-':'g', '+':'gh',
          ':':'ij', '.':'j'}


def readout(rect, name, expression, number, sample, left, top, width, height, split=False):
    """number is unsigned integer milliseconds; positions stay fixed for missing data."""
    items = []
    layout = '+000.000' if split else '00:00.000'
    advance = width / (7.6 if split else 8.1)
    digit_width = advance * .77
    thick = max(1.2, height * .105)
    middle = (height-thick)/2
    geometry = {
        'a':(thick,0,digit_width-2*thick,thick),
        'g':(thick,middle,digit_width-2*thick,thick),
        'd':(thick,height-thick,digit_width-2*thick,thick),
        'f':(0,thick,thick,middle-thick-1),
        'b':(digit_width-thick,thick,thick,middle-thick-1),
        'e':(0,middle+thick+1,thick,height-middle-2*thick-1),
        'c':(digit_width-thick,middle+thick+1,thick,height-middle-2*thick-1),
        'h':((digit_width-thick)/2,middle-height*.18,thick,height*.36),
        'i':((digit_width-thick)/2,height*.30,thick,thick),
        'j':((digit_width-thick)/2,height-thick,thick,thick),
    }
    missing = f"({expression}) == '{'---.---' if split else '--:--.---'}'"
    x = left
    numeric_positions = [i for i,c in enumerate(layout) if c == '0']
    for position, char in enumerate(layout):
        if char not in ':.':
            cell = rect(f'{name} digit {position} cell', x-1, top-2, digit_width+2, height+4)
            cell.pop('Bindings', None)
            cell['BackgroundColor'] = '#28000000'
            items.append(cell)
        if char in ':.' :
            segments = GLYPHS[char]
        elif char == '+':
            segments = 'gh'
        else:
            segments = 'abcdefg'
        for segment in segments:
            dx,dy,w,h = geometry[segment]
            if char in ':.':
                # Center punctuation between the previous digit edge and the next digit.
                dx = (digit_width - advance * .6 - thick) / 2
                if char == ':' and segment == 'j':
                    dy = height * .70
            item = rect(f'{name} digit {position} {segment}', x+dx, top+dy, w, h, 'primary')
            if char in ':.':
                active = 'true'
            elif char == '+':
                active = f"!({missing})" if segment == 'g' else f"!({missing}) && ({number[1]}) >= 0"
            else:
                ordinal = numeric_positions.index(position)
                if split:
                    divisor = 10 ** (5-ordinal)
                    value = f'Floor(({number[0]}) / {divisor}) % 10'
                else:
                    divisors = [600000,60000,10000,1000,100,10,1]
                    value = f'Floor(({number}) / {divisors[ordinal]}) % {6 if ordinal == 2 else 10}'
                digits = [digit for digit in '0123456789' if segment in GLYPHS[digit]]
                matches = ' || '.join(f'({value}) == {digit}' for digit in digits)
                active = f"if({missing},{'true' if segment == 'g' else 'false'},({matches}))"
            item['Bindings']['Opacity'] = binding(f'if({active},100,10)', 'Opacity')
            # Preview uses the same sample glyphs as the text-format verification.
            sample_position = position if not split or len(sample) == 8 else position-1
            sample_char = sample[sample_position] if sample_position >= 0 else ' '
            item['Opacity'] = 100 if segment in GLYPHS.get(sample_char,'') else 10
            items.append(item)
        x += advance * (.4 if char in ':.' else 1)
    return items
