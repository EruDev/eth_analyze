# _*_ encoding: utf-8 _*_

import datetime
import decimal
import json
from itertools import groupby
from django.http import HttpResponse
from django.db import connection
from django.shortcuts import render
from django.views.generic import View


class DecimalEncoder(json.JSONEncoder):
    def _iterencode(self, o, markers=None):
        if isinstance(o, decimal.Decimal):
            return (str(o) for o in [0])
        return super(DecimalEncoder, self)._iterencode(o, markers)


def query_names(request):
    """交易所名"""
    with connection.cursor() as cursor:
        sql = 'SELECT DISTINCT name from eth_exchange_address'
        cursor.execute(sql)
        row = cursor.fetchall()
    names = list()
    for idx, item in enumerate(row):
        names.append({
            'idx': idx,
            'name':  item[0]
        })
    return HttpResponse(json.dumps(names), content_type='application/json')


def exchange_rose(request):
    """涨幅"""
    d = dict()
    data = []
    name_list = request.GET.getlist('name', None)
    start = request.GET.get('start_time', None)
    end = request.GET.get('end_time', None)

    names = "','".join(name_list[0].split(','))
    s = datetime.datetime.strptime(start, '%Y%m%d%H')
    e = datetime.datetime.strptime(end, '%Y%m%d%H')
    counts = (e - s).days
    times_list = list()

    for i in range(1, counts+1):
        start_time = (s + datetime.timedelta(days=i)).strftime('%Y%m%d%H')
        times_list.append(start_time)
    times_tuple = tuple(times_list)

    if names != 'all':

        with connection.cursor() as cursor:
            sql = """SELECT addr.`name`, DATE_FORMAT(ex.`tag`, '%%Y%%m%%d%%H'), SUM(ex.`balance`) 
                    FROM `eth_exchange` ex 
                    INNER JOIN `eth_exchange_address` addr ON ex.`address` = addr.`address`
                    WHERE addr.`name` IN ('%s') and DATE_FORMAT(ex.`tag`, '%%Y%%m%%d%%H') IN %s
                    GROUP BY addr.`name`, DATE_FORMAT(ex.`tag`, '%%Y%%m%%d%%H')""" % (names, times_tuple)
            cursor.execute(sql)

            row = cursor.fetchall()
    else:
        with connection.cursor() as cursor:
            sql = """SELECT 'all'as name, DATE_FORMAT(ex.`tag`, '%%Y%%m%%d%%H'), SUM(ex.`balance`) 
                        FROM `eth_exchange` ex 
                        INNER JOIN `eth_exchange_address` addr ON ex.`address` = addr.`address`
                        WHERE DATE_FORMAT(ex.`tag`, '%%Y%%m%%d%%H') IN %s
                        GROUP BY 'all', DATE_FORMAT(ex.`tag`, '%%Y%%m%%d%%H')""" % (times_tuple,)
            cursor.execute(sql)

            row = cursor.fetchall()

    # 按照交易所名分组
    row_name = groupby(row, lambda x: x[0])

    # 分组处理数据
    for k, v in row_name:
            _list = list()
            for i in v:
                _list.append(i)

            for idx, item in enumerate(_list[1:]):
                if not item[0] in d.keys():
                    name = item[0]
                    detail = list()
                    pre_val = _list[idx][2]
                    grow_percent = float('%.3f' % ((item[2] - pre_val) / pre_val))
                    detail.append({
                        'tag': item[1],
                        'grow_percent': grow_percent * 100
                    })
                    d[name] = detail
                else:
                    name = item[0]
                    pre_val = _list[idx][2]
                    grow_percent = float('%.3f' % ((item[2] - pre_val) / pre_val))
                    d[name].append({
                        'tag': item[1],
                        'grow_percent': grow_percent * 100
                    })

    with connection.cursor() as cursor:
        sql2 = """SELECT DATE_FORMAT(fxh.`tag`, '%%Y%%m%%d%%H'), SUM(price_usd)
        FROM fxh_eth_price fxh
        WHERE DATE_FORMAT(fxh.`tag`, '%%Y%%m%%d%%H') IN %s
        GROUP BY DATE_FORMAT(fxh.`tag`, '%%Y%%m%%d%%H')
                """ % (times_tuple,)
        cursor.execute(sql2)
        eths = cursor.fetchall()

    eth = list()
    eth_dict = dict()
    for idx, item in enumerate(eths[1:]):
        pre = float(eths[idx][1])
        cur = float(item[1])
        grow_percent = float('%.3f' % ((cur - pre) / pre))
        eth.append({
            'tag': item[0],
            'grow_percent': grow_percent * 100
        })
    eth_dict['eth'] = eth
    data.append(d)
    data.append(eth_dict)

    return HttpResponse(json.dumps(data), content_type='application/json')


def exchange_balance(request):
    """余额"""
    d = dict()
    data = list()
    name_list = request.GET.getlist('name', None)
    start = request.GET.get('start_time', None)
    end = request.GET.get('end_time', None)

    names = "','".join(name_list[0].split(','))
    s = datetime.datetime.strptime(start, '%Y%m%d%H')
    e = datetime.datetime.strptime(end, '%Y%m%d%H')
    counts = (e - s).days
    times_list = list()

    for i in range(1, counts + 1):
        start_time = (s + datetime.timedelta(days=i)).strftime('%Y%m%d%H')
        times_list.append(start_time)
    times_tuple = tuple(times_list)

    if names != 'all':
        with connection.cursor() as cursor:
            sql = """SELECT addr.`name`, DATE_FORMAT(ex.`tag`, '%%Y%%m%%d%%H'), SUM(ex.`balance`) 
                    FROM `eth_exchange` ex 
                    INNER JOIN `eth_exchange_address` addr ON ex.`address` = addr.`address`
                    WHERE addr.`name` IN ('%s') and DATE_FORMAT(ex.`tag`, '%%Y%%m%%d%%H') IN %s
                    GROUP BY addr.`name`, DATE_FORMAT(ex.`tag`, '%%Y%%m%%d%%H')""" % (names, times_tuple,)
            cursor.execute(sql)

            row = cursor.fetchall()
    else:
        with connection.cursor() as cursor:
            sql = """SELECT 'all' as name, DATE_FORMAT(ex.`tag`, '%%Y%%m%%d%%H'), SUM(ex.`balance`) 
                        FROM `eth_exchange` ex 
                        INNER JOIN `eth_exchange_address` addr ON ex.`address` = addr.`address`
                        WHERE DATE_FORMAT(ex.`tag`, '%%Y%%m%%d%%H') IN %s
                        GROUP BY 'all', DATE_FORMAT(ex.`tag`, '%%Y%%m%%d%%H')""" % (times_tuple,)
            cursor.execute(sql)

            row = cursor.fetchall()
    row_name = groupby(row, lambda x: x[0])
    for k, v in row_name:
        _list = list()
        for i in v:
            _list.append(i)
        for idx, item in enumerate(_list):
            if not item[0] in d.keys():
                name = item[0]
                detail = list()
                detail.append({
                    'tag': item[1],
                    'balance': str(item[2])
                })
                d[name] = detail
            else:
                name = item[0]
                d[name].append({
                    'tag': item[1],
                    'balance': str(item[2])
                })

    with connection.cursor() as cursor:
        sql = """SELECT DATE_FORMAT(eth.`tag`,'%%Y%%m%%d%%H'), SUM(price_usd) 
                FROM fxh_eth_price eth
                WHERE DATE_FORMAT(eth.`tag`, '%%Y%%m%%d%%H') IN %s
                GROUP BY DATE_FORMAT(eth.`tag`, '%%Y%%m%%d%%H')
                """ % (times_tuple,)
        cursor.execute(sql)
        eths = cursor.fetchall()

    eth = list()
    eth_dict = dict()
    for idx, item in enumerate(eths[1:]):
        pre = float(eths[idx][1])
        cur = float(item[1])
        grow_percent = float('%.3f' % ((cur - pre) / pre))
        eth.append({
            'tag': item[0],
            'grow_percent': grow_percent * 100
        })
    eth_dict['eth'] = eth
    data.append(d)
    data.append(eth_dict)
    return HttpResponse(json.dumps(data), content_type='application/json')


class IndexView(View):
    def get(self, request):
        return render(request, 'index.html')


class BalanceView(View):
    def get(self, request):
        return render(request, 'balance.html')
