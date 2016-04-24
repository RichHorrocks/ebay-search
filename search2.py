#!/usr/bin/env python

import os
import sys
import pprint
import locale

import isodate
import ebaysdk
from ebaysdk.finding import Connection as finding
from ebaysdk.exception import ConnectionError

from flask import Flask
from flask import render_template

FILE_SEARCH = "./search.txt"
FILE_HTML = "./templates/list.html"

LINK_FLAG = '<tr><b><font color="red">LOOK AT ME!</font></b>'
LINK_BUTTONS = """<tr><td><button type="button">Remove!</button></td>
                      <td><button type="button">Flag!</button></td>"""
LINK_HTML= """<td align="right" style="width:60px">%s%s</td>
              <td align="right" style="width:120px">%s</td>
              <td align="right" style="width:15px">%s</td>
              <td><a href="%s" target="_blank">%s</a></td></tr>"""

HTML_HEADER = '</br>Search string: <b>"%s"</b> ------ Price: %s</br>'

# The attributes of the table.
TABLE_OPEN = '<table>'
TABLE_CLOSE = '</table>'

# Instantiate our Flask class.
app = Flask(__name__)


# Decide which URL will trigger everything...
@app.route('/')
def ebay_serve_page():
    return render_template("list.html")


# Check whether we're parsing a comment.
def ebay_is_comment(line):
    return line[:1] == '#'
       

# Write our constructed HTML strings.
def ebay_write_html(items_to_write):
    with open(FILE_HTML, 'w') as f:
        for item in items_to_write:
            f.write("%s" % item)


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
        if ebay_is_comment(item):
            continue

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

        items_html_list.append(HTML_HEADER % (item_name, item_price))
        items_html_list.append(TABLE_OPEN)

        for i in range(mydict_count):
            if mydict_count == 1:
                item_dict = mydict["searchResult"]["item"]
            else:
                item_dict = mydict["searchResult"]["item"][i]
         
            total_price = float(item_dict["sellingStatus"]
                                         ["currentPrice"]
                                         ["value"])

            # Some items will have free postage, so the below field won't be 
            # populated.
            free_postage = True
            if "shippingServiceCost" in item_dict["shippingInfo"]:
                free_postage = False
                total_price += float(item_dict["shippingInfo"]
                                              ["shippingServiceCost"]
                                              ["value"])

            if total_price < float(item_price):
                # Get the date in a human-readable form.
                date = isodate.parse_duration(item_dict["sellingStatus"]
                                                       ["timeLeft"]
                                                       ["value"]);

                html_link = LINK_BUTTONS + LINK_HTML
                items_html_list.append(html_link % 
                                       (locale.currency(total_price),
                                        "f" if free_postage else "",
                                        date,
                                        item_dict["sellingStatus"]
                                                 ["bidCount"]["value"],
                                        item_dict["viewItemURL"]
                                                 ["value"],
                                        item_dict["title"]
                                                 ["value"].encode('utf-8')))

        items_html_list.append(TABLE_CLOSE)

    ebay_write_html(items_html_list)


# Run!
if __name__ == '__main__':
    locale.setlocale(locale.LC_ALL, '')
    ebay_find_wanted_items()

    app.debug = True
    app.run(port = 5001, use_reloader=False)