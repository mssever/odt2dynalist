#!/usr/bin/env python3
#
################################################################################
# Important note:
# Because of the highly individual nature of the ODT files to be processed, each
# user will have to adjust this script according to their needs. It will fail
# out of the box unless you happen to format your source files the same way I
# do. Areas that I think you will most likely have to modify are commented with
# three leading hashes, like so: ###.
################################################################################

import argparse
import os
import re
import string
import sys

html_mode_available = True
try:
    from bs4 import BeautifulSoup
except ImportError:
    html_mode_available = False

# List types that may be set in HTML by LibreOffice. The type may also be unspecified.
html_types = set(('I','A','1','i','a', 'disc', 'circle', 'square'))

### These lists represent the sequence of outline levels in your original
### document, as they get converted to plain text by LibreOffice. You'll need to
### adjust it to match your usage. Make sure the order is correct (outermost
### first) and the lists are long enough to cover every possible list in your
### original. Note that if you have any levels which repeat symbols, invoking
### this script with --type=text will produce incorrect output.
###
### This function is only in use with --type=text in effect.
def list_symbols() -> list:
    '''These symbols are used when converting from plain text, not HTML.'''
    symbols = [['I','II','III','IV','V','VI','VII','VIII','IX','X']]
    symbols.append(list(string.ascii_uppercase))   # A, B, C, ..., Z
    symbols.append([str(i) for i in range(1, 21)]) # 1, 2, 3, ..., 20
    symbols.append(list(string.ascii_lowercase))   # a, b, c, ..., z
    symbols.append(['i','ii','iii','iv','v','vi','vii','viii','ix','x'])
    symbols.append(['α','β','γ','δ','ε'])
    return symbols

def format_item(text: str, depth: int) -> str:
    '''Add tabs to the beginning of each item.'''
    assert isinstance(depth, int) and depth >= 0
    return '\t' * depth + text

def format_text_line(line: str, symbols: list) -> str:
    '''Process a single item, when --type == "text"'''
    depth = 0
    parts = line.partition('.')
    if parts[1] == '.':
        for s in symbols:
            if parts[0] in s:
                break
            else:
                depth += 1
    return format_item(parts[2].strip(), depth)

# Only called when --type == 'html'
def format_html(soup):
    '''Formats the converted-to-html source for Dynalist'''
    output = []
    level = -1

    def iterate_children(children, level):
        '''Iterates over HTML list tags and figures out what is what.'''
        level += 1
        for child in children:
            if child.name == 'p':
                output.append({'level': level, 'item': child})
            elif child.name == 'div':
                iterate_children(child, level)
            #elif child.name == 'div' and child.attrs.get('type') not in html_types:
            #    iterate_children(child, level-1)

    def parse_items(item):
        '''Parses each item and converts it to a string formatted for Dynalist'''
        
        def fix_str(st):
            '''Removes extraneous newlines and whitespace'''
            st = st.replace('\n', ' ')
            return re.sub(r'\s+', ' ', st)

        def get_footnote(a):
            href = a['href']
            for parent in a.parents:
                if parent.parent is None:
                    footnote_arr = [i for i in parent.select(href)[0].next_siblings]
                    footnote = []
                    for fn in footnote_arr:
                        footnote.append(str(fn))
                    footnote = ''.join(footnote)
                    break
            return parse_items({'level': 0, 'item': '#fixme #footnote ' + str(footnote)})

        item_level = item['level']
        item = item['item']
        accumulator = ['\t' * item_level]
        footnotes = []
        if hasattr(item, 'contents'):
            for i in item.contents:
                if hasattr(i, 'select') and i.select('a') and 'footnote' in i.a.get('href'):
                    footnotes.append(get_footnote(i.a))
                # Search also for footnotes in the next sibling. If it's several
                # siblings later, it won't be found, currently.
                elif hasattr(i, 'nextSibling') and hasattr(i.nextSibling, 'name') and i.nextSibling.name == 'a' and i.nextSibling.get('href') and 'footnote' in i.nextSibling.get('href'):
                    footnotes.append(get_footnote(i.nextSibling))
                if isinstance(i, str):
                    accumulator.append(fix_str(i))
                elif i.name == 'i' and len(i.contents) == 1:
                    accumulator.append('__' + fix_str(i.contents[0]) + '__')
                elif i.name == 'b' and len(i.contents) == 1:
                    accumulator.append('**' + fix_str(i.contents[0]) + '**')
                elif (i.name == 'span' or i.name=='a') and i.strings is not None:
                    accumulator.append(fix_str(''.join(list(i.strings))))
                else:
                    print(i)
                    exit("ERROR: I don't know what to do with this.")
        else:
            item = item.replace('<i>', '__')
            item = item.replace('</i>', '__')
            item = item.replace('<b>', '**')
            item = item.replace('</b>', '**')
            item = re.sub(r'<[^>]{2,100}>', '', item)
            accumulator.append(item)
        o = [''.join(accumulator)]
        for f in footnotes:
            o.append('\n' + '\t' * item_level + f)
        return ''.join(o)
    
    for outer_list in soup.contents:
        if outer_list.name != 'div' or outer_list.attrs.get('type') not in html_types:
            continue
        iterate_children(outer_list, level)
        break
    for i in range(len(output)):
        tmp = parse_items(output[i])
        
        # The below is an ugly hack to get rid of extra spaces at the beginning
        # of a line. For some reason, re.sub was just corrupting things.
        if re.match(r'^([\t]*)[ ]+(\S+)', tmp):
            start = end = 0
            for j in range(len(tmp)):
                if start == 0 and tmp[j] != '\t':
                    start = j
                elif start > 0 and tmp[j] != ' ':
                    end = j
                    break
            output[i] = str(tmp[:start] + tmp[end:])
        else:
            output[i] = tmp
        
    return output

def parse_args() -> argparse.Namespace:
    '''Handles command-line arguments'''
    parser = argparse.ArgumentParser(description='''Converts LibreOffice sermon outlines to a format suitable for pasting into Dynalist.

    Prior to running this script, the sermon should already be exported as the specified type.''')
    infile = 'File to read for input. Default: stdin'
    outfile = 'File to write for output. Default: stdout'
    force = 'Overwrite the output file if it already exists'
    type_ = 'The type of the input file. Default: text. Other options: html.'
    add = parser.add_argument
    add('-i', '--infile', metavar='FILE', default=None, help=infile)
    add('-o', '--outfile', metavar='FILE', default=None, help=outfile)
    add('-f', '--force', action='store_true', default=False, help=force)
    add('-t', '--type', default='text', help=type_)
    return parser.parse_args()

def main():
    args = parse_args()
    if args.infile:
        if not os.path.isfile(args.infile):
            exit('ERROR: Input file doesn\'t exist: {}'.format(args.infile))
        with open(args.infile) as f:
            infile = f.read()
    else:
        with open(sys.stdin) as f:
            infile = f.read()
    if args.outfile and os.path.exists(args.outfile):
        if not os.path.isfile(args.outfile):
            exit("ERROR: Output file isn't a regular file")
        if not args.force:
            exit("ERROR: Can't overwrite existing output file. Use --force to override.")
    
    output = []

    if args.type == 'text':
        symbols = list_symbols()
        output = [format_text_line(i.strip(), symbols) for i in infile.split('\n') if len(i.strip()) > 0]
    elif args.type == 'html':
        if html_mode_available:
            soup = BeautifulSoup(infile, 'html.parser')
            output = format_html(soup)
        else:
            exit("ERROR: Please install Beautiful Soup 4 (Ubuntu package python-bs4) to use HTML mode.")
    else:
        exit("ERROR: Invalid input file type")
    
    if args.outfile:
        outfile = open(args.outfile, 'w')
    else:
        outfile = sys.stdout
    outfile.write('\n'.join([i for i in output if len(i) > 0]))
    outfile.close()

if __name__ == '__main__':
    main()
