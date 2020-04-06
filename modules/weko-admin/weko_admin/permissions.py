# -*- coding: utf-8 -*-
#
# Copyright (C) 2020 National Institute of Informatics.
#
# WEKO3 is free software; you can redistribute it and/or
# modify it under the terms of the MIT License; see LICENSE file for more
# details.

"""WEKO3 module docstring."""

import pkg_resources
from flask_principal import ActionNeed

action_admin_access = ActionNeed('read-style-action')
action_admin_update = ActionNeed('update-style-action')
"""Define the action needed by the default permission factory."""

_action2need_map = {
    'read-style-action': action_admin_access,
    'update-style-action': action_admin_update,
}


def admin_permission_factory(action):
    """Default factory for creating a permission for an admin.

    It tries to load a :class:`invenio_access.permissions.DynamicPermission`
    instance if `invenio_access` is installed.
    Otherwise, it loads a :class:`flask_principal.Permission` instance.

    :param admin_view: Instance of administration view which is currently being
        protected.
    :returns: Permission instance.
    """
    action_class = _action2need_map[action]
    try:
        pkg_resources.get_distribution('invenio-access')
        from invenio_access.permissions import Permission as Permission
    except pkg_resources.DistributionNotFound:
        from flask_principal import Permission

    return Permission(action_class)
