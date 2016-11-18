#!/usr/bin/env python3

import argparse
import os
import re
import string
import sys
#from xml.dom.minidom import parseString as xml_parse

from bs4 import BeautifulSoup

def list_symbols() -> list:
    symbols = [['I','II','III','IV','V','VI','VII','VIII','IX','X']]
    symbols.append(list(string.ascii_uppercase))
    symbols.append([str(i) for i in range(1, 21)])
    symbols.append(list(string.ascii_lowercase))
    symbols.append(['i','ii','iii','iv','vi','vii','viii','ix','x'])
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

def format_list(soup, level=None, output=None) -> (list, int):
    if output is None:
        output = []
    if level is None:
        soup = format_list(soup.find('ol'), 0)
        level = 0
    for child in soup.contents:
        if child == '\n':
            continue
        if child.name == 'p':
            output.append(format_line(child.contents, level))
        elif child.name == 'ol':
            output.append(format_list(child, level+1, output))
    if level == 0:
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
    type_ = 'The type of the input file. Default: text. Other options: flat.'
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
            exit('ERROR: Input file doesn\'t exist')
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
    elif args.type == 'flat':
        soup = BeautifulSoup(infile, 'html.parser')
        list_ = format_list(soup)
        symbols = list_symbols()
        for line in infile:
            text, depth = parse_input_line(line, symbols)
            output.append(format_item(text, depth))
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
