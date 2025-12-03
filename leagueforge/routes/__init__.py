# -*- coding: utf-8 -*-
"""
LeagueForge - Routes Package
===========================

Flask Blueprints per organizzazione modulare delle routes.

Struttura:
- achievements.py: Route achievement (catalogo, dettaglio)
- (public routes rimangono in app.py per ora)
- (admin routes: to be implemented)

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
    from routes.achievements import achievements_bp

    app.register_blueprint(achievements_bp)

    # TODO: Admin panel to be re-implemented
    # from routes.admin import admin_bp
    # app.register_blueprint(admin_bp, url_prefix='/admin')
