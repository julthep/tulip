# -*- coding: utf-8 -*-
"""
@author: julthep
"""

__author__ = "Julthep Nandakwang"
__version__ = "0.1.1"
__license__ = "LGPL-3.0"

import tulip as tlp

def main():
    """
    TULIP examples
    """
    from_file = True   # for dataset consume testing: 'True'=from file or 'False'=from web
    tlpedia_prefix = 'http://tlpedia.org/resource/'
    # test table
    print('='*40, 'create dataset')
    html = tlp.read_file('rfc1942_table.html')
    tulip = tlp.parse_html(html)
    turtle = tlp.gen_turtle(tulip)
    tlp.write_file(turtle, 'rfc1942_table.pre.ttl')
    tlp.add_elem('rfc1942_table.pre.ttl', 'rfc1942_table.ttl', 'turtle')
    dump = tlp.dump_tulip(tulip)
    tlp.write_file(dump, 'rfc1942_table.dump.txt')
    print('-'*40, 'consume dataset')
    rdf_str = tlp.read_file('rfc1942_table.ttl') if from_file else tlp.read_url(tlpedia_prefix + 'rfc1942_table.ttl')
    tulip_obj = tlp.parse_rdf(rdf_str,'turtle')
    tulip_json = tlp.tulip2json(tulip_obj)
    tlp.write_file(tulip_json, 'rfc1942_table.json')
    tulip_json2 = tlp.read_file('rfc1942_table.json') if from_file else tlp.read_url(tlpedia_prefix + 'rfc1942_table.json')
    tulip_obj2 = tlp.json2tulip(tulip_json2)
    html = tlp.gen_html(tulip_obj2)
    tlp.write_file(html, 'rfc1942_table.ttl.html')
    # test list
    print('='*40, 'create dataset')
    tlp.write_file(tlp.gen_turtle(tlp.parse_html(tlp.read_file('rfc1866_list.html'))), 
                  'rfc1866_list.pre.ttl')
    tlp.write_file(tlp.dump_tulip(tlp.parse_html(tlp.read_file('rfc1866_list.html'))), 
                  'rfc1866_list.dump.txt')
    tlp.add_elem('rfc1866_list.pre.ttl','rfc1866_list.ttl', 'turtle')
    print('-'*40, 'consume dataset')
    if from_file:
        tlp.write_file(tlp.tulip2json(tlp.parse_rdf(tlp.read_file('rfc1866_list.ttl'),'turtle')), 
                      'rfc1866_list.json')
        tlp.write_file(tlp.gen_html(tlp.json2tulip(tlp.read_file('rfc1866_list.json'))), 
                      'rfc1866_list.ttl.html')
    else:
        tlp.write_file(tlp.tulip2json(tlp.parse_rdf(tlp.read_url(tlpedia_prefix+'rfc1866_list.ttl'),'turtle')), 
                      'rfc1866_list.json')
        tlp.write_file(tlp.gen_html(tlp.json2tulip(tlp.read_url(tlpedia_prefix+'rfc1866_list.json'))), 
                      'rfc1866_list.ttl.html')
    # test article
    test_articles = ['Chulalongkorn University',
                     'List of C-family programming languages',
                     'Comparison of the AK-47 and M16',
                     'Saturn Award for Best Science Fiction Film',
                     'Simulated reality in fiction',
                     'User:Julthep']
    for test_article in test_articles:
        test_article_fn = test_article.replace(' ','_').replace(':','_')
        print('='*40, 'create dataset')
        tulip = tlp.parse_article(test_article)
        turtle = tlp.gen_turtle(tulip)
        tlp.write_file(turtle, test_article_fn+'.pre.ttl')
        tlp.add_elem(test_article_fn+'.pre.ttl', test_article_fn+'.ttl', 'turtle')
        dump = tlp.dump_tulip(tulip)
        tlp.write_file(dump, test_article_fn+'.dump.txt')
        print('-'*40, 'consume dataset')
        rdf_str = (tlp.read_file(test_article_fn+'.ttl') if from_file else 
                   tlp.read_url(tlpedia_prefix+test_article_fn+'.ttl'))
        tulip_obj = tlp.parse_rdf(rdf_str, 'turtle')
        tulip_json = tlp.tulip2json(tulip_obj)
        tlp.write_file(tulip_json, test_article_fn+'.json')
        tulip_json2 = (tlp.read_file(test_article_fn+'.json') if from_file else 
                       tlp.read_url(tlpedia_prefix+test_article_fn+'.json'))
        tulip_obj2 = tlp.json2tulip(tulip_json2)
        html_str = tlp.gen_html(tulip_obj2)
        tlp.write_file(html_str, test_article_fn+'.ttl.html')

if __name__ == '__main__':
    main()
