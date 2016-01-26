#!/usr/bin/env python

import os
import sys
import pprint

import ebaysdk
from ebaysdk.finding import Connection as finding
from ebaysdk.exception import ConnectionError

from flask import Flask
from flask import render_template

FILE_SEARCH = "search.txt"
FILE_HTML = "templates/list.html"

HTML_LINK = '<a href="%s" target="_blank">%s</a> %s %s</br>'
HTML_HEADER = '</br><b>Search string: %s</b></br>'


# Instantiate our Flask class.
app = Flask(__name__)


# Decide which URL will trigger everything...
@app.route('/')
def ebay_serve_page():
    return render_template("list.html")


# Write our constructed HTML strings.
def ebay_write_html(items_to_write):
    with open(FILE_HTML, 'a+') as f:
        for item in items_to_write:
            f.write("%s" % item.encode('utf-8'))


# Open the text file containing what to search eBay for.
def ebay_get_wanted_items():
    with open(FILE_SEARCH, 'r') as f:
        items = f.readlines()

    return items


def ebay_find_wanted_items():
    # No need to include our ID here; that gets grabbed from the YAML file.
    api = finding(siteid = 'EBAY-GB')

    # Get the search strings from our text file.
    # The amount we're willing to pay is: item.split(' ', 1)[0]
    # The string to search for is: item.split(' ', 1)[1]
    wanted_items = ebay_get_wanted_items()

    # List to hold the lines of html we're going to write to a file.
    items_html_list = []

    # Query eBay for each wanted item.
    for item in wanted_items:
        item_price = item.split(' ', 1)[0]
        item_name = item.split(' ', 1)[1]

        api.execute('findItemsAdvanced', {
            'keywords': item_name,
            'itemFilter': [ 
                {'name': 'ListingType',                 
                 'value': 'Auction'},
                {'name': 'LocatedIn',
                 'value': 'GB'},
                {'name': 'MaxPrice',
                 'value': item_price },
             ],
             'sortOrder': 'EndTimeSoonest',
        })

        # The results are returned as a dictionary.
        mydict = api.response_dict()
        mydict_count = int(mydict["searchResult"]["count"]["value"])        

        if mydict_count != 0:
            items_html_list.append(HTML_HEADER % item_name)

        for i in range(mydict_count):
            if mydict_count == 1:
                item_dict = mydict["searchResult"]["item"]
            else:
                item_dict = mydict["searchResult"]["item"][i]

            items_html_list.append(HTML_LINK % (item_dict["viewItemURL"]["value"],
                                                item_dict["title"]["value"],
                                                item_dict["sellingStatus"]["bidCount"]["value"],
                                                item_dict["sellingStatus"]["currentPrice"]["value"]))            

    ebay_write_html(items_html_list)


# Run!
if __name__ == '__main__':
    ebay_find_wanted_items()

    app.debug = True
    app.run(port = 5001, use_reloader=False)
