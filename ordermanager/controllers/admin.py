# -*- coding: utf-8 -*-
import logging

from pylons import request, response, session, tmpl_context as c
from pylons.controllers.util import abort, redirect_to
import ordermanager.lib.helpers as h
from ordermanager.lib.base import BaseController, render

import formencode
from formencode import htmlfill
from pylons.decorators import validate
from pylons.decorators.rest import restrict

import ordermanager.model as model
import ordermanager.model.meta as meta

log = logging.getLogger(__name__)


class AssignForm(formencode.Schema):
    allow_extra_fields = True
    filter_extra_fields = True


class AdminController(BaseController):

    # Все действия этого контроллера требуют админских прав!
    def __before__ (self):
        h.requirerights("admin")

    def index(self):
        return render(u'/admin/index.html')

    def autoassign(self):
        return render(u'/admin/assign.html')

    @validate(schema=AssignForm, form="autoassign")
    @restrict("POST")
    def saveautoassign(self):
        return render(u'/admin/assign.html')

    def fix (self):
        '''Исправляет права доступа для администратора и его группы (id равны единице!)'''
        admin = meta.Session.query(model.Person).get(1)
        admin.division = 1
        adiv = meta.Session.query(model.Person).get(1)
        adiv.owner = 1
        adiv.admin = True
        meta.Session.commit()
        session['flash'] = "Администратор исправлен!"
        session.save()
        redirect_to(h.url_for(controller="main", action="index"))
