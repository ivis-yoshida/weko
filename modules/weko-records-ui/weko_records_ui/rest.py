# -*- coding: utf-8 -*-
#
# Copyright (C) 2020 National Institute of Informatics.
#
# WEKO3 is free software; you can redistribute it and/or
# modify it under the terms of the MIT License; see LICENSE file for more
# details.

"""Blueprint for schema rest."""

from flask import Blueprint, current_app, jsonify, make_response, request
from invenio_pidstore.errors import PIDInvalidAction
from invenio_pidstore.models import PersistentIdentifier
from invenio_records_rest.links import default_links_factory
from invenio_records_rest.utils import obj_or_import_string
from invenio_records_rest.views import \
    create_error_handlers as records_rest_error_handlers
from invenio_rest import ContentNegotiatedMethodView
from invenio_rest.views import create_api_errorhandler
from weko_deposit.api import WekoRecord
from weko_records.serializers import citeproc_v1


def create_error_handlers(blueprint):
    """Create error handlers on blueprint."""
    blueprint.errorhandler(PIDInvalidAction)(create_api_errorhandler(
        status=403, message='Invalid action'
    ))
    records_rest_error_handlers(blueprint)


def create_blueprint(endpoints):
    """Create Weko-Records-UI-Cites-REST blueprint.

    See: :data:`invenio_deposit.config.DEPOSIT_REST_ENDPOINTS`.

    :param endpoints: List of endpoints configuration.
    :returns: The configured blueprint.
    """
    blueprint = Blueprint(
        'weko_records_ui_cites_rest',
        __name__,
        url_prefix='',
    )

    create_error_handlers(blueprint)

    for endpoint, options in (endpoints or {}).items():

        if 'record_serializers' in options:
            serializers = options.get('record_serializers')
            serializers = {mime: obj_or_import_string(func)
                           for mime, func in serializers.items()}
        else:
            serializers = {}

        record_class = obj_or_import_string(options['record_class'])

        ctx = dict(
            read_permission_factory=obj_or_import_string(
                options.get('read_permission_factory_imp')
            ),
            record_class=record_class,
            links_factory=obj_or_import_string(
                options.get('links_factory_imp'), default=default_links_factory
            ),
            # pid_type=options.get('pid_type'),
            # pid_minter=options.get('pid_minter'),
            # pid_fetcher=options.get('pid_fetcher'),
            loaders={
                options.get('default_media_type'): lambda: request.get_json()},
            default_media_type=options.get('default_media_type'),
        )

        cites = WekoRecordsCitesResource.as_view(
            WekoRecordsCitesResource.view_name.format(endpoint),
            serializers=serializers,
            # pid_type=options['pid_type'],
            ctx=ctx,
            default_media_type=options.get('default_media_type'),
        )

        blueprint.add_url_rule(
            options.pop('cites_route'),
            view_func=cites,
            methods=['GET'],
        )

    return blueprint


class WekoRecordsCitesResource(ContentNegotiatedMethodView):
    """Schema files resource."""

    view_name = '{0}_cites'

    def __init__(self, serializers, ctx, *args, **kwargs):
        """Constructor."""
        super(WekoRecordsCitesResource, self).__init__(
            serializers,
            *args,
            **kwargs
        )
        for key, value in ctx.items():
            setattr(self, key, value)

    # @pass_record
    # @need_record_permission('read_permission_factory')
    def get(self, pid_value, **kwargs):
        """Render citation for record according to style and language."""
        style = request.values.get('style', 1)  # style or 'science'
        locale = request.values.get('locale', 2)
        try:
            pid = PersistentIdentifier.get('depid', pid_value)
            record = WekoRecord.get_record(pid.object_uuid)

            result = citeproc_v1.serialize(pid, record, style=style,
                                           locale=locale)
            return make_response(jsonify(result), 200)
        except Exception:
            current_app.logger.exception(
                'Citation formatting for record {0} failed.'.format(
                    str(record.id)))
            return make_response(jsonify("Not found"), 404)
