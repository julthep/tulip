# -*- coding: utf-8 -*-
"""
@author: julthep
"""

__author__ = "Julthep Nandakwang"
__version__ = "0.1.0"
__license__ = "LGPL-3.0"

import requests
import bs4

from rdflib import Graph, Namespace, URIRef     #, Literal
from rdflib.collection import Collection
from rdflib.namespace import RDF    #, RDFS, FOAF
from urllib.parse import urljoin

session = requests.Session()

en_wiki_prefix    = 'http://en.wikipedia.org/wiki/'
base_url          = ''      # initial set global base_url

class Tulip:
    def __init__(self, size):
        self.member = [ Tulip(0) for _ in range(size) ]
        self.type   = {'Group': None, 'Item':      None, 
                       'Page':  None, 'Paragraph': None, 
                       'Table': None, 'Column':    None, 'Row': None, 'Cell': None, 
                       'List':  None, 'ListItem':  None}
        self.label  = None
        self.style  = {'Identified': None, 
                       'ColSpanned': None, 'RowSpanned': None, 
                       'ColSpanBrk': None, 'RowSpanBrk': None, 
                       'Enumerated': None}
        self.dimension = None
        self.link = {}
        self.local = {'Hidden': None, 'ColSpan': None, 'RowSpan': None}
    def __len__(self):
        return len(self.member)
    def __getitem__(self, index):
        return self.member[index]
    def __setitem__(self, index, value):
        self.member[index] = value
    def __delitem__(self, index):
        del self.member[index]

def read_file(filename):
    """
    read_file(str:filename)
    return str:Text
    """
    print('Reading file', filename)
    return open(filename, 'r', encoding='utf-8').read()

def write_file(text, filename):
    """
    write_file(str:text, str:filename)
    """
    print('Writing file', filename)
    open(filename, 'w', encoding='utf-8').write(text)

def read_url(url):
    """
    read_url(str:URL)
    return str:Text
    """
    global base_url
    base_url = url             # store global base_url
    print('Reading url', url)
    s = session.get(url)
    if s.ok is False:
        return None
    return s.text

def parse_html(html):
    """
    parse_html(str:html)
    return Tulip
    """
    return bs2tulip(bs4.BeautifulSoup(html, "html.parser"))

def parse_article(article):
    """
    parse_article(str:Wikipedia_article_name)
    return Tulip
    """
    bso = bs4.BeautifulSoup(read_url(en_wiki_prefix + article.replace(" ","_")), "html.parser")
    
    # decompose: remove unneeded elements
    for tag in bso.find_all('script'):
        tag.decompose()
    for tag in bso.find_all('style'):
        tag.decompose()
    for tag in bso.find_all('div', class_=['navbox','suggestions']):
        tag.decompose()
    # div:id:mw-navigation
    #     mw-head
    #         p-personal, left-navigation, right-navigation, ul:class:menu
    #     mw-panel
    #         p-navigation, p-interaction, p-tb, p-wikibase-otherprojects, p-coll-print_export, p-lang
    #         div:class:portal, div:class:body
    # div:id:footer
    #     ul:id:footer-info, ul:id:footer-places ul:id:footer-icons
    for tag in bso.find_all('div', id=['visual-history-container','mw-page-base','mw-head-base',
                                       'mw-data-after-content','mw-head','p-navigation','p-interaction',
                                       'footer','mwe-popups-svg']):
        tag.decompose()
    for tag in bso.find_all('span', class_=['mw-cite-backlink','mw-editsection','tocnumber']):
        tag.decompose()
    # "coordinates" on the top right of each page usually redundant with article content
    for tag in bso.find_all('span', id=['coordinates']):
        tag.decompose()
    # better keep style="display:none" for further check its need
    for tag in bso.find_all('table', class_=['navbox','mbox-small','plainlinks','sistersitebox']):
        tag.decompose()
    for tag in bso.find_all('sup', class_=['reference','noprint']):
        tag.decompose()
    # unwrap: remove some tags that have problem with data structure and keep their children
    for tag in bso.find_all('div', class_=['plainlist']):
        tag.unwrap()
    return bs2tulip(bso)

def bs2tulip(bso):
    """
    bs2tulip(BeautifulSoup:bso)
    return Tulip:tulip
    """
    print('Parsing HTML')
    tulips = bso.find_all(['table','ul','ol'])
    tulip = Tulip(len(tulips))
    tulip.type['Page'] = True
    # workaround for Wikipedia derived page
    tulip.label = bso.find('title').get_text().strip().replace(' - Wikipedia','')
    tulip_idx = 0
    for tulip_grp in tulips:
        if tulip_grp.name == 'table':
            # find max col and row
            max_col_count = 0
            max_row_adjust = 0
            all_rows = tulip_grp.find_all('tr')
            for row in all_rows:
                col_count = 0
                row_adjust = 0
                for cell in row.find_all(['th','td'], recursive=False):
                    col_count += int(cell.get('colspan', 1))
                    if int(cell.get('rowspan', 0)) != 0:
                        row_adjust += int(cell.get('rowspan'))
                        if row_adjust > max_row_adjust:
                            max_row_adjust = row_adjust
                if col_count > max_col_count:
                    max_col_count = col_count
                if max_row_adjust > 0:
                    max_row_adjust -= 1
            # reserve col
            tulip[tulip_idx] = Tulip(max_col_count)
            # reserve row
            for col in range(max_col_count):
                tulip[tulip_idx][col] = Tulip(len(all_rows)+max_row_adjust)
                tulip[tulip_idx][col].type['Column'] = True    # optional, no need in process
            max_dim = 2
            # generate table properties
            tulip[tulip_idx].type['Table'] = True
            caption = tulip_grp.find('caption', recursive=False)
            if caption != None:
                for br_tag in caption.find_all('br'):
                    br_new = bso.new_tag('newbr')
                    br_new.string = '\n'
                    br_tag.replace_with(br_new)
                tulip[tulip_idx].label = caption.get_text().strip()
            # workaround to temporary get table header
            else:
                for header in tulip_grp.previous_elements:
                    if header.name in ['h1','h2','h3','h4','h5','h6']:
                        tulip[tulip_idx].label = '\n'.join(filter(lambda x: x != '', 
                                                                   map(lambda x: x.strip(), 
                                                                       header.get_text().splitlines())))
                        break
            # store loop
            # row loop
            for row_idx, row in enumerate(all_rows):
                col_idx = 0
                # col/cell loop
                for cell in row.find_all(['th','td'], recursive=False):
                    src_list_items = Tulip(0)
                    i_list = cell.find(['ul','ol'], recursive=False)
                    if i_list != None:
                        i_rows = i_list.find_all('li', recursive=False)
                        src_list_items = Tulip(len(i_rows))
                        src_list_items.style['Enumerated'] = (None, True)[i_list.name == 'ol']
                        if max_dim < 3: max_dim = 3
                        for i_idx, i_row in enumerate(i_rows):
                            for un_tag in i_row.find_all(['table','ul','ol'], recursive=False):
                                un_tag.decompose()
                            for br_tag in i_row.find_all('br'):
                                br_new = bso.new_tag('newbr')
                                br_new.string = '\n'
                                br_tag.replace_with(br_new)
                            src_list_items[i_idx].label = i_row.get_text().strip()
                    for un_tag in cell.find_all(['table','ul','ol'], recursive=False):
                        un_tag.decompose()
                    for br_tag in cell.find_all('br'):
                        br_new = bso.new_tag('newbr')
                        br_new.string = '\n'
                        br_tag.replace_with(br_new)
                    # Caution: can't set 'label' to None, None need for cell span checking loop for TULIP table nodes creation
                    #      *** but after completly created TULIP table/column/cell nodes from spanned 'not None' cells
                    #          'label' could be None, for example, when reading them back from RDF Turtle/N-Triples
                    src_label = '\n'.join(filter(lambda x: x != '', 
                                                  map(lambda x: x.strip(), cell.get_text().splitlines())))
                    src_link = {}
                    for a_tag in cell.find_all('a', href=True):
                        if a_tag.get_text().strip() != '':
                            src_link['text:' + a_tag.get_text().strip()] = urljoin(base_url, a_tag.get('href'))
                        else:
                            for a_img in a_tag.find_all('img'):
                                if a_img.get('src') != '':
                                    src_link['image:' + urljoin(base_url, a_tag.find('img').get('src'))] = urljoin(base_url, a_tag.get('href'))
                    src_header = (None, True)[cell.name == 'th']
                    src_col_span = True if cell.get('colspan', 0) else None
                    src_row_span = True if cell.get('rowspan', 0) else None
                    row_span = int(cell.get('rowspan', 1))   # need int to processing
                    col_span = int(cell.get('colspan', 1))   # need int to processing
                    for rspan in range(row_span):
                        for cspan in range(col_span):
                            # move to next col/cell to skip rowspanned cells previously store
                            while tulip[tulip_idx][col_idx+cspan][row_idx+rspan].label != None:
                                col_idx += 1
                            # inner list
                            i_rows = src_list_items
                            if len(i_rows) != 0:
                                tulip[tulip_idx][col_idx+cspan][row_idx+rspan] = Tulip(len(i_rows))
                                for i_idx, i_row in enumerate(i_rows):
                                    tulip[tulip_idx][col_idx+cspan][row_idx+rspan][i_idx].type['Item'] = True   # optional, no need in process
                                    tulip[tulip_idx][col_idx+cspan][row_idx+rspan][i_idx].label = i_row.label
                            tulip[tulip_idx][col_idx+cspan][row_idx+rspan].type['Cell'] = True            # optional, no need in process
                            tulip[tulip_idx][col_idx+cspan][row_idx+rspan].label = src_label   # can't set to None, None need for span checker
                            tulip[tulip_idx][col_idx+cspan][row_idx+rspan].link = src_link
                            tulip[tulip_idx][col_idx+cspan][row_idx+rspan].style['Identified'] = src_header
                            tulip[tulip_idx][col_idx+cspan][row_idx+rspan].style['Enumerated'] = src_list_items.style['Enumerated']
                            tulip[tulip_idx][col_idx+cspan][row_idx+rspan].style['ColSpanned'] = src_col_span
                            tulip[tulip_idx][col_idx+cspan][row_idx+rspan].style['RowSpanned'] = src_row_span
                    # adjust ahead to next col after span loop
                    col_idx += col_span
            tulip[tulip_idx].dimension = max_dim
        elif tulip_grp.name == 'ul' or tulip_grp.name == 'ol':
            max_dim = 0
            level = 0
            def _tulip_list_recursion(tulip, idx, pass_tag, max_dim=0, level=0):
                ### begin of recursion
                level += 1
                item_tags = pass_tag.find_all('li', recursive=False)
                tulip[idx] = Tulip(len(item_tags))
                tulip[idx].type['List'] = True
                tulip[idx].style['Enumerated'] = (None, True)[pass_tag.name == 'ol']
                # workaround to temporary get table header
                # to do: move to below after level -= 1 to test get label after decompose ul/ol
                if level == 1:     # if the first call, not in recursion
                    for header in pass_tag.previous_elements:
                        if header.name in ['h1','h2','h3','h4','h5','h6']:
                            tulip[idx].label = '\n'.join(filter(lambda x: x != '', 
                                                                 map(lambda x: x.strip(), 
                                                                     header.get_text().splitlines())))
                            break
                if max_dim < level: max_dim = level
                # list item loop
                for item_idx, item_tag in enumerate(item_tags):
                    list_tag = item_tag.find(['ul','ol'], recursive=False)
                    if list_tag != None:
                        ### point of recursion
                        max_dim, level = _tulip_list_recursion(tulip[idx], item_idx, list_tag, 
                                                                max_dim, level)
                    for un_tag in item_tag.find_all(['ul','ol'], recursive=False):
                        un_tag.decompose()
                    for br_tag in item_tag.find_all('br'):
                        br_new = bso.new_tag('newbr')
                        br_new.string = '\n'
                        br_tag.replace_with(br_new)
                    tulip[idx][item_idx].type['Item'] = True     # optional, no need in process
                    # break lines > remove leading/trailing white spaces each line > remove blank lines > merge them again
                    tulip[idx][item_idx].label = '\n'.join(filter(lambda x: x != '', 
                                                                   map(lambda x: x.strip(), 
                                                                       item_tag.get_text().splitlines())))
                    for a_tag in item_tag.find_all('a', href=True):
                        if a_tag.get_text().strip() != '':
                            tulip[idx][item_idx].link['text:' + a_tag.get_text().strip()] = urljoin(base_url, a_tag.get('href'))
                        elif a_tag.find('img').get('src') != '':
                            tulip[idx][item_idx].link['image:' + urljoin(base_url, a_tag.find('img').get('src'))] = urljoin(base_url, a_tag.get('href'))
                level -= 1
                return max_dim, level
                ### end of recursion
            max_dim, level = _tulip_list_recursion(tulip, tulip_idx, tulip_grp, max_dim, level)
            tulip[tulip_idx].dimension = max_dim
        if tulip[tulip_idx].member != [] or tulip[tulip_idx].label != None:
            tulip_idx += 1
    # clean up tail unused reserved members
    for _ in range(len(tulip)):
        if len(tulip[-1]) == 0:
            del tulip[-1]
        else:
            break
    return tulip

def gen_turtle(tulip):
    """
    gen_turtle(Tulip:tulip)
    return str:Turtle
    """
    print('Generating Turtle')
    indent = ' '*4
    # dummy header for Wikipedia page derived resources
    turtle = '''@prefix rdf: <http://www.w3.org/1999/02/22-rdf-syntax-ns#> .
@prefix rdfs: <http://www.w3.org/2000/01/rdf-schema#> .
@prefix owl: <http://www.w3.org/2002/07/owl#> .
@prefix prov: <http://www.w3.org/ns/prov#> .
@prefix foaf: <http://xmlns.com/foaf/0.1/> .
@prefix wikipedia: <http://en.wikipedia.org/wiki/> .
@prefix dbpedia: <http://dbpedia.org/resource/> .
@prefix tlp: <http://purl.org/tulip/ns#> .
@prefix tlpedia: <http://tlpedia.org/resource/> .

tlpedia:''' + tulip.label.replace(' ','_') + '''
    owl:sameAs dbpedia:''' + tulip.label.replace(' ','_') + ''' ;
    prov:wasDerivedFrom <http://en.wikipedia.org/wiki/''' + tulip.label.replace(' ','_') + '''?oldid=> ;
    foaf:isPrimaryTopicOf wikipedia:''' + tulip.label.replace(' ','_') + ''' ;
    foaf:name "''' + tulip.label + '''" ;
    tlp:indexList ( 0 ) ;
    rdfs:label "''' + tulip.label + '''" ;
    rdf:type tlp:Page ;
'''
    elem_pred_added = False
    for i in range(len(tulip)):
        level = 0
        if tulip[i].type['Table']:
            if tulip[i].member != [] or tulip[i].label != None:
                level += 1
                if not elem_pred_added:
                    turtle += indent*(level*2-1) + 'tlp:member\n'
                    elem_pred_added = True
                turtle += indent*(level*2) + '[\n'
                turtle += indent*(level*2+1) + 'tlp:index ' + str(i+1) + ' ;\n'
                turtle += indent*(level*2+1) + 'tlp:indexList ( ' + str(i+1) + ' 0 ) ;\n'
                turtle += indent*(level*2+1) + 'rdf:type tlp:Table ;\n'
                label = tulip[i].label
                if label != None:
                    if label.find('\n') != -1 or label.find('"') != -1:
                        turtle += indent*(level*2+1) + 'rdfs:label """' + label + '""" ;\n'
                    else:
                        turtle += indent*(level*2+1) + 'rdfs:label "' + label + '" ;\n'
                if tulip[i].link != {}:
                    turtle += indent*(level*2+1) + 'tlp:link\n'
                    for key, url in tulip[i].link.items():
                        turtle += indent*(level*2+2) + '[\n'
                        if key[:5] == 'text:':
                            if key.find('\n') != -1 or key.find('"') != -1:
                                turtle += indent*(level*2+3) + 'tlp:text """' + key[5:] + '""" ;\n'
                            else:
                                turtle += indent*(level*2+3) + 'tlp:text "' + key[5:] + '" ;\n'
                        elif key[:6] == 'image:':
                            turtle += indent*(level*2+3) + 'tlp:image <' + key[6:] + '> ;\n'
                        turtle += indent*(level*2+3) + 'tlp:url <' + url + '>\n'
                        turtle += indent*(level*2+2) + '] ,\n'
                    turtle = turtle[:-3] + ' ;\n'
                if tulip[i].dimension != None:
                    turtle += indent*(level*2+1) + 'tlp:dimension ' + str(tulip[i].dimension) + ' ;\n'
                elem_pred_added_j = False
                for j in range(len(tulip[i])):
                    label = tulip[i][j].label
                    if tulip[i][j].member != [] or label != None:
                        level += 1
                        if not elem_pred_added_j:
                            turtle += indent*(level*2-1) + 'tlp:member\n'
                            elem_pred_added_j = True
                        turtle += indent*(level*2) + '[\n'
                        turtle += indent*(level*2+1) + 'tlp:index ' + str(j+1) + ' ;\n'
                        turtle += indent*(level*2+1) + 'tlp:indexList ( ' + str(i+1) + ' ' + str(j+1) + ' 0 ) ;\n'
                        turtle += indent*(level*2+1) + 'rdf:type tlp:Column ;\n'
                        if label != None:
                            if label.find('\n') != -1 or label.find('"') != -1:
                                turtle += indent*(level*2+1) + 'rdfs:label """' + label + '""" ;\n'
                            else:
                                turtle += indent*(level*2+1) + 'rdfs:label "' + label + '" ;\n'
                        if tulip[i][j].link != {}:
                            turtle += indent*(level*2+1) + 'tlp:link\n'
                            for key, url in tulip[i][j].link.items():
                                turtle += indent*(level*2+2) + '[\n'
                                if key[:5] == 'text:':
                                    if key.find('\n') != -1 or key.find('"') != -1:
                                        turtle += indent*(level*2+3) + 'tlp:text """' + key[5:] + '""" ;\n'
                                    else:
                                        turtle += indent*(level*2+3) + 'tlp:text "' + key[5:] + '" ;\n'
                                elif key[:6] == 'image:':
                                    turtle += indent*(level*2+3) + 'tlp:image <' + key[6:] + '> ;\n'
                                turtle += indent*(level*2+3) + 'tlp:url <' + url + '>\n'
                                turtle += indent*(level*2+2) + '] ,\n'
                            turtle = turtle[:-3] + ' ;\n'
                        elem_pred_added_k = False
                        for k in range(len(tulip[i][j])):
                            label = tulip[i][j][k].label
                            if tulip[i][j][k].member != [] or label != None:
                                level += 1
                                if not elem_pred_added_k:
                                    turtle += indent*(level*2-1) + 'tlp:member\n'
                                    elem_pred_added_k = True
                                turtle += indent*(level*2) + '[\n'
                                turtle += indent*(level*2+1) + 'tlp:index ' + str(k+1) + ' ;\n'
                                turtle += indent*(level*2+1) + 'tlp:indexList ( ' + str(i+1) + ' ' + str(j+1) + ' ' + str(k+1) + ' 0 ) ;\n'
                                turtle += indent*(level*2+1) + 'rdf:type tlp:Cell ;\n'
                                if label != None:
                                    if label.find('\n') != -1 or label.find('"') != -1:
                                        turtle += indent*(level*2+1) + 'rdfs:label """' + label + '""" ;\n'
                                    else:
                                        turtle += indent*(level*2+1) + 'rdfs:label "' + label + '" ;\n'
                                    for key in [ key for key,v in tulip[i][j][k].style.items() if v is not None ]:
                                        turtle += indent*(level*2+1) + 'tlp:style tlp:' + key + ' ;\n'
                                if tulip[i][j][k].link != {}:
                                    turtle += indent*(level*2+1) + 'tlp:link\n'
                                    for key, url in tulip[i][j][k].link.items():
                                        turtle += indent*(level*2+2) + '[\n'
                                        if key[:5] == 'text:':
                                            if key.find('\n') != -1 or key.find('"') != -1:
                                                turtle += indent*(level*2+3) + 'tlp:text """' + key[5:] + '""" ;\n'
                                            else:
                                                turtle += indent*(level*2+3) + 'tlp:text "' + key[5:] + '" ;\n'
                                        elif key[:6] == 'image:':
                                            turtle += indent*(level*2+3) + 'tlp:image <' + key[6:] + '> ;\n'
                                        turtle += indent*(level*2+3) + 'tlp:url <' + url + '>\n'
                                        turtle += indent*(level*2+2) + '] ,\n'
                                    turtle = turtle[:-3] + ' ;\n'
                                ### begin of recursion
                                # inner list
                                elem_pred_added_l = False
                                for l in range(len(tulip[i][j][k])):
                                    label = tulip[i][j][k][l].label
                                    if tulip[i][j][k][l].member != [] or label != None:
                                        level += 1
                                        if not elem_pred_added_l:
                                            turtle += indent*(level*2-1) + 'rdf:type tlp:List ;\n'
                                            turtle += indent*(level*2-1) + 'tlp:member\n'
                                            elem_pred_added_l = True
                                        turtle += indent*(level*2) + '[\n'
                                        turtle += indent*(level*2+1) + 'tlp:index ' + str(l+1) + ' ;\n'
                                        turtle += indent*(level*2+1) + 'tlp:indexList ( ' + str(i+1) + ' ' + str(j+1) + ' ' + str(k+1) + ' ' + str(l+1) + ' 0 ) ;\n'
                                        turtle += indent*(level*2+1) + 'rdf:type tlp:Item ;\n'
                                        if label != None:
                                            if label.find('\n') != -1 or label.find('"') != -1:
                                                turtle += indent*(level*2+1) + 'rdfs:label """' + label + '""" ;\n'
                                            else:
                                                turtle += indent*(level*2+1) + 'rdfs:label "' + label + '" ;\n'
                                        if tulip[i][j][k][l].link != {}:
                                            turtle += indent*(level*2+1) + 'tlp:link\n'
                                            for key, url in tulip[i][j][k][l].link.items():
                                                turtle += indent*(level*2+2) + '[\n'
                                                if key[:5] == 'text:':
                                                    if key.find('\n') != -1 or key.find('"') != -1:
                                                        turtle += indent*(level*2+3) + 'tlp:text """' + key[5:] + '""" ;\n'
                                                    else:
                                                        turtle += indent*(level*2+3) + 'tlp:text "' + key[5:] + '" ;\n'
                                                elif key[:6] == 'image:':
                                                    turtle += indent*(level*2+3) + 'tlp:image <' + key[6:] + '> ;\n'
                                                turtle += indent*(level*2+3) + 'tlp:url <' + url + '>\n'
                                                turtle += indent*(level*2+2) + '] ,\n'
                                            turtle = turtle[:-3] + ' ;\n'
                                        ### point of recursion
                                        turtle = turtle[:-3] + '\n'
                                        turtle += indent*(level*2) + '] ,\n'
                                        level -= 1
                                ### end of recursion
                                turtle = turtle[:-3] + '\n'
                                turtle += indent*(level*2) + '] ,\n'
                                level -= 1
                        turtle = turtle[:-3] + '\n'
                        turtle += indent*(level*2) + '] ,\n'
                        level -= 1
                turtle = turtle[:-3] + '\n'
                turtle += indent*(level*2) + '] ,\n'
                level -= 1
        elif tulip[i].type['List']:
            def _turtle_list_recursion(turtle, tulip, idx, index_list, level=0, elem_pred_added=False):
                ### begin of recursion
                indent = ' '*4
                label = tulip[idx].label
                if tulip[idx].member != [] or label != None:
                    level += 1
                    if not elem_pred_added:
                        if level != 1:        # if in recursion, not the first call
                            turtle += indent*(level*2-1) + 'rdf:type tlp:List ;\n'
                        turtle += indent*(level*2-1) + 'tlp:member\n'
                        elem_pred_added = True
                    turtle += indent*(level*2) + '[\n'
                    turtle += indent*(level*2+1) + 'tlp:index ' + str(idx+1) + ' ;\n'
                    index_list += ' ' + str(idx+1)
                    turtle += indent*(level*2+1) + 'tlp:indexList (' + index_list + ' 0 ) ;\n'
                    if level != 1:        # if in recursion, not the first call
                        turtle += indent*(level*2+1) + 'rdf:type tlp:Item ;\n'
                    if tulip[idx].style['Enumerated'] != None:
                        turtle += indent*(level*2+1) + 'tlp:style tlp:Enumerated ;\n'
                    if tulip[idx].dimension != None:
                        turtle += indent*(level*2+1) + 'tlp:dimension ' + str(tulip[idx].dimension) + ' ;\n'
                    if label != None:
                        if label.find('\n') != -1 or label.find('"') != -1:
                            turtle += indent*(level*2+1) + 'rdfs:label """' + label + '""" ;\n'
                        else:
                            turtle += indent*(level*2+1) + 'rdfs:label "' + label + '" ;\n'
                    if tulip[idx].link != {}:
                        turtle += indent*(level*2+1) + 'tlp:link\n'
                        for key, url in tulip[idx].link.items():
                            turtle += indent*(level*2+2) + '[\n'
                            if key[:5] == 'text:':
                                if key.find('\n') != -1 or key.find('"') != -1:
                                    turtle += indent*(level*2+3) + 'tlp:text """' + key[5:] + '""" ;\n'
                                else:
                                    turtle += indent*(level*2+3) + 'tlp:text "' + key[5:] + '" ;\n'
                            elif key[:6] == 'image:':
                                turtle += indent*(level*2+3) + 'tlp:image <' + key[6:] + '> ;\n'
                            turtle += indent*(level*2+3) + 'tlp:url <' + url + '>\n'
                            turtle += indent*(level*2+2) + '] ,\n'
                        turtle = turtle[:-3] + ' ;\n'
                    # nested list
                    child_elem_pred_added = False
                    for next in range(len(tulip[idx])):
                        ### point of recursion
                        turtle, level, child_elem_pred_added = _turtle_list_recursion(turtle, tulip[idx], 
                                                        next, index_list, level, child_elem_pred_added)
                    turtle = turtle[:-3] + '\n'
                    turtle += indent*(level*2) + '] ,\n'
                    level -= 1
                return turtle, level, elem_pred_added
                ### end of recursion
            turtle, level, elem_pred_added = _turtle_list_recursion(turtle, tulip, i, '', level, elem_pred_added)
    turtle = turtle[:-3] + '\n'
    turtle += '.'
    return turtle

def add_elem(pre_file, post_file, format):
    """
    add_elem(str:pre_filename, str:post_filename, str:RDF_format)
    """
    print('Updating', pre_file, 'with tlp:element to', post_file)
    g = Graph()
    g.parse(pre_file, format=format)
    g.update('''PREFIX rdf: <http://www.w3.org/1999/02/22-rdf-syntax-ns#>
        PREFIX tlp: <http://purl.org/tulip/ns#>
        INSERT {
            ?s tlp:element ?b .
        }
        WHERE {
            ?s rdf:type tlp:Page .
            ?s tlp:member+ ?b . 
        }''')
    g.serialize(destination=post_file, format=format)

def parse_rdf(rdf_text, format):
    """
    parse_rdf(str:RDF text, str:RDF serialization format)
    return Tulip:tulip
    """
    print('Parsing RDF in', format)
    tlp_prefix = 'http://purl.org/tulip/ns#'
    tlp     = Namespace(tlp_prefix)
    G = Graph()
    G.parse(data=rdf_text, format=format)
    # find dimension
    len_dict = dict()
    for s,p,o in G:
        if p == URIRef('http://purl.org/tulip/ns#indexList'):
            c = list(Collection(G, o))
            c1 = c2 = c3 = c4 = None
            c0 = int(c[0])-1
            try:
                c1 = int(c[1])-1
            except IndexError:
                pass
            else:
                try:
                    c2 = int(c[2])-1
                except IndexError:
                    pass
                else:
                    try:
                        c3 = int(c[3])-1
                    except IndexError:
                        pass
                    else:
                        try:
                            c4 = int(c[4])-1
                        except IndexError:
                            pass
            if c4 != None and c4 != -1:
                try:
                    if len_dict[str([c0,c1,c2,c3,c4])] < 1: len_dict[str([c0,c1,c2,c3,c4])] = 1
                except KeyError:
                    len_dict[str([c0,c1,c2,c3,c4])] = 1
                try:
                    if len_dict[str([c0,c1,c2,c3])] < c4+1: len_dict[str([c0,c1,c2,c3])] = c4+1
                except KeyError:
                    len_dict[str([c0,c1,c2,c3])] = c4+1
            if c3 != None and c3 != -1:
                try:
                    if len_dict[str([c0,c1,c2])] < c3+1: len_dict[str([c0,c1,c2])] = c3+1
                except KeyError:
                    len_dict[str([c0,c1,c2])] = c3+1
            if c2 != None and c2 != -1:
                try:
                    if len_dict[str([c0,c1])] < c2+1: len_dict[str([c0,c1])] = c2+1
                except KeyError:
                    len_dict[str([c0,c1])] = c2+1
            if c1 != None and c1 != -1:
                try:
                    if len_dict[str([c0])] < c1+1: len_dict[str([c0])] = c1+1
                except KeyError:
                    len_dict[str([c0])] = c1+1
            if c0 != None and c0 != -1:
                try:
                    if len_dict[str([])] < c0+1: len_dict[str([])] = c0+1
                except KeyError:
                    len_dict[str([])] = c0+1
    # researve Tulip
    tulip = Tulip(len_dict[str([])])
    for i in range(len_dict[str([])]):
        try:
            tulip[i] = Tulip(len_dict[str([i])])
            for j in range(len_dict[str([i])]):
                try:
                    tulip[i][j] = Tulip(len_dict[str([i,j])])
                    for k in range(len_dict[str([i,j])]):
                        try:
                            tulip[i][j][k] = Tulip(len_dict[str([i,j,k])])
                            for l in range(len_dict[str([i,j,k])]):
                                try:
                                    tulip[i][j][k][l] = Tulip(len_dict[str([i,j,k,l])])
                                except KeyError:
                                    pass
                        except KeyError:
                            pass
                except KeyError:
                    pass
        except KeyError:
            pass
    # store Tulip
    for s,p,o in G:
        if p == URIRef('http://purl.org/tulip/ns#indexList'):
            c = list(Collection(G, o))
            c0 = c1 = c2 = c3 = c4 = -1
            try:
                c0 = int(c[0])-1
            except IndexError:
                pass
            else:
                try:
                    c1 = int(c[1])-1
                except IndexError:
                    pass
                else:
                    try:
                        c2 = int(c[2])-1
                    except IndexError:
                        pass
                    else:
                        try:
                            c3 = int(c[3])-1
                        except IndexError:
                            pass
                        else:
                            try:
                                c4 = int(c[4])-1
                            except IndexError:
                                pass
            def _set_prop(tulip, G, s):
                if str(G.label(s)) != '':
                    # replace NTriples newline '\r\n' to '\n'
                    tulip.label = str(G.label(s)).replace('\r\n','\n')
                for i in G.objects(s,RDF.type):
                    tulip.type[i.replace(tlp_prefix,'')] = True
                for i in G.objects(s,tlp.style):
                    tulip.style[i.replace(tlp_prefix,'')] = True
                for i in G.objects(s,tlp.dimension):
                    tulip.dimension = int(i)
                for i in G.objects(s,tlp.link):
                    for key in G.objects(i,tlp.text):
                        tulip.link['text:' + str(key)] = str(list(G.objects(i,tlp.url))[0])
                    for key in G.objects(i,tlp.image):
                        tulip.link['image:' + str(key)] = str(list(G.objects(i,tlp.url))[0])
            if c4 != -1:
                _set_prop(tulip[c0][c1][c2][c3][c4], G, s)
            elif c3 != -1:
                _set_prop(tulip[c0][c1][c2][c3], G, s)
            elif c2 != -1:
                _set_prop(tulip[c0][c1][c2], G, s)
            elif c1 != -1:
                _set_prop(tulip[c0][c1], G, s)
            elif c0 != -1:
                _set_prop(tulip[c0], G, s)
            else:
                _set_prop(tulip, G, s)
    return tulip

def gen_html(tulip):
    """
    gen_html(Tulip:tulip)
    return str:html
    """
    print('Generating HTML')
    html = '''<!DOCTYPE html>
<html>
    <head>
        <title>'''
    if tulip.label != None:
        html += tulip.label
    html += '''</title>
    </head>
    <body style="font-family: sans-serif">
'''
    indent = ' '*4
    level = 1
    for tulip_grp in tulip:
        if tulip_grp.type['Table']:
            level += 1
            html += indent*level + '<table border="1" style="border-collapse: collapse">\n'
            if tulip_grp.label != None:
                html += indent*(level+1) + '<caption>' + tulip_grp.label.replace('\n','<br />') + '</caption>\n'
            # tulip.local prepared loop
            for col in range(len(tulip_grp)):
                row_span = None
                for row in range(len(tulip_grp[col])):
                    if row_span == None:
                        show_row = row
                        row_span = 0
                    row_span += 1
                    try:
                        tulip_grp[col][row].local['Hidden'] = True
                    except IndexError:
                        pass
                    #### 'last cell of span' conditions
                    try:
                        # Check that this is not RowSpanned cell and 
                        # it is not the last row (cell) of column
                        # (which not need to be equal with other column)
                        if (tulip_grp[col][row].style['RowSpanned'] == None or
                                              len(tulip_grp[col])-1 == row):
                            tulip_grp[col][show_row].local['RowSpan'] = row_span
                            tulip_grp[col][show_row].local['Hidden'] = None
                            row_span = None
                        # Check that this label is different from next row (cell)
                        # This condition have to separated check, even same consequence as above 
                        # (because [row+1] could produce error, which will be filtered out by above)
                        elif (tulip_grp[col][row].style['RowSpanned'] and 
                              tulip_grp[col][row].label != tulip_grp[col][row+1].label):
                            tulip_grp[col][show_row].local['RowSpan'] = row_span
                            tulip_grp[col][show_row].local['Hidden'] = None
                            row_span = None
                    except IndexError:
                        pass
            # HTML generated loop
            for row in range(len(tulip_grp[0])):
                level += 1
                html += indent*level + '<tr>\n'
                row_span = 0
                col_span = 0
                for col in range(len(tulip_grp)):
                    try:
                        if tulip_grp[col][row].local['Hidden']:
                            continue
                    except IndexError:
                        pass
                    try:
                        if tulip_grp[col][row].local['RowSpan'] != None:
                            row_span = tulip_grp[col][row].local['RowSpan']
                    except IndexError:
                        pass
                    try:
                        if tulip_grp[col][row].style['ColSpanned']:
                            col_span += 1
                            if (tulip_grp[col+1][row].style['ColSpanned'] and
                                tulip_grp[col+1][row].label == tulip_grp[col][row].label):
                                continue
                    except IndexError:
                        pass
                    level += 1
                    try:
                        if row_span > 1:
                            html += indent*level + ('<th rowspan="' + str(row_span) + '">\n' 
                                                    if tulip_grp[col][row].style['Identified'] 
                                                    else '<td rowspan="' + str(row_span) + '">\n')
                        elif col_span > 1:
                            html += indent*level + ('<th colspan="' + str(col_span) + '">\n' 
                                                    if tulip_grp[col][row].style['Identified'] 
                                                    else '<td colspan="' + str(col_span) + '">\n')
                        else:
                            html += indent*level + ('<th>\n' 
                                                    if tulip_grp[col][row].style['Identified'] 
                                                    else '<td>\n')
                    except IndexError:
                        html += indent*level + '<td>\n'
                    level += 1
                    # try first, except in case of irregular table (eg. rfc1942 example)
                    try:
                        if tulip_grp[col][row].label != None:
                            linked_text = tulip_grp[col][row].label
                        else:
                            linked_text = ''
                        for key, url in tulip_grp[col][row].link.items():
                            if key[:5] == 'text:':
                                linked_text = linked_text.replace(key[5:], '<a href="' + url + '">' + key[5:] + '</a>')
                            elif key[:6] == 'image:':
                                linked_text += '<a href="' + url + '"><img src="' + key[6:] + '"></a>'
                        if linked_text != '':
                            html += indent*level + linked_text.replace('\n','<br />') + '\n'
                        ### point of recursion
                        html += _html_list_recursion(tulip_grp[col][row], level)
                    except IndexError:
                        pass
                    level -= 1
                    try:
                        html += indent*level + ('</th>\n' 
                                                if tulip_grp[col][row].style['Identified'] 
                                                else '</td>\n')
                    except IndexError:
                        html += indent*level + '</td>\n'
                    level -= 1
                    col_span = 0
                html += indent*level + '</tr>\n'
                level -= 1
            html += indent*level + '</table>\n'
            level -= 1
        if tulip_grp.type['List']:
            level += 1        # caution: leave increment here, do not move into recursion
            html += _html_list_recursion(tulip_grp, level)
            level -= 1        # caution: leave decrement here, do not move into recursion
    html += indent*level + '</body>\n'
    html += '</html>'
    return html

def _html_list_recursion(tulip, level):
    indent = ' '*4
    html = ''
    # temporary use H4 for adding root list label
    if level == 1 and tulip.label != None:          # if the first call, not in recursion
        html += indent*level + '<h4>' + tulip.label.replace('\n','<br />') + '</h4>\n'
    header_added = False
    list_tag = 'ol' if tulip.style['Enumerated'] else 'ul'
    for i,node in enumerate(tulip):
        if not header_added:
            html += indent*level + '<' + list_tag + '>\n'
            level += 1
            header_added = True
        html += indent*level + '<li>\n'
        level += 1
        if node.label != None:
            linked_text = node.label
        else:
            linked_text = ''
        for key, url in node.link.items():
            if key[:5] == 'text:':
                linked_text = linked_text.replace(key[5:], '<a href="' + url + '">' + key[5:] + '</a>')
            elif key[:6] == 'image:':
                linked_text += '<a href="' + url + '"><img src="' + key[6:] + '"></a>'
        if linked_text != '':
            html += indent*level + linked_text.replace('\n','<br />') + '\n'
        ### point of recursion
        html += _html_list_recursion(tulip[i], level)
        level -= 1
        html += indent*level + '</li>\n'
    if header_added:
        level -= 1
        html += indent*level + '</' + list_tag + '>\n'
    return html

def dump_tulip(tulip, position=[], level=0):
    """
    dump_tulip(Tulip:tulip)
    return string:dump
    """
    dump = ''
    dump += dump_node(tulip, position, level)
    for i, elem in enumerate(tulip):
        position.append(i)
        level += 1
        dump += dump_tulip(elem, position, level)
        level -= 1
        position.pop()
    return dump

def dump_node(tulip, position=[], level=0):
    """
    dump_node(Tulip:tulip)
    return string:dump
    """
    indent = ' '*4
    dump = ''
    spacer = '\u2502' + ' '*(len(str(position))-1)
    end_spacer = '\u2514' + '\u2500'*(len(str(position))-1)
    dump += indent*level + str(position) + ' Type: ' + \
        ', '.join([ key for key,v in tulip.type.items() if v is not None ]) + '\n'
    if tulip.label != None:
        dump += indent*level + spacer + ' Label: ' + tulip.label + '\n'
    if any(tulip.style.values()):
        dump += indent*level + spacer + ' Style: ' + \
            ', '.join([ key for key,v in tulip.style.items() if v is not None ]) + '\n'
    if tulip.dimension != None:
        dump += indent*level + spacer + ' Dimension: ' + str(tulip.dimension) + '\n'
    if any(tulip.link.values()):
        dump += indent*level + spacer + ' Link: ' + str(tulip.link) + '\n'
    if any(tulip.local.values()):
        dump += indent*level + spacer + ' Local: ' + str(tulip.local) + '\n'
    if len(tulip) != 0:
        dump += indent*level + spacer + ' Number of Member: ' + str(len(tulip)) + '\n'
    dump = end_spacer.join(dump.rsplit(spacer, 1))
    return dump

def main():
    """
    TULIP
    ### available functions:
        str:text    = read_file(str:filename)
                      write_file(str:text, str:filename)
        str:text    = read_url(str:URL)
        Tulip:TULIP = parse_html(str:HTML)
        Tulip:TULIP = parse_article(str:Wikipedia_article_name)
        Tulip:TULIP = parse_rdf(str:RDF, str:RDF_format)
        str:Turtle  = gen_turtle(Tulip:TULIP)
                      add_elem(str:pre_filename, str:post_filename, str:RDF_format)
        str:HTML    = gen_html(Tulip:TULIP)
        str:text    = dump_tulip(Tulip:TULIP)
    ### HTML file -> TULIP Turtle file
        write_file(gen_turtle(parse_html(read_file(str:HTML_filename))), str:Turtle_filename)
    ### Wikipedia article name -> TULIP Turtle file
        write_file(gen_turtle(parse_article(str:Wikipedia_article_name)), str:Turtle_filename)
    ### TULIP RDF file -> HTML file
        write_file(gen_html(parse_rdf(read_file(str:RDF_filename),RDF_format)), str:HTML_filename)
    ### TULIP RDF file -> TULIP Turtle file, for testing
        write_file(gen_turtle(parse_rdf(read_file(str:RDF_filename),RDF_format)), str:Turtle_filename)
    """
    # test article
    test_article      = 'Chulalongkorn University'
    print('='*70)
    tulip = parse_article(test_article)
    turtle = gen_turtle(tulip)
    write_file(turtle, test_article.replace(' ','_')+'.pre.ttl')
    add_elem(test_article.replace(' ','_')+'.pre.ttl',test_article.replace(' ','_')+'.ttl', 'turtle')
    dump = dump_tulip(tulip)
    write_file(dump, test_article.replace(' ','_')+'.txt')
    print('-'*70)
    rdf_text = read_file(test_article.replace(' ','_')+'.ttl')
    tulip_rdf = parse_rdf(rdf_text, 'turtle')
    html = gen_html(tulip_rdf)
    write_file(html, test_article.replace(' ','_')+'.ttl.html')
    dump = dump_tulip(tulip_rdf)
    write_file(dump, test_article.replace(' ','_')+'.ttl.txt')

if __name__ == '__main__':
    main()
