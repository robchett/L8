#!/usr/bin/env python

import json
import hashlib

import time
import datetime

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


def pretty_date(time=False):
    """
    Get a datetime object or a int() Epoch timestamp and return a
    pretty string like 'an hour ago', 'Yesterday', '3 months ago',
    'just now', etc
    """
    from datetime import datetime, timedelta
    now = datetime.now() - timedelta(hours=1)
    if isinstance(time, int):
        diff = now - datetime.fromtimestamp(time)
    elif isinstance(time, datetime):
        diff = now - time
    elif not time:
        diff = now - now
    second_diff = diff.seconds
    day_diff = diff.days

    if day_diff < 0:
        return ''

    if day_diff == 0:
        if second_diff < 10:
            return "just now"
        if second_diff < 60:
            return str(second_diff) + " seconds ago"
        if second_diff < 120:
            return "a minute ago"
        if second_diff < 3600:
            return str(second_diff / 60) + " minutes ago"
        if second_diff < 7200:
            return "an hour ago"
        if second_diff < 86400:
            return str(second_diff / 3600) + " hours ago"
    if day_diff == 1:
        return "Yesterday"
    if day_diff < 7:
        return str(day_diff) + " days ago"
    if day_diff < 31:
        return str(day_diff / 7) + " weeks ago"
    if day_diff < 365:
        return str(day_diff / 30) + " months ago"
    return str(day_diff / 365) + " years ago"

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
        #err_dict['timestamp'] = int(time.mktime(err_dict['time'].timetuple()))
        err_dict['ptime'] = pretty_date(err_dict['time'])
        json_errs.append(err_dict)

    return jsonify({'errors': json_errs,
                    'hash': hashlib.md5(str(json_errs)).hexdigest()})


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
