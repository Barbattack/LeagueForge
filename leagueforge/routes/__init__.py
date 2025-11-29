# -*- coding: utf-8 -*-
"""
LeagueForge - Routes Package
===========================

Flask Blueprints per organizzazione modulare delle routes.

Struttura:
- admin.py: Route admin (login, dashboard, import)
- achievements.py: Route achievement (catalogo, dettaglio)
- (public routes rimangono in app.py per ora)

Usage:
    from routes import register_blueprints
    register_blueprints(app)
"""

from flask import Blueprint


def register_blueprints(app):
    """
    Registra tutti i Blueprint sull'app Flask.

    Args:
        app: Flask application instance
    """
    from routes.admin import admin_bp
    from routes.achievements import achievements_bp

    app.register_blueprint(admin_bp, url_prefix='/admin')
    app.register_blueprint(achievements_bp)
