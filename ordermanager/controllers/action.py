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

import datetime

log = logging.getLogger(__name__)

#####################################################################
# Валидация форм
class ValidPerformers(formencode.FancyValidator):
    def _to_python(self, values, state):
        if len(values['performers'])==0:
            raise formencode.Invalid(
                {'performers': u"Следует выбрать хотя бы одного исполнителя!"},
                values,
                state
            )
        meta.Session.expunge_all()
        all_perfs = [user.id for user in meta.Session.query(model.Person).filter_by(deleted=False).filter_by(div_id=values["div_id"]).filter_by(performer=True)]
        for perf in values['performers']:
            if perf not in all_perfs:
                raise formencode.Invalid(
                    {'performers': u"Один или больше исполнителей неверны. (Не относятся к выполняющему подразделению, может быть стоит сначала заявку взять себе на выполнение?)."}, # "%d не в %s. d%d s%d" % (perf, all_perfs, values['div_id'], session.get('division'))},
                    values,
                    state
                )
        return values

class ValidDivision(formencode.FancyValidator):
    def _to_python(self, value, state):
        value = int(value)
        if not h.have_role('admin'):
            if value != int(session.get('division')):
                raise formencode.Invalid(
                    u"Попытка взлома? Передан код подразделения %d, а должен быть %d."%(value,session.get('division')),
                    value,
                    state
                )
        else:
            divlist = [int(x.div_id) for x in meta.Session.query(model.Person.div_id).filter_by(performer=True).group_by(model.Person.div_id)]
            if value not in divlist:
                raise formencode.Invalid(
                    u"Неверное подразделение: Передано %s, а должно быть одним из %s."%(value,divlist),
                    value,
                    state
                )           
        return value

class ActForm(formencode.Schema):
    allow_extra_fields = True
    filter_extra_fields = True
    div_id = ValidDivision(
        if_missing = lambda: session.get('division'),
        messages = {
            'empty': u"Выберите подразделение",
            'notIn': u"Выберите подразделение из списка!"
        }        
    )
    performers = formencode.foreach.ForEach(formencode.validators.Int())
    status = formencode.validators.OneOf(
        [unicode(x.id) for x in meta.Session.query(model.Status).filter(model.sql.not_(model.Status.id.in_([1, 4, 6, 11, 12])))],
        not_empty=True,
        messages = {
            'empty': u"Выберите статус",
            'notIn': u"Выберите статус из списка!"
        }
    )
    description = formencode.validators.String()
    chained_validators = [ValidPerformers()]

class ComplainForm(formencode.Schema):
    allow_extra_fields = True
    filter_extra_fields = True
    id = formencode.validators.String(
        not_empty=True,
        messages = {'empty': u"Выберите заявку!"}
    )
    description = formencode.validators.String(
        not_empty=True,
        messages = {'empty': u"Вы "+h.strong(u"должны")+u" указать причину вашего недовольства!"}
    )

class ThankForm(formencode.Schema):
    allow_extra_fields = True
    filter_extra_fields = True
    id = formencode.validators.String(
        not_empty=True,
        messages = {'empty': u"Выберите заявку!"}
    )
    description = formencode.validators.String(
        messages = {'empty': u"Было бы неплохо узнать, что вас порадовало!"}
    )


#####################################################################
# Контроллер

class ActionController(BaseController):

    def __before__ (self):
        h.refresh_account()
        # Неавторизованным вход воспрещён!
        if session.get("guest"):
            abort (401)

    def choose (self, id=None):
        c.order = h.checkorder(id)
        # Теперь - проверка прав доступа (ответственный подразделения, выполняющего заявки)
        if not (h.have_role('admin') or ((h.have_role("appointer")) and session.has_key('division') and c.order.perf_id == session['division'])):
            abort(403)
        actionquery = meta.Session.query(model.Action)
        #if actionquery.filter_by(div_id=c.order.perf_id).all() is None:
        #    lastaction = None
        #else:
        #    lastaction = actionquery.filter_by(div_id=c.order.perf_id).order_by(model.sql.desc(model.Action.created)).first()
        lastaction = actionquery.filter_by(order_id=id).filter_by(div_id=c.order.perf_id).order_by(model.sql.desc(model.Action.created)).first()
        c.actions = actionquery.filter_by(order_id=id).order_by(model.Action.created).all()
        # Статусы
        statuses = meta.Session.query(model.Status).all()
        if h.have_role('admin'): excluded_statuses = [1, 4, 6, 11, 12, 14]
        else: excluded_statuses = [1, 2, 4, 6, 11, 12, 14]
        c.statuses = [[status.id, status.title] for status in statuses if status.id not in excluded_statuses]
        # Люди-исполнители
        if h.have_role('admin') and lastaction is not None:
            performers = meta.Session.query(model.Person).filter_by(deleted=False).filter_by(div_id=lastaction.div_id).filter_by(performer=True)
        else:
            performers = meta.Session.query(model.Person).filter_by(deleted=False).filter_by(div_id=session['division']).filter_by(performer=True)
        c.performers = [[user.id, h.name(user)] for user in performers]
        if lastaction is not None:
            c.curperfs = [x.id for x in lastaction.performers]
            c.curdiv = lastaction.div_id
        if h.have_role("admin"):
            divlist = [x.div_id for x in meta.Session.query(model.Person.div_id).filter_by(performer=True).all()]
            c.divisions = [[x.id, x.title] for x in meta.Session.query(model.Division).filter_by(deleted=False).filter(model.Division.id.in_(divlist)).all()]
        return render("/actions/choose.html")

    @validate (schema=ActForm, form="choose")
    @restrict ("POST")
    def act (self, id):
        order = h.checkorder(id)
        # Теперь - проверка прав доступа (ответственный подразделения, выполняющего эту заявку)
        if not (h.have_role('admin') or ((h.have_role("appointer")) and session.has_key('division') and order.perf_id == session['division'])):
            abort(403)
        lastaction = meta.Session.query(model.Action).order_by(model.sql.desc(model.Action.created)).first()
        if lastaction.status_id == self.form_result['status'] and [x.id for x in lastaction.performers] == self.form_result['performers']:
            h.flashmsg (u"Нельзя повторять статусы!")
            redirect_to(h.url_for(controller='action', action='choose', id=order.id)) 
            return u"Ай-яй-яй!"
        act = model.Action()
        act.order_id = order.id
        act.status_id = self.form_result['status']
        act.div_id = session['division']
        act.description = self.form_result['description']
        for pid in self.form_result['performers']:
            perf = meta.Session.query(model.Person).get(pid)
            act.performers.append(perf)
        meta.Session.add(act)
        # Если указан перевод состояния заявки - переводим в него. Иначе оставляем как есть.
        status = meta.Session.query(model.Status).get(int(self.form_result['status']))
        if status.redirects:
            order.status_id = status.redirects
        order.perf_id = session['division']
        # Обновляем исполнителей заявки
        if status.redirects == 1:
            order.performers = []
        else:
            order.performers = act.performers;
        # Если это "отметить выполненной", то ставим заявке время выполнения
        if status.id == 3:
            order.doneAt = datetime.datetime.now()
        # Готово
        meta.Session.commit()
        h.flashmsg (u"Статус заявки № " + h.strong(order.id) + " был изменён на " + h.strong(order.status.title) + ".")
        meta.Session.expire_all()
        redirect_to(h.url_for(controller='order', action='view', id=order.id)) 

    # Создание жалобы на заявку
    def complain (self, id=None):
        # Если номер заявки не указан, то позволим выбрать.
        if id is not None:
            c.order = h.checkorder(id)
            if not session.has_key('division'):
                abort(401)
            elif c.order.cust_id != session['division']:
                abort(403)
            c.selectedorder = c.order.id
        else: c.selectedorder = None               
        if not h.have_role('creator'):
           abort(403)
        orders = meta.Session.query(model.Order).filter("status_id<>:value and cust_id=:customer").params(value=4, customer=session['division']).all()
        c.orders =[['', u'-- выберите заявку, выполнением которой вы недовольны --']]
        for order in orders:
            if h.can_complain(order):
                if len(order.title) > 32:
                    order.title = order.title[:32] + u"…"
                str = unicode(order.id) + ". [" + order.work.title + h.literal(" &mdash; ") + order.category.title + "]: " + order.title
                c.orders.append([order.id, str])
        return render("/actions/complain.html")

    @validate (schema=ComplainForm, form="complain")
    @restrict ("POST")
    def makecomplaint (self):
        order = meta.Session.query(model.Order).filter_by(id=self.form_result['id']).first()
        if order is None:
            abort(404)
        if order.deleted:
            abort(410)
        # Теперь - проверка прав доступа (ответственный подразделения, подавшего эту заявку)
        if not (session.has_key('division') and session['division']):
            abort(401)
        if not (h.have_role('creator') and order.cust_id == session['division']):
            abort(403)
        complaint = model.Action()
        complaint.order_id = order.id
        complaint.status_id = 6
        complaint.div_id = session['division']
        perf = meta.Session.query(model.Person).get(session['id'])
        complaint.performers.append(perf)
        # Если претензию подаёт оператор, то и его добавим
        if session.has_key("operator_id") and session["id"] != session["operator_id"]:
            complaint.performers.append(meta.Session.query(model.Person).get(session["operator_id"]))
        complaint.description = self.form_result['description']
        meta.Session.add (complaint)
        order.status_id = 6
        # Обновляем создателей заявки
        if perf not in order.customers:
            order.customers.append(perf)
        meta.Session.commit()
        h.flashmsg (u"Жалоба подана. Всех лишат зарплаты. Дело заявки № " + h.strong(order.id) + " будет сделано.")
        redirect_to(h.url_for(controller='order', action='view', id=order.id)) 

    # Создание жалобы на заявку
    def thank (self, id=None):
        # Если номер заявки не указан, то позволим выбрать.
        if id is not None:
            c.order = h.checkorder(id)
            if not session.has_key('division'):
                abort(401)
            elif c.order.cust_id != session['division']:
                abort(403)
            c.selectedorder = c.order.id
        else: c.selectedorder = None               
        if not h.have_role('creator'):
           abort(403)
        orders = meta.Session.query(model.Order).filter("status_id<>:value and cust_id=:customer").params(value=4, customer=session['division']).all()
        c.orders =[['', u'-- выберите заявку, выполнением которой вы остались довольны --']]
        for order in orders:
            if h.can_complain(order):
                if len(order.title) > 32:
                    order.title = order.title[:32] + u"…"
                str = unicode(order.id) + ". [" + order.work.title + h.literal(" &mdash; ") + order.category.title + "]: " + order.title
                c.orders.append([order.id, str])
        return render("/actions/thank.html")

    @validate (schema=ThankForm, form="thank")
    @restrict ("POST")
    def makethank (self):
        order = meta.Session.query(model.Order).filter_by(id=self.form_result['id']).first()
        if order is None:
            abort(404)
        if order.deleted:
            abort(410)
        # Теперь - проверка прав доступа (ответственный подразделения, подавшего эту заявку)
        if not (session.has_key('division') and session['division']):
            abort(401)
        if not (h.have_role('creator') and order.cust_id == session['division']):
            abort(403)
        thank = model.Action()
        thank.order_id = order.id
        thank.status_id = 14
        thank.div_id = session['division']
        perf = meta.Session.query(model.Person).get(session['id'])
        thank.performers.append(perf)
        # Если претензию подаёт оператор, то и его добавим
        if session.has_key("operator_id") and session["id"] != session["operator_id"]:
            thank.performers.append(meta.Session.query(model.Person).get(session["operator_id"]))
        thank.description = self.form_result['description']
        meta.Session.add (thank)
        meta.Session.commit()
        h.flashmsg (u"Спасибо за " + h.literal("&laquo;") + "спасибо" + h.literal("&raquo;") + "!")
        redirect_to(h.url_for(controller='order', action='view', id=order.id)) 
        
    def approve (self, id):
        order = h.checkorder(id)
        # Теперь - проверка прав доступа (ответственный подразделения, подавшего эту заявку)
        if not (session.has_key('division') and order.cust_id == session['division'] and order.status_id == 3 and (h.have_role('appointer') or h.have_role('responsible') or h.have_role('chief'))):
            abort(403)
        approval = model.Action()
        approval.order_id = order.id
        approval.status_id = 4
        approval.div_id = session['division']
        #approval.performer = session['id']
        perf = meta.Session.query(model.Person).get(session['id'])
        approval.performers.append(perf)
        meta.Session.add (approval)
        order.status_id = 4
        # Обновляем создателей заявки
        if perf not in order.customers:
            order.customers.append(perf)
        meta.Session.commit()
        h.flashmsg (u"Заявка № " + h.strong(order.id) + " полностью выполнена.")
        redirect_to(h.url_for(controller='order', action='view', id=order.id))         


