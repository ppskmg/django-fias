#coding: utf-8
from __future__ import unicode_literals, absolute_import

import os
from django.db.models import Min
from fias.config import FIAS_TABLES
from fias.importer.source import *
from fias.importer.loader import TableLoader, TableUpdater
from fias.models import Status, Version


def get_tablelist(path, data_format):
    if path is None:
        latest_version = Version.objects.latest('dumpdate')
        url = getattr(latest_version, 'complete_{0}_url'.format(data_format))

        tablelist = RemoteArchiveTableList(path=url, version=latest_version)

    else:
        if os.path.isfile(path):
            tablelist = LocalArchiveTableList(path=path)

        elif os.path.isdir(path):
            tablelist = DirectoryTableList(path=path)

        elif path.startswith('http://') or path.startswith('https://') or path.startswith('//'):
            tablelist = RemoteArchiveTableList(path=path)

        else:
            raise TableListLoadingError('Path `{0}` is not valid table list source')

    return tablelist


def get_table_names(tables):
    return tables if tables is not None else FIAS_TABLES


def load_complete_data(path=None,
                       data_format='xml',
                       truncate=False, raw=False,
                       limit=10000, tables=None):


    tablelist = get_tablelist(path=path, data_format=data_format)

    for tbl in get_table_names(tables):
        for table in tablelist.tables[tbl]:
            if truncate:
                table.truncate()

            loader = TableLoader(limit=limit)
            loader.load(tablelist=tablelist, table=table)


def update_data(path=None, data_format='xml', limit=1000, tables=None):
    tablelist = get_tablelist(path=path, data_format=data_format)

    for tbl in get_table_names(tables):
        for table in tablelist.tables[tbl]:
            loader = TableUpdater(limit=limit)
            loader.load(tablelist=tablelist, table=table)


def auto_update_data(skip=False, data_format='xml', limit=1000):
    min_version = Status.objects.filter(table__in=get_table_names(None)).aggregate(Min('ver'))['ver__min']

    if min_version is not None:
        for version in Version.objects.filter(ver_gt=min_version).order_by('ver'):
            url = getattr(version, 'delta_{0}_url'.format(data_format))
            update_data(path=url, data_format=data_format, limit=limit)
    else:
        raise TableListLoadingError('Not available. Please import the data before updating')
