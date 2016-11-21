#!/usr/bin/env python3

import argparse
import os
import re
import string
import sys
#from xml.dom.minidom import parseString as xml_parse

from bs4 import BeautifulSoup

html_types = set(('I','A','1','i','a'))

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
    assert isinstance(depth, int) and depth >= 0
    return '\t' * depth + text

def format_text_line(line: str, symbols: list) -> str:
    depth = 0
    parts = line.partition('.')
    if parts[1] == '.':
        for s in symbols:
            if parts[0] in s:
                break
            else:
                depth += 1
    return format_item(parts[2].strip(), depth)

def format_line(line, depth) -> str:
    o = []
    if not isinstance(line, list):
        line = [line]
    for l in line:
        l = l.extract()
        assert l is not None
        l = l.replace('\n', ' ').replace('\t', ' ')
        l = re.sub(r'\W+', ' ', l)
        o.append(format_item(l, depth))
    return '\n'.join(o)

#def format_list(soup, level=None, output=None) -> (list, int):
#    if output is None:
#        output = []
#    if level is None:
#        soup = format_list(soup.find('ol'), 0)
#        level = 0
#    for child in soup.contents:
#        if child == '\n':
#            continue
#        if child.name == 'p':
#            output.append(format_line(child.contents, level))
#        elif child.name == 'ol':
#            output.append(format_list(child, level+1, output))
#    if level == 0:
#        return output

def format_html(soup):
    output = []
    level = -1

    def iterate_children(children, level):
        level += 1
        for child in children:
            if child.name == 'p':
                output.append({'level': level, 'item': child})
            elif child.name == 'div' and child.attrs.get('type') in html_types:
                level += 1
                iterate_children(child, level)
            elif child.name == 'div' and child.attrs.get('type') not in html_types:
                iterate_children(child, level)

    def parse_items(item):
        
        def fix_str(st):
            st = st.replace('\n', ' ')
            return re.sub(r'\W+', ' ', st)

        item_level = item['level']
        item = item['item']
        accumulator = ['\t' * item_level]
        footnotes = []
        if hasattr(item, 'contents'):
            for i in item.contents:
                
                if hasattr(i, 'select') and i.select('a') and 'footnote' in i.a.get('href'):
                    href = i.a['href']
                    for parent in i.parents:
                        if parent.parent is None:
                            footnote = parent.select(href)[0].next_siblings
                            break
                    footnotes.append(parse_items({'level': item_level, 'item': str(footnote)}))
                    sys.stderr.write(repr(footnotes[-1]) + '\n')
                if isinstance(i, str):
                    accumulator.append(fix_str(i))
                elif i.name == 'i' and len(i.contents) == 1:
                    accumulator.append('__' + fix_str(i.contents[0]) + '__')
                elif i.name == 'b' and len(i.contents) == 1:
                    accumulator.append('**' + fix_str(i.contents[0]) + '**')
                elif (i.name == 'span' or i.name=='a') and i.strings is not None: # and len(i.contents) == 1:
                    accumulator.append(fix_str(''.join(list(i.strings))))
                else:
                    print(i)
                    exit("ERROR: I don't know what to do with this.")
        else:
            accumulator.append(item)
        o = [''.join(accumulator)]
        for f in footnotes:
            o.append('\n' + '\t' * item_level + f)
        return ''.join(o)
    
    for outer_list in soup.contents:
        if outer_list.name != 'div' or outer_list.attrs.get('type') not in html_types:
            continue
        #print(child)
        iterate_children(outer_list, level)
        break
    for i in range(len(output)):
        output[i] = parse_items(output[i])
    return output

def parse_input_line(line: str, symbols: list) -> (str, int):
    depth = 0
    parts = line.partition('.')
    if parts[1]: # If the separator was found and we have a list item
        for s in symbols:
            if parts[0] in s:
                break
            else:
                depth += 1
    return (parts[2].strip(), depth)

def parse_dom_for_bullets(dom):
    list_ = dom.getElementsByTagName('text:list')
    #output = 

def parse_args() -> argparse.Namespace:
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
        sys.stderr.write("WARNING!\n\tHTML mode is currently buggy and the results are almost certainly wrong.\n\tIf you're using this mode to fix the bugs, great.\n\tBut, if you're just looking for results, use --type=text.\n")
        soup = BeautifulSoup(infile, 'html.parser')
        output = format_html(soup)
        #list_ = format_list(soup)
        #symbols = list_symbols()
        #for line in infile:
        #    text, depth = parse_input_line(line, symbols)
        #    output.append(format_item(text, depth))
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
