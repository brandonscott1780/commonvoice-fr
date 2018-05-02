#!/usr/bin/env python3

import sys
import re
import argparse
import networkx as nx
import networkx.drawing.nx_pydot as nx_pydot

from xml.dom.pulldom import START_ELEMENT, CHARACTERS, END_ELEMENT, parse
from xml.dom.minidom import Element, Text

parser = argparse.ArgumentParser(description='SyceronBrut text content extraction for Common Voice')
parser.add_argument('--debug', action='store_true', help='Some debug')
parser.add_argument('--debug-more', action='store_true', help='Some more debug')

parser.add_argument('--print-tree', action='store_true', help='Only print XML tree structure')
parser.add_argument('--tree-output', type=argparse.FileType('w'), help='Where to store XML tree structure. Use \'-\' for stdout.')

parser.add_argument('file', type=str, help='Source XML file')

args = parser.parse_args()

doc = parse(args.file)
indent_level = 0
visited = []

structure = nx.DiGraph()

is_syceron = False

accepted_seance_context = [
  re.compile("CompteRendu@Metadonnees@DateSeance"),
  re.compile("CompteRendu@Metadonnees@Sommaire@Sommaire1@TitreStruct@Intitule"),
  re.compile("CompteRendu@Contenu@Quantiemes@Journee"),
  #re.compile("CompteRendu@Contenu@ouverture_seance@paragraphe@ORATEURS@ORATEUR@NOM"),
  re.compile(".*@paragraphe@texte.*"),
]
seance_context = None

for event, node in doc:
  if not is_syceron:
    if event == START_ELEMENT:
      is_syceron = node.tagName == "syceronBrut"
    continue

  if event == CHARACTERS:
    if type(node) == Text:
      if not node.nodeValue.isprintable():
        continue

  if event == START_ELEMENT:
    indent_level += 2
    if type(node) == Element:
      if args.print_tree and len(visited) > 0:
        structure.add_edge(visited[-1], node.tagName)

      visited.append(node.tagName)
      
      if node.tagName == "DateSeance":
        if not args.print_tree:
          print(seance_context)

        seance_context = {}

  if args.debug:
    print("DEBUG:", "/".join(visited), visited)
    print("DEBUG:", " "*indent_level, str(type(node)), ":", node.toxml())

  if type(node) == Text:
    visitedFullPath = "@".join(visited)

    if args.debug_more:
        print("DEBUG:", "visitedFullPath=" + visitedFullPath, ":", node.nodeValue, )

    if any(regex.match(visitedFullPath) for regex in accepted_seance_context):
      try:
        seance_context[visited[-1:][0]].append(node.nodeValue)
      except KeyError:
        seance_context[visited[-1:][0]] = [ node.nodeValue ]

  if event == END_ELEMENT:
    indent_level -= 2
    if type(node) == Element and len(visited) > 0:
      old = visited.pop()

if args.tree_output:
  print(nx_pydot.to_pydot(structure), file=sys.stdout if args.tree_output == '-' else args.tree_output)