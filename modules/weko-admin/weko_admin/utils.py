# -*- coding: utf-8 -*-
#
# This file is part of WEKO3.
# Copyright (C) 2017 National Institute of Informatics.
#
# WEKO3 is free software; you can redistribute it
# and/or modify it under the terms of the GNU General Public License as
# published by the Free Software Foundation; either version 2 of the
# License, or (at your option) any later version.
#
# WEKO3 is distributed in the hope that it will be
# useful, but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the GNU
# General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with WEKO3; if not, write to the
# Free Software Foundation, Inc., 59 Temple Place, Suite 330, Boston,
# MA 02111-1307, USA.

"""Utilities for convert response json."""
import csv
import zipfile
from io import BytesIO, StringIO

import redis
import requests
from flask import current_app, session
from flask_babelex import lazy_gettext as _
from invenio_accounts.models import Role, userrole
from invenio_db import db
from invenio_i18n.ext import current_i18n
from invenio_i18n.views import set_lang
from invenio_mail.admin import MailSettingView
from simplekv.memory.redisstore import RedisStore
from sqlalchemy import func
from weko_authors.models import Authors
from weko_records.api import ItemsMetadata
import requests

from . import config
from .models import AdminLangSettings, ApiCertificate, FeedbackMailSetting, \
    SearchManagement, StatisticTarget, StatisticUnit


def get_response_json(result_list, n_lst):
    """Get a response json.

    :param result_list:
    :param n_lst:
    :return: result
    """
    result = {}
    if isinstance(result_list, list):
        newlst = []
        for rlst in result_list:
            adr_lst = rlst.get('addresses')
            if isinstance(adr_lst, list):
                for alst in adr_lst:
                    alst['start_ip_address'] = alst['start_ip_address'].split(
                        '.')
                    alst['finish_ip_address'] = alst[
                        'finish_ip_address'].split('.')
            newlst.append(rlst.dumps())
        result.update(dict(site_license=newlst))
        del result_list

    if n_lst:
        item_type = {}
        allow = []
        deny = []
        for lst in n_lst:
            tmp = []
            tmp.append({'id': str(lst.id), 'name': lst.name})
            if lst.has_site_license:
                allow.extend(tmp)
            else:
                deny.extend(tmp)

        item_type['deny'] = deny or []
        item_type['allow'] = allow or []
        result['item_type'] = item_type

    return result


def allowed_file(filename):
    """Allowed file."""
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in config.LOGO_ALLOWED_EXTENSIONS


def get_search_setting():
    """Get search setting from DB.

    :return: Setting data by Json
    """
    res = SearchManagement.get()

    if res:
        db_obj = res.search_setting_all
        # current_app.logger.debug(db_str)
        # if 'False' in db_str:
        #     db_str.replace('False','false')
        # if 'True' in db_str:
        #     db_str.replace('True', 'true')
        # db_str = json.dumps(db_str)
        # db_obj= json.loads(db_str)

        return db_obj
    else:
        return config.WEKO_ADMIN_MANAGEMENT_OPTIONS


def get_admin_lang_setting():
    """Convert language list to json.

    :return:
    """
    try:
        active_lang_list = AdminLangSettings.get_active_language()
    except Exception as e:
        return str(e)
    return active_lang_list


def update_admin_lang_setting(admin_lang_settings):
    """Update language to admin_lang_settings table.

    :param admin_lang_settings: input data to update language into database
    """
    try:
        for admin_lang in admin_lang_settings:
            AdminLangSettings.update_lang(admin_lang.get('lang_code'),
                                          admin_lang.get('lang_name'),
                                          admin_lang.get('is_registered'),
                                          admin_lang.get('sequence'))
    except Exception as e:
        return str(e)
    return 'success'


def get_selected_language():
    """Get selected language."""
    result = {
        'lang': '',
        'selected': '',
        'refresh': False
    }
    registered_languages = AdminLangSettings.get_registered_language()
    if not registered_languages:
        return result

    result['lang'] = registered_languages
    default_language = registered_languages[0].get('lang_code')
    result['refresh'] = is_refresh(default_language)
    result['selected'] = get_current_language(default_language)

    return result


def get_current_language(default_language):
    """Get current language.

    :param default_language:
    :return: selected language
    """
    if "selected_language" in session:
        session['selected_language'] = current_i18n.language
        return session['selected_language']
    else:
        session['selected_language'] = default_language
        set_lang(default_language)
        return session['selected_language']


def set_default_language():
    """Set the default language.

    In case user opens the web for the first time,
    set default language base on Admin language setting
    """
    if "selected_language" not in session:
        registered_languages = AdminLangSettings.get_registered_language()
        if registered_languages:
            default_language = registered_languages[0].get('lang_code')
            set_lang(default_language)


def is_refresh(default_language):
    """Is refresh.

    :param default_language:
    :return:
    """
    if "selected_language" not in session:
        if default_language != current_i18n.language:
            return True
    return False


def get_api_certification_type():
    """Get API certification type.

    :return: list of supported certification type
    """
    try:
        all_api = ApiCertificate.select_all()
        result = []
        for api in all_api:
            data = dict()
            data['api_code'] = api.get('api_code')
            data['api_name'] = api.get('api_name')
            result.append(data)
        return result
    except Exception as e:
        return str(e)


def get_current_api_certification(api_code):
    """Get current API certification.

    :param api_code: API code
    :return: API certification data if exist
    """
    results = {
        'api_code': api_code,
        'api_name': '',
        'cert_data': {}
    }
    try:
        cert_data = ApiCertificate.select_by_api_code(api_code)
        results['api_name'] = cert_data.get('api_name')
        results['cert_data'] = cert_data.get('cert_data')

    except Exception as e:
        return str(e)

    return results


def save_api_certification(api_code, cert_data):
    """Save API certification to DB base on api code.

    :param api_code: API code
    :param cert_data: certification data
    :return: dict
    {
        'results': true // true if save successfully
        'error':''
    }
    """
    result = {
        'results': '',
        'error': ''
    }
    try:
        if cert_data:
            if ApiCertificate.select_by_api_code(api_code) is not None:
                """ Update database in case api_code exited """
                result['results'] = ApiCertificate.update_cert_data(api_code,
                                                                    cert_data)
            else:
                result['error'] = _(
                    "Input type is invalid. Please check again.")
        else:
            result['error'] = _(
                "Account information is invalid. Please check again.")
    except Exception as e:
        result['error'] = str(e)

    return result


def create_crossref_url(pid):
    """Create Crossref api url.

    :param pid:
    :return Crossref api url:
    """
    if not pid:
        raise ValueError('PID is required')
    url = config.WEKO_ADMIN_CROSSREF_API_URL + config.WEKO_ADMIN_ENDPOINT + \
          '?pid=' + pid + config.WEKO_ADMIN_TEST_DOI + config.WEKO_ADMIN_FORMAT
    return url


def validate_certification(cert_data):
    """Validate certification.

    :param cert_data: Certification data
    :return: true if certification is valid, false otherwise
    """
    response = requests.get(create_crossref_url(cert_data))
    return config.WEKO_ADMIN_VALIDATION_MESSAGE not in \
           str(vars(response).get('_content', None))


def get_initial_stats_report():
    """Get initial statistic report.

    :return: list unit and list target
    """
    result = {
        'target': '',
    }

    targets = StatisticTarget.get_all_stats_report_target()
    match_target = list()
    for target in targets:
        temp_target = dict()
        temp_target['id'] = target['id']
        temp_target['data'] = target['data']
        match_target.append(temp_target)
    result['target'] = match_target

    return result


def get_unit_stats_report(target_id):
    """Get unit statistic report."""
    result = {
        'unit': '',
    }

    target = StatisticTarget.get_target_by_id(target_id)
    target_units = target.target_unit
    units = StatisticUnit.get_all_stats_report_unit()

    list_unit = list()
    for unit in units:
        try:
            if target_units.index(unit['id']) is not None:
                list_unit.append(unit)
        except Exception:
            pass
    result['unit'] = list_unit
    return result


def get_user_report_data():
    """Get user report data from db and modify."""
    role_counts = []
    try:
        role_counts = db.session.query(Role.name,
                                       func.count(userrole.c.role_id)) \
            .outerjoin(userrole) \
            .group_by(Role.id).all()
    except Exception as e:
        current_app.logger.error('Could not retrieve user report data: ')
        current_app.logger.error(e)
        return {}

    role_counts = [dict(role_name=name, count=count)
                   for name, count in role_counts]
    results = {'all': role_counts}
    total_users = sum([x['count'] for x in role_counts])

    # Total registered users
    results['all'].append({'role_name': _('Registered Users'),
                           'count': total_users})
    return results


def package_reports(all_stats, year, month):
    """Package the .tsv files into one zip file."""
    tsv_files = []
    zip_stream = BytesIO()
    year = str(year)
    month = str(month)
    try:  # TODO: Make this into one loop, no need for two
        for stats_type, stats in all_stats.items():
            file_name = current_app.config['WEKO_ADMIN_REPORT_FILE_NAMES'].get(
                stats_type, '_')
            file_name = 'logReport_' + file_name + year + '-' + month + '.tsv'
            tsv_files.append({
                'file_name': file_name,
                'stream': make_stats_tsv(stats, stats_type, year, month)})

        # Dynamically create zip from StringIO data into BytesIO
        report_zip = zipfile.ZipFile(zip_stream, 'w')
        for tsv_file in tsv_files:
            report_zip.writestr(tsv_file['file_name'],
                                tsv_file['stream'].getvalue())
        report_zip.close()
    except Exception as e:
        current_app.logger.error('Unexpected error: ', e)
        raise
    return zip_stream


def make_stats_tsv(raw_stats, file_type, year, month):
    """Make TSV report file for stats."""
    header_row = current_app.config['WEKO_ADMIN_REPORT_HEADERS'].get(file_type)
    sub_header_row = current_app.config['WEKO_ADMIN_REPORT_SUB_HEADERS'].get(
        file_type)
    tsv_output = StringIO()

    writer = csv.writer(tsv_output, delimiter='\t',
                        lineterminator="\n")
    writer.writerows([[header_row],
                      [_('Aggregation Month'), year + '-' + month],
                      [''], [header_row]])

    if file_type in ['billing_file_download', 'billing_file_preview']:
        col_dict_key = file_type.split('_', 1)[1]
        cols = current_app.config['WEKO_ADMIN_REPORT_COLS'].get(col_dict_key,
                                                                [])
        cols[3:1] = raw_stats['all_groups']  # Insert group columns
    else:
        cols = current_app.config['WEKO_ADMIN_REPORT_COLS'].get(file_type, [])
    writer.writerow(cols)

    # Special cases:
    # Write total for per index views
    if file_type == 'index_access':
        writer.writerow([_('Total Detail Views'), raw_stats['total']])

    elif file_type in ['billing_file_download', 'billing_file_preview']:
        write_report_tsv_rows(writer, raw_stats['all'], file_type,
                              raw_stats['all_groups'])  # Pass all groups
    elif file_type == 'site_access':
        write_report_tsv_rows(writer,
                              raw_stats['site_license'],
                              file_type,
                              _('Site license member'))
        write_report_tsv_rows(writer,
                              raw_stats['other'],
                              file_type,
                              _('Other than site license'))
    else:
        write_report_tsv_rows(writer, raw_stats['all'], file_type)

    # Write open access stats
    if sub_header_row is not None:
        writer.writerows([[''], [sub_header_row]])
        if 'open_access' in raw_stats:
            writer.writerow(cols)
            write_report_tsv_rows(writer, raw_stats['open_access'])
        elif 'institution_name' in raw_stats:
            writer.writerows([[_('Institution Name')] + cols])
            write_report_tsv_rows(writer,
                                  raw_stats['institution_name'],
                                  file_type)
    return tsv_output


def write_report_tsv_rows(writer, records, file_type=None, other_info=None):
    """Write tsv rows for stats."""
    from weko_items_ui.utils import get_user_information
    if isinstance(records, dict):
        records = list(records.values())
    for record in records:
        if file_type is None or \
            file_type == 'file_download' or \
            file_type == 'file_preview':
            writer.writerow([record['file_key'], record['index_list'],
                             record['total'], record['no_login'],
                             record['login'], record['site_license'],
                             record['admin'], record['reg']])

        elif file_type in ['billing_file_download', 'billing_file_preview']:
            row = [record['file_key'], record['index_list'],
                   record['total'], record['no_login'],
                   record['login'], record['site_license'],
                   record['admin'], record['reg']]
            group_counts = []
            for group_name in other_info:  # Add group counts in
                group_counts.append(record['group_counts'].get(group_name, 0))
            row[3:1] = group_counts
            writer.writerow(row)

        elif file_type == 'index_access':
            writer.writerow(
                [record['index_name'], record['view_count']])
        elif file_type == 'search_count':
            writer.writerow([record['search_key'], record['count']])
        elif file_type == 'user_roles':
            writer.writerow([record['role_name'], record['count']])
        elif file_type == 'detail_view':
            item_metadata_json = ItemsMetadata. \
                get_record(record['record_id'])
            writer.writerow([
                item_metadata_json['title'], record['index_names'],
                record['total_all'], record['total_not_login']])
        elif file_type == 'file_using_per_user':
            user_email = ''
            user_name = 'Guest'
            user_id = int(record['cur_user_id'])
            if user_id > 0:
                user_info = get_user_information(user_id)
                user_email = user_info['email']
                user_name = user_info['username']
            writer.writerow([
                user_email, user_name,
                record['total_download'], record['total_preview']])
        elif file_type == 'top_page_access':
            writer.writerow([record['host'], record['ip'],
                             record['count']])
        elif file_type == 'site_access':
            if record:
                if other_info:
                    writer.writerow([other_info, record['top_view'],
                                     record['search'],
                                     record['record_view'],
                                     record['file_download'],
                                     record['file_preview']])
                else:
                    writer.writerow([record['name'], record['top_view'],
                                     record['search'],
                                     record['record_view'],
                                     record['file_download'],
                                     record['file_preview']])


def reset_redis_cache(cache_key, value):
    """Delete and then reset a cache value to Redis."""
    try:
        datastore = RedisStore(redis.StrictRedis.from_url(
            current_app.config['CACHE_REDIS_URL']))
        datastore.delete(cache_key)
        datastore.put(cache_key, value.encode('utf-8'))
    except Exception as e:
        current_app.logger.error('Could not reset redis value', e)
        raise


def get_redis_cache(cache_key):
    """Check and then retrieve the value of a Redis cache key."""
    try:
        datastore = RedisStore(redis.StrictRedis.from_url(
            current_app.config['CACHE_REDIS_URL']))
        if datastore.redis.exists(cache_key):
            return datastore.get(cache_key).decode('utf-8')
    except Exception as e:
        current_app.logger.error('Could get value for ' + cache_key, e)
    return None


def get_feed_back_email_setting():
    """Get list feedback email setting.

    Returns:
        dictionary -- feedback email setting

    """
    result = {
        'data': '',
        'is_sending_feedback': '',
        'error': ''
    }
    setting = FeedbackMailSetting.get_all_feedback_email_setting()
    if len(setting) == 0:
        return result
    list_author_id = setting[0].account_author.split(',')
    result['is_sending_feedback'] = setting[0].is_sending_feedback
    list_data = list()
    for author_id in list_author_id:
        email = Authors.get_first_email_by_id(author_id)
        new_data = dict()
        new_data['author_id'] = author_id
        new_data['email'] = email
        list_data.append(new_data)
    result['data'] = list_data
    return result


def update_feedback_email_setting(data, is_sending_feedback):
    """Update feedback email setting.

    Arguments:
        data {list} -- data list
        is_sending_feedback {bool} -- is sending feedback

    Returns:
        dict -- error message

    """
    result = {
        'error': ''
    }
    update_result = False
    if not data:
        update_result = FeedbackMailSetting.delete()
        return handle_update_message(
            result,
            update_result
        )
    error_message = validate_feedback_mail_setting(data)
    if error_message:
        result['error'] = error_message
        return result
    current_setting = FeedbackMailSetting.get_all_feedback_email_setting()
    if len(current_setting) == 0:
        update_result = FeedbackMailSetting.create(
            convert_feedback_email_data_to_string(data),
            is_sending_feedback
        )
    else:
        update_result = FeedbackMailSetting.update(
            convert_feedback_email_data_to_string(data),
            is_sending_feedback
        )
    return handle_update_message(
        result,
        update_result
    )


def convert_feedback_email_data_to_string(data, keyword='author_id'):
    """Convert feedback email data to string.

    Arguments:
        data {list} -- Data list

    Keyword Arguments:
        keyword {str} -- search keyword (default: {'author_id'})

    Returns:
        string -- list as string

    """
    if not isinstance(data, list):
        return None
    result = ''
    for item in data:
        if item.get(keyword):
            result = result + ',' + item.get(keyword)
    return result[1:]


def handle_update_message(result, success):
    """Check query result and return message.

    Arguments:
        result {dict} -- message
        success {bool} -- query result

    Returns:
        dict -- message

    """
    if not success:
        result['error'] = _('Cannot update Feedback email settings.')
    return result


def validate_feedback_mail_setting(data):
    """Validate duplicate email and author id.

    Arguments:
        data {list} -- data list

    Returns:
        string -- error message

    """
    error_message = None
    list_author = convert_feedback_email_data_to_string(
        data
    ).split(',')
    list_email = convert_feedback_email_data_to_string(
        data,
        'email'
    ).split(',')
    new_list = list()
    for item in list_author:
        if len(new_list) == 0 or item not in new_list:
            new_list.append(item)
        else:
            error_message = _('Author is duplicated.')
            return error_message
    new_list = list()
    for item in list_email:
        if len(new_list) == 0 or item not in new_list:
            new_list.append(item)
        else:
            error_message = _('Duplicate Email Addresses.')
            return error_message
    return error_message


def get_statistic_email_data(data):
    """ Convert statistic data to email data.

    Arguments:
        data {list} -- list statistic data

    Returns:
        list -- email data

    """
    list_result = list()
    for item in data:
        new_data = dict()
        new_data['title'] = ''
        new_data['url'] = ''
        new_data['detail_view'] = 0
        new_data['file_download'] = 0

        list_result.append(new_data)
    return list_result


def get_list_statistic_email():
    """Get list statistic email from setting.

    Returns:
        list -- list email

    """
    setting = FeedbackMailSetting.get_all_feedback_email_setting()
    is_send = setting[0].is_sending_feedback
    if not is_send:
        return None

    email_setting = setting[0].json.get('email')
    authors = get_feed_back_email_setting
    list_email = list()
    for auth in authors:
        list_email.append(auth.get('email'))

    for mail in email_setting:
        if mail in list_email:
            list_email.remove(mail)
    return list_email


def fill_email_data(template, data):
    return None


def send_mail(receiver, body, subject):
    """Send mail to receiver.

    Arguments:
        receiver {string} -- receiver mail address
        body {string} -- mail content
        subject {string} -- mail subject

    Returns:
        boolean -- True if send success
    """
    # FAKE DATA:
    receiver = 'weko-ope@nii.ac.jp',
    body = 'This is a test mail.'
    subject = 'Test statistic mail'
    # ========
    rf = {
        'subject': subject,
        'body': body,
        'recipient': receiver
    }
    return MailSettingView.send_statistic_mail(rf)


def count_file_view_per_item(record_id):
    """Count number of view of items

    Arguments:
        record_id {string} -- id of item to count
    """
    root_url = request.url_root
    url = root_url + '/api/stats/' + record_id
    time = str(datetime.now().month - 1) + '-' + (datetime.now().year)
    data = {
        "date": time
    }
    response = requests.post(url, data=data)
    return response["total"]


def count_file_download_per_item(bucket_id, file_key):
    """Count number of view of items

    Arguments:
        record_id {string} -- id of item to count
    """
    root_url = request.url_root
    url = root_url + '/api/stats/' + bucket_id + '/' + file_key
    time = str(datetime.now().month - 1) + '-' + (datetime.now().year)
    data = {
        "date": time
    }
    response = requests.post(url, data=data)
    return response["total"]
