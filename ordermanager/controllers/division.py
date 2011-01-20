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
from pylons.decorators import jsonify

import ordermanager.model as model
import ordermanager.model.meta as meta

from sqlalchemy import func
from sqlalchemy.orm import join

from datetime import datetime, timedelta

log = logging.getLogger(__name__)

#### VALIDATION

# Этот валидатор проверяет название на уникальность
class UniqueDiv (formencode.FancyValidator):
    def _to_python(self, value, state):
         names = [name[0] for name in meta.Session.query(model.Division.title).all()]
         if value in names:
             raise formencode.Invalid(
                 u'Такое подразделение уже существует. Выберите другое название.',
                 value, state)
         return value

class NewDivisionForm(formencode.Schema):
    allow_extra_fields = True
    filter_extra_fields = True
    title = UniqueDiv(
        strip = True,
        not_empty=True,
        messages = {'empty': u"Введите название"}
    )
    address = formencode.validators.String(
        not_empty=True,
        messages = {'empty': u"Введите адрес"}
    )
    description = formencode.validators.String()
    email = formencode.validators.Email()
    phone = formencode.validators.String()


class EditDivisionForm(formencode.Schema):
    allow_extra_fields = True
    filter_extra_fields = True
    title = formencode.validators.String(
        strip = True,
        not_empty=True,
        messages = {'empty': u"Введите название"}
    )
    address = formencode.validators.String(
        not_empty=True,
        messages = {'empty': u"Введите адрес"}
    )
    description = formencode.validators.String()
    email = formencode.validators.Email()
    phone = formencode.validators.String()

class UserListForm(formencode.Schema):
    allow_extra_fields = True
    filter_extra_fields = True
    users = formencode.validators.String(if_missing=[])



class DivisionController(BaseController):

    def index(self):
        return redirect_to(h.url_for(action="list"))

    def list(self):
        qdiv = meta.Session.query(model.Division).filter_by(deleted=False).order_by(model.Division.title)
        c.paginator = h.paginate.Page(
            qdiv,
            page=int(request.params.get('page', 1)),
            items_per_page = 15,
        )
        c.divcount = qdiv.count()
        return render ("/divisions/list.html")

    def view(self, id=None):
        c.division = h.checkdiv(id)
        c.division.responsible = meta.Session.query(model.Person).filter_by(div_id=id).filter_by(responsible=True).all()
        c.division.chief = meta.Session.query(model.Person).filter_by(div_id=id).filter_by(chief=True).all()
        c.lastorders = meta.Session.query(model.Order).filter_by(cust_id=id).\
            order_by(model.sql.desc(model.Order.created))[:10]
        c.personnel = meta.Session.query(model.Person).filter_by(div_id=id).\
            filter_by(deleted=False).order_by(model.Person.surname).all()
        # Учёт количества сделанных заявок
        last = meta.Session.query(model.Person.id, func.count(model.Order.id)).\
            join(model.Order.performers).filter(model.Person.div_id==id).\
            group_by(model.Person.id)
        last30d = last.filter(model.Order.doneAt > datetime.now()-timedelta(30)).all()
        last1d = last.filter(model.Order.doneAt > datetime.now()-timedelta(1)).all()
        c.lastmonth = dict(last30d)
        c.lastday = dict(last1d)
        c.total = dict(last.all())
        return render("/divisions/view.html")

    def add(self):
        h.requirerights("admin")
        users = meta.Session.query(model.Person).all()
        c.users = []
        for i in users:
            c.users.append([i.id, h.name(i)])
        return render ("/divisions/add.html")

    @validate(schema=NewDivisionForm, form="add")
    @restrict('POST')
    def create(self):
        h.requirerights("admin")
        div = model.Division()
        for key, value in self.form_result.items():
            setattr(div, key, value)
        meta.Session.add(div)
        meta.Session.commit()
        h.flashmsg (u"Подразделение " + h.literal("&laquo;") + div.title + h.literal("&raquo;") + " добавлено.")
        redirect_to(h.url_for(controller='division', action='view', id=div.id))
        #meta.Session.expunge_all()

    def edit(self, id=None):
        h.requirerights("admin")
        div = h.checkdiv(id)
        users = meta.Session.query(model.Person).all()
        c.users = []
        for i in users:
            c.users.append([i.id, h.name(i)])
        #qmembers = meta.Session.query(model.Person).filter_by(division=div.id).all()
        members = []
        for i in div.people:
            members.append(i.id)
        values = {
            'title': div.title,
            'address': div.address,
            'description': div.description,
            'email': div.email,
            'phone': div.phone,
            'users': members,
        }
        return htmlfill.render(render("/divisions/edit.html"), values)

    @validate(schema=EditDivisionForm, form="edit")
    @restrict('POST')
    def save(self, id):
        h.requirerights("admin")
        div = h.checkdiv(id)
        for key, value in self.form_result.items():
            if getattr(div, key) != value:
                setattr(div, key, value)
        meta.Session.commit()
        h.flashmsg (u"Информация о подразделении была сохранена")
        redirect_to(h.url_for(controller='division', action='view', id=div.id))

    # Редактируем список пользователей
    @validate(schema=UserListForm, form="edit")
    @restrict('POST')
    def changeusers(self, id=None):
        h.admincheck()
        div = h.checkdiv(id)
        user = meta.Session.query(model.Person)
        userlist = eval(self.form_result['users'])
        # Сначала удалим всех нафиг
        oldusers = user.filter_by(div_id=id).all()
        for person in oldusers:
            person.div_id = None
        # Вносим в список новых пользователей
        try:
            users = user.filter(model.Person.id.in_(userlist)).all()
            for person in users:
                person.div_id = div.id
        except TypeError: # Если элемент один, то ругается, что Int не iterable
            user.get(userlist).div_id = div.id
        # Сохраняемся
        meta.Session.commit()
        h.flashmsg (u"Информация о подразделении была сохранена")
        redirect_to(h.url_for(controller='division', action='view', id=id))

    def delete(self, id=None):
        h.admincheck()
        div = h.checkdiv(id)
        # Стараемся не оставить людей сиротами
        for user in div.people:
            user.deleted = True
        #meta.Session.delete(div)
        div.deleted = True
        meta.Session.commit()
        h.flashmsg (u"Подразделение было удалено")
        redirect_to(h.url_for(controller='division', action='list', id=None))

    @jsonify
    def getperformers (self, id=None):
        '''Отдаёт JSON со списком пользователей-исполнителей'''
        if id is None: return ''
        div = meta.Session.query(model.Division).get(id)
        if div is None: return ''
        result = [{"id": x.id, "name": h.name(x)} for x in div.people if x.performer == True]
        return result
        
