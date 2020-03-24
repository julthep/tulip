"""
@author: julthep
"""

__author__ = "Julthep Nandakwang"
__version__ = "0.1.2"
__license__ = "LGPL-3.0"

import requests
import bs4
import json

from rdflib import Graph, Namespace, URIRef     #, Literal
from rdflib.collection import Collection
from rdflib.namespace import RDF    #, RDFS, FOAF
from urllib.parse import urljoin

session = requests.Session()

en_wiki_prefix    = 'http://en.wikipedia.org/wiki/'
en_wiki_indexphp  = 'http://en.wikipedia.org/w/index.php?title='
base_url          = ''      # initial set global base_url

class Tulip:
    def __init__(self, size):
        self.member = [ Tulip(0) for _ in range(size) ]
        self.type   = {'Group': None, 'Item':      None, 
                       'Page':  None, 'Paragraph': None, 
                       'Table': None, 'Column':    None, 'Row': None, 'Cell': None, 
                       'List':  None, 'ListItem':  None}
        self.label  = None
        self.style  = {'Emphasize': None, 'Enumerate':  None,
                       'ColMajor':  None, 'RowMajor':   None, 
                       'GrpSpan':   None, 'LineSpan':   None, 
                       'GrpSpanBr': None, 'LineSpanBr': None}
        self.dimension = None
        self.link = {}
        self.local = {'GrpSkip': None, 'LineSkip': None, 'GrpSpan': None, 'LineSpan': None}
    def __len__(self):
        return len(self.member)
    def __getitem__(self, index):
        return self.member[index]
    def __setitem__(self, index, value):
        self.member[index] = value
    def __delitem__(self, index):
        del self.member[index]

def recur_dict(object):
    return json.loads(
           json.dumps(object, default=lambda o: 
              getattr(o, '__dict__', str(o)), ensure_ascii=False))

class TulipJS:
    def __init__(self, d):
        self.member = [ TulipJS(d['member'][i]) for i in range(len(d['member']))]
        self.type   = {'Group': d['type']['Group'], 'Item':      d['type']['Item'], 
                       'Page':  d['type']['Page'],  'Paragraph': d['type']['Paragraph'], 
                       'Table': d['type']['Table'], 'Column':    d['type']['Column'], 
                       'Row':   d['type']['Row'],   'Cell':      d['type']['Cell'], 
                       'List':  d['type']['List'],  'ListItem':  d['type']['ListItem']}
        self.label  = d['label']
        self.style  = {'Emphasize': d['style']['Emphasize'], 'Enumerate':  d['style']['Enumerate'],
                       'ColMajor':  d['style']['ColMajor'],  'RowMajor':   d['style']['RowMajor'], 
                       'GrpSpan':   d['style']['GrpSpan'],   'LineSpan':   d['style']['LineSpan'], 
                       'GrpSpanBr': d['style']['GrpSpanBr'], 'LineSpanBr': d['style']['LineSpanBr']}
        self.dimension = d['dimension']
        self.link = d['link']
        # no need to load .local temporary working dict from JSON file, just initial them for HTML generation
        self.local = {'GrpSkip': None, 'LineSkip': None, 'GrpSpan': None, 'LineSpan': None}
    def __len__(self):
        return len(self.member)
    def __getitem__(self, index):
        return self.member[index]
    def __iter__(self):
        for item in self.member:
            yield item

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
    return s.text if s.ok else None

"""
 d8888b.  .d8b.  d8888b. .d8888. d88888b         db   db d888888b .88b  d88. db      
 88  `8D d8' `8b 88  `8D 88'  YP 88'             88   88 `~~88~~' 88'YbdP`88 88      
 88oodD' 88ooo88 88oobY' `8bo.   88ooooo         88ooo88    88    88  88  88 88      
 88~~~   88~~~88 88`8b     `Y8b. 88~~~~~         88~~~88    88    88  88  88 88      
 88      88   88 88 `88. db   8D 88.             88   88    88    88  88  88 88booo. 
 88      YP   YP 88   YD `8888Y' Y88888P C88888D YP   YP    YP    YP  YP  YP Y88888P 
"""

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
    # in case 'article' includes any parameters such as 'oldid=' or 'printable='
    if article.find('&') == -1:
        bso = bs4.BeautifulSoup(read_url(en_wiki_prefix + article.replace(" ","_")), "html.parser")
    else:
        bso = bs4.BeautifulSoup(read_url(en_wiki_indexphp + article.replace(" ","_")), "html.parser")
    # decompose: remove unneeded elements
    for tag in bso.find_all('script'):
        tag.decompose()
    for tag in bso.find_all('style'):
        tag.decompose()
    for tag in bso.find_all('div', class_=['navbox', 'suggestions']):
        tag.decompose()
    # div:id:mw-navigation
    #     mw-head
    #         p-personal, left-navigation, right-navigation, ul:class:menu
    #     mw-panel
    #         p-navigation, p-interaction, p-tb, p-wikibase-otherprojects, p-coll-print_export, p-lang
    #         div:class:portal, div:class:body
    # div:id:footer
    #     ul:id:footer-info, ul:id:footer-places ul:id:footer-icons
    for tag in bso.find_all('div', id=['visual-history-container', 'mw-page-base', 'mw-head-base',
                                       'mw-data-after-content', 'mw-head', 'p-navigation', 'p-interaction',
                                       'footer', 'mwe-popups-svg']):
        tag.decompose()
    for tag in bso.find_all('span', class_=['mw-cite-backlink', 'mw-editsection', 'tocnumber']):
        tag.decompose()
    # "coordinates" on the top right of each page usually redundant with article content
    for tag in bso.find_all('span', id=['coordinates']):
        tag.decompose()
    # better keep style="display:none" for further check its need
    for tag in bso.find_all('table', class_=['navbox', 'mbox-small', 'plainlinks', 'sistersitebox']):
        tag.decompose()
    for tag in bso.find_all('sup', class_=['reference', 'noprint']):
        tag.decompose()
    # unwrap: remove some tags that have problem with data structure, but keep their children
    for tag in bso.find_all('div', class_=None):   # all 'div' with no 'class', i.g. 'div' for 'style' purpose
        tag.unwrap()
    for tag in bso.find_all('div', class_=['plainlist', 'hlist']):   # 'hlist-separated'
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
                tulip[tulip_idx][col].type['Column'] = True                 # optional, no need in process
                tulip[tulip_idx][col].style['Enumerate'] = True            # optional, clarify for table->list conversion
            max_dim = 2
            # generate table properties
            tulip[tulip_idx].type['Table'] = True
            tulip[tulip_idx].style['Enumerate'] = True            # optional, clarify for table->list conversion
            tulip[tulip_idx].style['ColMajor'] = True            # optional, clarify for col->row-major transposition
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
                        src_list_items.style['Enumerate'] = (None, True)[i_list.name == 'ol']
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
                            tulip[tulip_idx][col_idx+cspan][row_idx+rspan].style['Emphasize'] = src_header
                            tulip[tulip_idx][col_idx+cspan][row_idx+rspan].style['Enumerate'] = src_list_items.style['Enumerate']
                            tulip[tulip_idx][col_idx+cspan][row_idx+rspan].style['GrpSpan'] = src_col_span
                            tulip[tulip_idx][col_idx+cspan][row_idx+rspan].style['LineSpan'] = src_row_span
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
                tulip[idx].style['Enumerate'] = (None, True)[pass_tag.name == 'ol']
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

"""
  d888b  d88888b d8b   db         d888888b db    db d8888b. d888888b db      d88888b 
 88' Y8b 88'     888o  88         `~~88~~' 88    88 88  `8D `~~88~~' 88      88'     
 88      88ooooo 88V8o 88            88    88    88 88oobY'    88    88      88ooooo 
 88  ooo 88~~~~~ 88 V8o88            88    88    88 88`8b      88    88      88~~~~~ 
 88. ~8~ 88.     88  V888            88    88b  d88 88 `88.    88    88booo. 88.     
  Y888P  Y88888P VP   V8P C88888D    YP    ~Y8888P' 88   YD    YP    Y88888P Y88888P 
"""

def gen_turtle(tulip):
    """
    gen_turtle(Tulip:tulip)
    return str:Turtle
    """
    print('Generating Turtle')
    indent = ' '*4
    # dummy header for Wikipedia page derived resources
    tulip_label_fn = tulip.label.replace(' ','_')
    turtle = '''@prefix rdf: <http://www.w3.org/1999/02/22-rdf-syntax-ns#> .
@prefix rdfs: <http://www.w3.org/2000/01/rdf-schema#> .
@prefix owl: <http://www.w3.org/2002/07/owl#> .
@prefix prov: <http://www.w3.org/ns/prov#> .
@prefix foaf: <http://xmlns.com/foaf/0.1/> .
@prefix wikipedia: <http://en.wikipedia.org/wiki/> .
@prefix dbpedia: <http://dbpedia.org/resource/> .
@prefix tlp: <http://purl.org/tulip/ns#> .
@prefix tlpedia: <http://tlpedia.org/resource/> .

<http://tlpedia.org/resource/''' + tulip_label_fn + '''>
    owl:sameAs <http://dbpedia.org/resource/''' + tulip_label_fn + '''> ;
    prov:wasDerivedFrom <http://en.wikipedia.org/wiki/''' + tulip_label_fn + '''?oldid=> ;
    foaf:isPrimaryTopicOf <http://en.wikipedia.org/wiki/''' + tulip_label_fn + '''> ;
    foaf:name "''' + tulip.label + '''" ;
    tlp:indexList ( 0 ) ;
    rdfs:label "''' + tulip.label + '''" ;
    rdf:type tlp:Page ;
'''
    elem_pred_added = False
    for i in range(len(tulip)):
        level = 0
        index_list = ''
        if tulip[i].type['Table']:
            if tulip[i].member != [] or tulip[i].label != None:
                level += 1
                if not elem_pred_added:
                    turtle += indent*(level*2-1) + 'tlp:member\n'
                    elem_pred_added = True
                turtle += indent*(level*2) + '[\n'
                turtle += indent*(level*2+1) + 'tlp:index ' + str(i+1) + ' ;\n'
                index_list_i = index_list + ' ' + str(i+1)
                turtle += indent*(level*2+1) + 'tlp:indexList (' + index_list_i + ' 0 ) ;\n'
                turtle += indent*(level*2+1) + 'rdf:type tlp:Table ;\n'
                label = tulip[i].label
                if label != None:
                    if label.find('\n') != -1 or label.find('"') != -1:
                        turtle += indent*(level*2+1) + 'rdfs:label """' + label + '""" ;\n'
                    else:
                        turtle += indent*(level*2+1) + 'rdfs:label "' + label + '" ;\n'
                for key in [ key for key,v in tulip[i].style.items() if v is not None ]:
                    turtle += indent*(level*2+1) + 'tlp:style tlp:' + key + ' ;\n'
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
                        index_list_j = index_list_i + ' ' + str(j+1)
                        turtle += indent*(level*2+1) + 'tlp:indexList (' + index_list_j + ' 0 ) ;\n'
                        turtle += indent*(level*2+1) + 'rdf:type tlp:Column ;\n'
                        if label != None:
                            if label.find('\n') != -1 or label.find('"') != -1:
                                turtle += indent*(level*2+1) + 'rdfs:label """' + label + '""" ;\n'
                            else:
                                turtle += indent*(level*2+1) + 'rdfs:label "' + label + '" ;\n'
                        for key in [ key for key,v in tulip[i][j].style.items() if v is not None ]:
                            turtle += indent*(level*2+1) + 'tlp:style tlp:' + key + ' ;\n'
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
                                index_list_k = index_list_j + ' ' + str(k+1)
                                turtle += indent*(level*2+1) + 'tlp:indexList (' + index_list_k + ' 0 ) ;\n'
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
                                    ### point of recursion
                                    turtle, level, elem_pred_added_l = _turtle_list_recursion(turtle, tulip[i][j][k], l, index_list_k, level, elem_pred_added_l)
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
            ### point of recursion
            turtle, level, elem_pred_added = _turtle_list_recursion(turtle, tulip, i, index_list, level, elem_pred_added)
        else:
            pass            # TO DO: handle later
    turtle = turtle[:-3] + '\n'
    turtle += '.'
    return turtle

def _turtle_list_recursion(turtle, tulip, idx, index_list, level=0, elem_pred_added=False):
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
        if tulip[idx].style['Enumerate'] != None:
            turtle += indent*(level*2+1) + 'tlp:style tlp:Enumerate ;\n'
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

def add_elem(pre_file, post_file, format):
    """
    add_elem(str:pre_filename, str:post_filename, str:post_file_format)
    """
    print('Updating', pre_file, 'with tlp:element to', post_file)
    g = Graph()
    g.parse(pre_file, format='turtle')      # Pre file always in Turtle format
    g.update('''PREFIX rdf: <http://www.w3.org/1999/02/22-rdf-syntax-ns#>
        PREFIX tlp: <http://purl.org/tulip/ns#>
        INSERT {
            ?s tlp:element ?b .
        }
        WHERE {
            ?s rdf:type tlp:Page .
            ?s tlp:member+ ?b . 
        }''')
    g.serialize(destination=post_file, format=format)   # Post file could be in any supported format

def ttl2nt(turtle_file, ntriples_file):
    """
    ttl2nt(str:Turtle filename, str:Ntriples filename)
    """
    print('Reserializing Turtle', turtle_file, 'to N-Triples', ntriples_file)
    g = Graph()
    g.parse(turtle_file, format='turtle')
    g.serialize(destination=ntriples_file, format='ntriples')
    # for testing purpose, re-serialize ntriples back to turtle
    print('Test reserializing N-Triples', ntriples_file, 'back to Turtle', ntriples_file+'.ttl')
    g = Graph()
    g.parse(ntriples_file, format='ntriples')
    g.serialize(destination=ntriples_file+'.ttl', format='turtle')

"""
 d8888b.  .d8b.  d8888b. .d8888. d88888b         d8888b. d8888b. d88888b 
 88  `8D d8' `8b 88  `8D 88'  YP 88'             88  `8D 88  `8D 88'     
 88oodD' 88ooo88 88oobY' `8bo.   88ooooo         88oobY' 88   88 88ooo   
 88~~~   88~~~88 88`8b     `Y8b. 88~~~~~         88`8b   88   88 88~~~   
 88      88   88 88 `88. db   8D 88.             88 `88. 88  .8D 88      
 88      YP   YP 88   YD `8888Y' Y88888P C88888D 88   YD Y8888D' YP      
"""

def parse_rdf(rdf_str, format):
    """
    parse_rdf(str:RDF text, str:RDF serialization format)
    return Tulip:tulip
    """
    print('Parsing RDF in', format, 'format')
    tlp_prefix = 'http://purl.org/tulip/ns#'
    tlp     = Namespace(tlp_prefix)
    G = Graph()
    G.parse(data=rdf_str, format=format)
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

def tulip2json(tulip):
    return json.dumps(recur_dict(tulip), ensure_ascii=False)
def json2tulip(json_str):
    return TulipJS(json.loads(json_str))

"""
  d888b  d88888b d8b   db         db   db d888888b .88b  d88. db      
 88' Y8b 88'     888o  88         88   88 `~~88~~' 88'YbdP`88 88      
 88      88ooooo 88V8o 88         88ooo88    88    88  88  88 88      
 88  ooo 88~~~~~ 88 V8o88         88~~~88    88    88  88  88 88      
 88. ~8~ 88.     88  V888         88   88    88    88  88  88 88booo. 
  Y888P  Y88888P VP   V8P C88888D YP   YP    YP    YP  YP  YP Y88888P 
"""

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
    <h1>'''
    if tulip.label != None:
        html += tulip.label
    html += '''</h1>
'''
    indent = str_repeat(' ', 2)
    level = 1
    for tulip_grp in tulip:
        if tulip_grp.type['Table']:
            level += 1
            html += _html_table_recursion(tulip_grp, level)
            level -= 1
        if tulip_grp.type['List']:
            level += 1        # caution: leave increment here, do not move into recursion
            html += _html_list_recursion(tulip_grp, level)
            level -= 1        # caution: leave decrement here, do not move into recursion
    html += str_repeat(indent, level) + '</body>\n'
    html += '</html>'
    return html

def str_repeat(str, n):
    """Repeat string for n times 
    (workaround for Python string multiplication not yet support in Transcrypt
    to avoid using JavaScript str.repeat() to keep Python source compatible)
    
    Arguments:
        str {string} -- string to repeat
        n {int} -- number of repeat
    """
    repeat = ''
    for _ in range(n): repeat += str
    return repeat

def _html_table_recursion(tulip, level):
    indent = str_repeat(' ', 2)
    html = ''
    html += str_repeat(indent, level) + '<table border="1" style="border-collapse: collapse">\n'
    if tulip.label != None:
        html += str_repeat(indent, level+1) + '<caption><strong>' + tulip.label.replace('\n','<br />') + '</strong></caption>\n'
    ##### tulip.local prepared loop
    # collect max_row for irregular table of list-converted table
    max_row = 0
    for col in range(len(tulip)):
        row_span = None
        row_len = len(tulip.member[col])
        if row_len > max_row: max_row = row_len
        for row in range(row_len):
            if row_span == None:
                show_row = row
                row_span = 0
            row_span += 1
            try:
                tulip[col][row].local['LineSkip'] = True
            except IndexError:
                pass
            #### 'last cell of span' conditions
            try:
                # Check that this is not LineSpan cell and 
                # it is not the last row (cell) of column
                # (which not need to be equal with other column)
                if (tulip[col][row].style['LineSpan'] == None or
                                        len(tulip[col])-1 == row):
                    tulip[col][show_row].local['LineSpan'] = row_span
                    tulip[col][show_row].local['LineSkip'] = None
                    row_span = None
                # Check that this label is different from next row (cell)
                # This condition have to separated check, even same consequence as above 
                # (because [row+1] could produce error, which will be filtered out by above)
                elif (tulip[col][row].style['LineSpan'] and 
                        tulip[col][row].label != tulip[col][row+1].label):
                    tulip[col][show_row].local['LineSpan'] = row_span
                    tulip[col][show_row].local['LineSkip'] = None
                    row_span = None
            except IndexError:
                pass
    ##### HTML generated loop
    # use max_row for irregular table or from list-converted table
    for row in range(max_row):
        level += 1
        html += str_repeat(indent, level) + '<tr>\n'
        row_span = 0
        col_span = 0
        for col in range(len(tulip)):
            try:
                if tulip[col][row].local['LineSkip']:
                    continue
            except IndexError:
                pass
            try:
                if tulip[col][row].local['LineSpan'] != None:
                    row_span = tulip[col][row].local['LineSpan']
            except IndexError:
                pass
            try:
                if tulip[col][row].style['GrpSpan']:
                    col_span += 1
                    if (tulip[col+1][row].style['GrpSpan'] and
                        tulip[col+1][row].label == tulip[col][row].label):
                        continue
            except IndexError:
                pass
            level += 1
            try:
                if row_span > 1:
                    html += str_repeat(indent, level) + ('<th rowspan="' + str(row_span) + '">\n' 
                                            if tulip[col][row].style['Emphasize'] 
                                            else '<td rowspan="' + str(row_span) + '">\n')
                elif col_span > 1:
                    html += str_repeat(indent, level) + ('<th colspan="' + str(col_span) + '">\n' 
                                            if tulip[col][row].style['Emphasize'] 
                                            else '<td colspan="' + str(col_span) + '">\n')
                else:
                    html += str_repeat(indent, level) + ('<th>\n' 
                                            if tulip[col][row].style['Emphasize'] 
                                            else '<td>\n')
            except IndexError:
                html += str_repeat(indent, level) + '<td>\n'
            level += 1
            # try first, except in case of irregular table (eg. rfc1942 example)
            try:
                if tulip[col][row].label != None:
                    linked_text = tulip[col][row].label
                else:
                    linked_text = ''
                for key, url in tulip[col][row].link.items():
                    if key[:5] == 'text:':
                        linked_text = linked_text.replace(key[5:], '<a href="' + url + '">' + key[5:] + '</a>')
                    elif key[:6] == 'image:':
                        linked_text += '<a href="' + url + '"><img src="' + key[6:] + '"></a>'
                if linked_text != '':
                    html += str_repeat(indent, level) + linked_text.replace('\n','<br />') + '\n'
                ### point of recursion
                html += _html_list_recursion(tulip[col][row], level)
            except IndexError:
                pass
            level -= 1
            try:
                html += str_repeat(indent, level) + ('</th>\n' 
                                        if tulip[col][row].style['Emphasize'] 
                                        else '</td>\n')
            except IndexError:
                html += str_repeat(indent, level) + '</td>\n'
            level -= 1
            col_span = 0
        html += str_repeat(indent, level) + '</tr>\n'
        level -= 1
    html += str_repeat(indent, level) + '</table>\n'
    return html

def _html_list_recursion(tulip, level):
    indent = str_repeat(' ', 2)
    html = ''
    # temporary use <strong> for adding root list label
    if level == 2 and tulip.label != None:          # if the first call, not in recursion
        html += str_repeat(indent, level) + '<strong>' + tulip.label.replace('\n','<br />') + '</strong>\n'
    header_added = False
    list_tag = 'ol' if tulip.style['Enumerate'] else 'ul'
    for i,node in enumerate(tulip):
        if not header_added:
            html += str_repeat(indent, level) + '<' + list_tag + '>\n'
            level += 1
            header_added = True
        html += str_repeat(indent, level) + '<li>\n'
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
            html += str_repeat(indent, level) + ('<strong>' + linked_text.replace('\n','<br />') + '</strong>'
                                                 if node.style['Emphasize']
                                                 else linked_text.replace('\n','<br />')) + '\n'
        ### point of recursion
        html += _html_list_recursion(tulip[i], level)
        level -= 1
        html += str_repeat(indent, level) + '</li>\n'
    if header_added:
        level -= 1
        html += str_repeat(indent, level) + '</' + list_tag + '>\n'
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
                      add_elem(str:pre_filename, str:post_filename, str:post_file_format)
        str:HTML    = gen_html(Tulip:TULIP)
        str:text    = dump_tulip(Tulip:TULIP)
                      ttl2nt(str:Turtle_filename, str:NTriples_filename)
        dict:tulip  = recur_dict(Tulip:tulip)
        str:JSON    = tulip2json(Tulip:tulip)
        Tulip:tulip = TulipJS(dict:tulip)
        Tulip:tulip = json2tulip(str:JSON)
    ### HTML file -> TULIP Turtle file
        write_file(gen_turtle(parse_html(read_file(str:HTML_filename))), str:Turtle_filename)
    ### Wikipedia article name -> TULIP Turtle file
        write_file(gen_turtle(parse_article(str:Wikipedia_article_name)), str:Turtle_filename)
    ### TULIP RDF file -> HTML file
        write_file(gen_html(parse_rdf(read_file(str:RDF_filename),RDF_format)), str:HTML_filename)
    ### TULIP RDF file -> TULIP Turtle file, for testing
        write_file(gen_turtle(parse_rdf(read_file(str:RDF_filename),RDF_format)), str:Turtle_filename)
    """
    from_file = True   # for dataset consume testing: 'True'=from file or 'False'=from web
    tlpedia_prefix = 'http://tlpedia.org/resource/'
    ########## test table
    print(str_repeat('=', 40), 'create dataset')
    html = read_file('rfc1942_table.html')
    tulip = parse_html(html)
    turtle = gen_turtle(tulip)
    write_file(turtle, 'rfc1942_table.pre.ttl')
    add_elem('rfc1942_table.pre.ttl', 'rfc1942_table.ttl', 'turtle')
    add_elem('rfc1942_table.pre.ttl', 'rfc1942_table.nt', 'ntriples')  # for testing
    ttl2nt('rfc1942_table.ttl','rfc1942_table.ttl.nt')  # for checking
    dump = dump_tulip(tulip)
    write_file(dump, 'rfc1942_table.txt')
    print(str_repeat('-', 40), 'consume dataset')
    rdf_str = read_file('rfc1942_table.ttl') if from_file else read_url(tlpedia_prefix + 'rfc1942_table.ttl')
    tulip_obj = parse_rdf(rdf_str,'turtle')
    tulip_json = tulip2json(tulip_obj)
    write_file(tulip_json, 'rfc1942_table.json')
    tulip_json2 = read_file('rfc1942_table.json') if from_file else read_url(tlpedia_prefix + 'rfc1942_table.json')
    tulip_obj2 = json2tulip(tulip_json2)
    html = gen_html(tulip_obj2)
    write_file(html, 'rfc1942_table.ttl.html')
    dump = dump_tulip(tulip_obj2)
    write_file(dump, 'rfc1942_table.ttl.txt')
    ########## test list
    print(str_repeat('=', 40), 'create dataset')
    write_file(gen_turtle(parse_html(read_file('rfc1866_list.html'))), 'rfc1866_list.pre.ttl')
    write_file(dump_tulip(parse_html(read_file('rfc1866_list.html'))), 'rfc1866_list.txt')
    add_elem('rfc1866_list.pre.ttl','rfc1866_list.ttl', 'turtle')
    add_elem('rfc1866_list.pre.ttl','rfc1866_list.nt', 'ntriples')  # for testing
    ttl2nt('rfc1866_list.ttl','rfc1866_list.ttl.nt')  # for checking
    print(str_repeat('-', 40), 'consume dataset')
    if from_file:
        write_file(tulip2json(parse_rdf(read_file('rfc1866_list.ttl'),'turtle')), 'rfc1866_list.json')
        write_file(gen_html(json2tulip(read_file('rfc1866_list.json'))), 'rfc1866_list.ttl.html')
        write_file(dump_tulip(json2tulip(tulip2json(parse_rdf(read_file('rfc1866_list.ttl'),'turtle')))), 'rfc1866_list.ttl.txt')
    else:
        write_file(tulip2json(parse_rdf(read_url(tlpedia_prefix+'rfc1866_list.ttl'),'turtle')), 'rfc1866_list.json')
        write_file(gen_html(json2tulip(read_url(tlpedia_prefix+'rfc1866_list.json'))), 'rfc1866_list.ttl.html')
        write_file(dump_tulip(json2tulip(tulip2json(parse_rdf(read_url(tlpedia_prefix+'rfc1866_list.ttl'),'turtle')))), 'rfc1866_list.ttl.txt')
    ########## test article
    test_articles = ['Chulalongkorn University',
                     'User:Julthep']
    for test_article in test_articles:
        test_article_fn = test_article.replace(' ','_').replace(':','_')
        print(str_repeat('=', 40), 'create dataset')
        tulip = parse_article(test_article)
        turtle = gen_turtle(tulip)
        write_file(turtle, test_article_fn+'.pre.ttl')
        add_elem(test_article_fn+'.pre.ttl',test_article_fn+'.ttl', 'turtle')
        add_elem(test_article_fn+'.pre.ttl',test_article_fn+'.nt', 'ntriples')  # for testing
        ttl2nt(test_article_fn+'.ttl',test_article_fn+'.ttl.nt') # for checking
        dump = dump_tulip(tulip)
        write_file(dump, test_article_fn+'.txt')
        print(str_repeat('-', 40), 'consume dataset')
        rdf_str = (read_file(test_article_fn+'.ttl') if from_file else 
                   read_url(tlpedia_prefix+test_article_fn+'.ttl'))
        tulip_obj = parse_rdf(rdf_str, 'turtle')
        tulip_json = tulip2json(tulip_obj)
        write_file(tulip_json, test_article_fn+'.json')
        tulip_json2 = (read_file(test_article_fn+'.json') if from_file else 
                       read_url(tlpedia_prefix+test_article_fn+'.json'))
        tulip_obj2 = json2tulip(tulip_json2)
        html_str = gen_html(tulip_obj2)
        write_file(html_str, test_article_fn+'.ttl.html')
        dump_str = dump_tulip(tulip_obj2)
        write_file(dump_str, test_article_fn+'.ttl.txt')

if __name__ == '__main__':
    main()
