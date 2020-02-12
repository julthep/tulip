# -*- coding: utf-8 -*-
"""
@author: julthep
"""

__author__ = "Julthep Nandakwang"
__version__ = "0.1.0"
__license__ = "LGPL-3.0"

import tulip as tlp

def main():
    """
    TULIP examples
    """
    # test table
    print('='*70)
    html = tlp.read_file('rfc1942_table.html')
    tulip = tlp.parse_html(html)
    turtle = tlp.gen_turtle(tulip)
    tlp.write_file(turtle, 'rfc1942_table.pre.ttl')
    tlp.add_elem('rfc1942_table.pre.ttl', 'rfc1942_table.ttl', 'turtle')
    dump = tlp.dump_tulip(tulip)
    tlp.write_file(dump, 'rfc1942_table.dump.txt')
    print('-'*70)
    rdf_text = tlp.read_file('rfc1942_table.ttl')
    tulip_rdf = tlp.parse_rdf(rdf_text,'turtle')
    html = tlp.gen_html(tulip_rdf)
    tlp.write_file(html, 'rfc1942_table.ttl.html')
    # test list
    print('='*70)
    tlp.write_file(tlp.gen_turtle(tlp.parse_html(tlp.read_file('rfc1866_list.html'))), 
                  'rfc1866_list.pre.ttl')
    tlp.write_file(tlp.dump_tulip(tlp.parse_html(tlp.read_file('rfc1866_list.html'))), 
                  'rfc1866_list.dump.txt')
    tlp.add_elem('rfc1866_list.pre.ttl','rfc1866_list.ttl', 'turtle')
    print('-'*70)
    tlp.write_file(tlp.gen_html(tlp.parse_rdf(tlp.read_file('rfc1866_list.ttl'),'turtle')), 
                  'rfc1866_list.ttl.html')
    # test article
    test_articles = ['Chulalongkorn University',
                     'List of C-family programming languages',
                     'Comparison of the AK-47 and M16']
    for test_article in test_articles:
        print('='*70)
        tulip = tlp.parse_article(test_article)
        turtle = tlp.gen_turtle(tulip)
        tlp.write_file(turtle, test_article.replace(' ','_')+'.pre.ttl')
        tlp.add_elem(test_article.replace(' ','_')+'.pre.ttl',
                     test_article.replace(' ','_')+'.ttl', 'turtle')
        dump = tlp.dump_tulip(tulip)
        tlp.write_file(dump, test_article.replace(' ','_')+'.dump.txt')
        print('-'*70)
        rdf_text = tlp.read_file(test_article.replace(' ','_')+'.ttl')
        tulip_rdf = tlp.parse_rdf(rdf_text, 'turtle')
        html = tlp.gen_html(tulip_rdf)
        tlp.write_file(html, test_article.replace(' ','_')+'.ttl.html')

if __name__ == '__main__':
    main()
