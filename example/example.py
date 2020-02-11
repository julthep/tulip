# -*- coding: utf-8 -*-
"""
@author: julthep
"""

__author__ = "Julthep Nandakwang"
__version__ = "0.1.0"
__license__ = "LGPL-3.0"

from tulip import (read_file, write_file,
                   parse_html, parse_article, parse_rdf,
                   gen_turtle, add_elem, gen_html, dump_tulip)

def main():
    """
    """
    # test table
    print('='*70)
    html = read_file('rfc1942_table.html')
    tulip = parse_html(html)
    turtle = gen_turtle(tulip)
    write_file(turtle, 'rfc1942_table.pre.ttl')
    add_elem('rfc1942_table.pre.ttl', 'rfc1942_table.ttl', 'turtle')
    dump = dump_tulip(tulip)
    write_file(dump, 'rfc1942_table.txt')
    print('-'*70)
    rdf_text = read_file('rfc1942_table.ttl')
    tulip_rdf = parse_rdf(rdf_text,'turtle')
    html = gen_html(tulip_rdf)
    write_file(html, 'rfc1942_table.ttl.html')
    dump = dump_tulip(tulip_rdf)
    write_file(dump, 'rfc1942_table.ttl.txt')
    # test list
    print('='*70)
    write_file(gen_turtle(parse_html(read_file('rfc1866_list.html'))), 'rfc1866_list.pre.ttl')
    write_file(dump_tulip(parse_html(read_file('rfc1866_list.html'))), 'rfc1866_list.txt')
    add_elem('rfc1866_list.pre.ttl','rfc1866_list.ttl', 'turtle')
    print('-'*70)
    write_file(gen_html(parse_rdf(read_file('rfc1866_list.ttl'),'turtle')), 'rfc1866_list.ttl.html')
    write_file(dump_tulip(parse_rdf(read_file('rfc1866_list.ttl'),'turtle')), 'rfc1866_list.ttl.txt')
    # test article
    test_article      = 'Chulalongkorn University'
    test_article      = 'List of C-family programming languages'
    test_article      = 'Comparison of the AK-47 and M16'
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
