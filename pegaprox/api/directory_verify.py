# -*- coding: utf-8 -*-
"""
Directory credential check for a trusted front end (MAKUS).

A web front end that keeps its own users and sessions (for example the MOAVI
screens) can let people sign in with their LDAP / Active Directory account
without holding a directory configuration of its own: LDAP is configured once
here (Settings > LDAP), and the front end asks this server whether a user name
and password are valid.

  GET  /api/directory/ldap/status   {enabled}
  POST /api/directory/ldap/verify   {username, password}
       -> 200 {valid: true, username, email, display_name, groups, role, user_dn}
       -> 200 {valid: false, error}

Rules:
  * API token only, and the token must carry admin.settings. A browser session
    is refused even for an admin: this is a server-to-server check, and an
    interactive caller has /api/auth/login.
  * No session is created and no local user row is provisioned or changed;
    the caller owns its users.
  * Attempts are rate limited per user name (and per source address), so the
    endpoint cannot be used to brute force directory passwords.
  * Every result is written to the audit log without the password.
"""

import logging

from flask import Blueprint, jsonify, request

from pegaprox.utils.auth import require_auth
from pegaprox.utils.audit import log_audit, get_client_ip
from pegaprox.utils.ldap import get_ldap_settings, ldap_authenticate
from pegaprox.utils.ssh import check_auth_action_rate_limit

bp = Blueprint('directory_verify', __name__)

_MAX_USERNAME = 256
_MAX_PASSWORD = 1024


def _token_only():
    session = getattr(request, 'session', None) or {}
    if not session.get('api_token'):
        return jsonify({'error': 'API token required'}), 403
    return None


@bp.route('/api/directory/ldap/status', methods=['GET'])
@require_auth(perms=['admin.settings'])
def directory_ldap_status():
    denied = _token_only()
    if denied:
        return denied
    cfg = get_ldap_settings()
    return jsonify({'enabled': bool(cfg.get('enabled') and cfg.get('server') and cfg.get('base_dn'))})


@bp.route('/api/directory/ldap/verify', methods=['POST'])
@require_auth(perms=['admin.settings'])
def directory_ldap_verify():
    denied = _token_only()
    if denied:
        return denied

    data = request.get_json(silent=True) or {}
    username = str(data.get('username') or '').strip()
    password = data.get('password')
    if not username or not isinstance(password, str) or not password:
        return jsonify({'error': 'username and password are required'}), 400
    if len(username) > _MAX_USERNAME or len(password) > _MAX_PASSWORD:
        return jsonify({'error': 'username or password too long'}), 400

    caller = request.session.get('user', '')
    remote = get_client_ip() or ''
    if not check_auth_action_rate_limit(f'dir_verify:{username.lower()}', max_attempts=10, window=300) \
            or not check_auth_action_rate_limit(f'dir_verify_ip:{remote}', max_attempts=300, window=300):
        log_audit(caller, 'directory.ldap_verify_limited', f'user={username[:64]}', remote)
        return jsonify({'error': 'Too many attempts, try again later'}), 429

    result = ldap_authenticate(username, password)
    if not result.get('success'):
        err = str(result.get('error') or 'Invalid credentials')
        # Wrong user and wrong password look the same to the caller.
        public = 'Invalid credentials' if ('Invalid LDAP credentials' in err or 'not found' in err.lower()) else err
        log_audit(caller, 'directory.ldap_verify_failed', f'user={username[:64]} reason={err[:120]}', remote)
        return jsonify({'valid': False, 'error': public})

    log_audit(caller, 'directory.ldap_verify_ok', f'user={username[:64]}', remote)
    return jsonify({
        'valid': True,
        'username': result.get('username') or username,
        'email': result.get('email') or '',
        'display_name': result.get('display_name') or '',
        'groups': list(result.get('groups') or []),
        'role': result.get('role') or '',
        'user_dn': result.get('user_dn') or '',
    })
