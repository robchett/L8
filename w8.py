#!/usr/bin/env python

"""
Copyright Ben Gosney 2014-2016
bengosney@googlemail.com

This program is free software: you can redistribute it and/or modify
it under the terms of the GNU General Public License as published by
the Free Software Foundation, either version 3 of the License, or
(at your option) any later version.

This program is distributed in the hope that it will be useful,
but WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
GNU General Public License for more details.

You should have received a copy of the GNU General Public License
along with this program.  If not, see <http://www.gnu.org/licenses/>.
"""

import json
import hashlib

import time
from datetime import datetime
from dateutil import relativedelta
from data.data import Data
from data.config import args
from flask import Flask, jsonify, url_for

app = Flask(__name__)


def list_routes():
    import urllib
    output = {}
    for rule in app.url_map.iter_rules():
        doc = app.view_functions[rule.endpoint].__doc__
        if rule.rule.startswith('/api/') and doc is not None:
            output[rule.rule] = doc.strip()

    return output


def _pretty_date_format(qty, quantifier):
    return "%d %s%s ago" % (qty, quantifier, "s" if qty > 1 else "") 


def pretty_date(obj_time=False):
    dt1 = datetime.fromtimestamp(time.time()) # 1973-11-29 22:33:09
    dt2 = datetime.fromtimestamp(obj_time) # 1977-06-07 23:44:50
    rd = relativedelta.relativedelta (dt1, dt2)

    if rd.years > 0:
        return _pretty_date_format(rd.years, "year")
    if rd.months > 0:    
        return _pretty_date_format(rd.months, "month")   
    if rd.days > 0:    
        return _pretty_date_format(rd.days, "day")    
    if rd.hours > 0:    
        return _pretty_date_format(rd.hours, "hour")  
    if rd.minutes > 0:    
        return _pretty_date_format(rd.minutes, "minute")  
    if rd.seconds > 0:    
        return _pretty_date_format(rd.seconds, "second") 
    return "just now"

base_path = '/api/v1.0/'


@app.route(base_path)
def api():
    """
    List the api calls
    """

    return jsonify({
        'success': True,
        'version': 1.0,
        'methods': list_routes(),
    })


@app.route(base_path + 'domain/list/')
def domains():
    """
    List the domains that have errors
    """
    errors_obj = Data(args)
    domains = errors_obj.domains()
    json_domains = []

    for d in domains:
        json_domains.append(d.__dict__)

    return jsonify({'domains': json_domains,
                    'hash': hashlib.md5(str(json_domains)).hexdigest()})


@app.route(base_path + 'domain/<string:host>/errors/')
@app.route(base_path + 'domain/<string:host>/errors/<int:mode>/')
def errors(host, mode=1):
    """
    List the errors for a domain
    """

    errors_obj = Data(args)
    errs = errors_obj.errors(host, mode)
    json_errs = []

    for e in errs:
        err_dict = e.__dict__
        err_dict['ptime'] = pretty_date(err_dict['time'])
        err_dict['iso_time'] = datetime.fromtimestamp(err_dict['time']).isoformat()
        json_errs.append(err_dict)

<<<<<<< HEAD
    return jsonify({'errors': json_errs,
                    'hash': hashlib.md5(str(json_errs)).hexdigest()})
=======
    return jsonify({'errors': json_errs, 'hash': hashlib.md5(str(json_errs)).hexdigest()})
>>>>>>> upstream/master


@app.route(base_path + 'levels/')
def error_levels():
    """
    List the error levels
    """

    errors_obj = Data(args)

    return jsonify({'levels': errors_obj.levels.keys})


@app.route(base_path + 'delete/<int:id>/')
@app.route(base_path + 'delete/group/<int:id>/', defaults={'group': True})
def delete_error(id, group=False):
    """
    Deletes an error based on ID
    """

    errors_obj = Data(args)
    try:
        error = errors_obj.get_error(id)
    except LookupError:
        return jsonify({'success': False})

    if group:
        errors_obj.delete_type(error)
    else:
        errors_obj.delete_entry(error)

    return jsonify({'success': True})


@app.route('/')
def template():
    return open('data/template.html').read(100000)

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0')
