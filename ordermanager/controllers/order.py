# -*- coding: utf-8 -*-
import logging

from pylons import request, response, session, tmpl_context as c
from pylons.controllers.util import abort, redirect_to
import ordermanager.lib.helpers as h
from ordermanager.lib.base import BaseController, render

import formencode
from formencode import htmlfill
from pylons.decorators import validate, jsonify
from pylons.decorators.rest import restrict

import ordermanager.model as model
import ordermanager.model.meta as meta

from sqlalchemy import or_

log = logging.getLogger(__name__)

#####################################################################
# Валидация форм
class ValidPerformers (formencode.FancyValidator):
    def _to_python (self, values, state):
        if len(values['performers'])==0:
            raise formencode.Invalid(
                {'performers': u"Следует выбрать хотя бы одного исполнителя!"},
                values,
                state
            )
        all_perfs = [user.id for user in meta.Session.query(model.Person).filter_by(div_id=session.get("division")).filter_by(performer=True)]
        for perf in values['performers']:
            if perf not in all_perfs:
                raise formencode.Invalid(
                    {'performers': u"Один или больше исполнителей неверны. (Не относятся к выполняющему подразделению, может быть стоит сначала заявку взять себе на выполнение?)"},
                    values,
                    state
                )
        return values
        
class MatchedCategories (formencode.FancyValidator):
    def _to_python (self, values, state):
        validcats = [unicode(x.id) for x in meta.Session.query(model.Category).filter_by(deleted=False).\
            filter(or_(model.Category.upcat_id==values['upcat_id'], model.Category.upcat_id==None)).all()]
        if values['cat_id'] not in validcats:
            raise formencode.Invalid(
                {'cat_id': u"Неподходящяя категория! Выберите из списка. Если ошибка повторяется - перезагрузите страницу или включите JavaScript в браузере."},
                values, state)
        return values 

class OrderForm (formencode.Schema):
    allow_extra_fields = True
    filter_extra_fields = True
    title = formencode.validators.String(
        #not_empty=True,
        messages = {'empty': u"Введите название!"}
    )
    work_id = formencode.validators.OneOf(
        [unicode(x.id) for x in meta.Session.query(model.Work).filter_by(deleted=False).all()],
        not_empty=True,
        messages = {
            'empty': u"Выберите вид работ",
            'notIn': u"Выберите вид работы из списка!"
        }
    )
    upcat_id = formencode.validators.OneOf(
        [unicode(x.id) for x in meta.Session.query(model.UpperCategory).filter_by(deleted=False).all()],
        not_empty=True,
        messages = {
            'empty': u"Выберите надкатегорию",
            'notIn': u"Выберите надкатегорию из списка!"
        }
    )
    cat_id = formencode.validators.OneOf(
        [unicode(x.id) for x in meta.Session.query(model.Category).filter_by(deleted=False).all()],
        not_empty=True,
        messages = {
            'empty': u"Выберите категорию",
            'notIn': u"Выберите вид работы из списка!"
        }
    )
    place = formencode.validators.String()
    # TODO: Сделать валидацию (по OneOf) инвентарных номеров!
    inventories = formencode.foreach.ForEach(formencode.validators.Int())
    workload = formencode.validators.Number()
    chained_validators = [MatchedCategories()]

class TakeForm(formencode.Schema):
    allow_extra_fields = True
    filter_extra_fields = True
    performers = formencode.foreach.ForEach(formencode.validators.Int())
    workload = formencode.validators.Number()
    chained_validators = [ValidPerformers()]

class GoTo(formencode.Schema):
    allow_extra_fields = True
    filter_extra_fields = True
    id = formencode.validators.Int()

#####################################################################
# Контроллер

class OrderController(BaseController):

    def __before__ (self):
        h.refresh_account()
        c.upcats = [x for x in meta.Session.query(model.UpperCategory).filter_by(deleted=False).all()]

    def index(self):
        #return redirect_to(h.url_for(action="list"))
        pass

    def list(self, show=None, sort="date", **kwargs):
        qorder = meta.Session.query(model.Order).order_by(model.sql.desc(model.Order.created))
        c.upcat = kwargs.get('upcat', None)  
        c.mworkcur = kwargs.get('work', None) or request.params.get('work','any')  
        c.mcatcur = kwargs.get('cat', None) or request.params.get('cat','any')
        c.mstatcur = kwargs.get('status', None) or request.params.get('status','any')    
        if c.upcat not in ['any', None]:
            upcat = meta.Session.query(model.UpperCategory).filter_by(url_text=c.upcat).first()
            if upcat is not None:
                qorder = qorder.filter_by(upcat_id=upcat.id)
        if c.mcatcur not in ['any', None]:
            cat = meta.Session.query(model.Category).filter_by(url_text=c.mcatcur).first()
            if cat is not None:
                qorder = qorder.filter_by(cat_id=cat.id)
        if c.mworkcur not in ['any', None]:
            work = meta.Session.query(model.Work).filter_by(url_text=c.mworkcur).first()
            if work is not None:
                qorder = qorder.filter_by(work_id=work.id)                
        if c.mstatcur not in ['any', None]:
            status = meta.Session.query(model.Status).filter(model.Status.redirects==model.Status.id).filter_by(id=c.mstatcur).first()
            if status is not None:
                qorder = qorder.filter_by(status_id=status.id)
        qorder = qorder.filter_by(deleted=bool(request.urlvars.get('deleted', False)))
        # Разбивка на страницы
        c.paginator = h.paginate.Page(
            qorder,
            page = (kwargs.get('page') or 1),   #int(request.params.get('page', 1)),
            items_per_page = (session.get('preferences') or {}).get('ordersinpage', 15),
        )
        c.ordercount = qorder.count()
        mstat = meta.Session.query(model.Status)\
            .filter(model.Status.redirects==model.Status.id).filter_by(deleted=False)\
            .order_by(model.Status.id).all()
        c.mstat = [['any', u' -- Все -- ']] + [[x.id, x.title] for x in mstat]
        mcat = meta.Session.query(model.Category).filter_by(deleted=False).order_by(model.Category.id)
        if kwargs.get('upcat') not in ['any', None] and upcat is not None:
            mcat = mcat.filter(or_(model.Category.upcat_id==upcat.id, model.Category.upcat_id==None))
        c.mcat = [['any', u' -- Все -- ']] + [[x.url_text, x.title] for x in mcat.all()]
        mwork = meta.Session.query(model.Work).filter_by(deleted=False).order_by(model.Work.id).all()
        c.mwork = [['any', u' -- Все -- ']] + [[x.url_text, x.title] for x in mwork]
        return render ("/orders/list.html")

    def listownorders (self, type="performing", **kwargs):
        qorder = meta.Session.query(model.Order).order_by(model.sql.desc(model.Order.created))
        qorder = qorder.filter(model.Order.deleted==False)
        if type == "performing":
           qorder = qorder.filter(model.sql.not_(model.Order.status_id.in_([1, 3, 4, 5, 15])))
           qorder = qorder.filter(model.Order.performers.any(id=session['id']))
        # Разбивка на страницы
        c.paginator = h.paginate.Page(
            qorder,
            page = (kwargs.get('page') or 1),   #int(request.params.get('page', 1)),
            items_per_page = (session.get('preferences') or {}).get('ordersinpage', 15),
        )
        c.ordercount = qorder.count()
        return render ("/orders/list.html")
        
    def filter(self, **kwargs):
        redirect_to(h.url_for(controller='order', action='list',
                              upcat=(request.params.get('upcat', None) or kwargs.get('upcat', 'any')), \
                              cat=request.params.get('cat','any'), work=request.params.get('work', 'any'),
                              status=request.params.get('status', 'any')))

    def view(self, id):
        c.order = h.checkorder(id)
        #c.order.title = c.order.title.replace(u"\n", h.literal(u"<br />"));
        return render("/orders/view.html")

    def add(self):
        '''Показ формы для создания заявки'''
        h.requirerights('creator')
        work = meta.Session.query(model.Work).filter_by(deleted=False).order_by(model.Work.id).all()
        c.work = [[None, u" -- выберите вид работ -- "]]
        for i in work:
            c.work.append([i.id, i.title])
        category = meta.Session.query(model.Category).filter_by(deleted=False).order_by(model.Category.id).all()
        c.category = [[None, u" -- выберите категорию -- "]]
        for i in category:
            c.category.append([i.id, i.title])
        upcategory = meta.Session.query(model.UpperCategory).filter_by(deleted=False).order_by(model.UpperCategory.id).all()
        c.upcategory = [[None, u" -- выберите надкатегорию -- "]]
        for i in upcategory:
            c.upcategory.append([i.id, i.title])
        c.curcat = c.curwork = c.upcat = []
        c.workload = 1.0
        return render ("/orders/add.html")

    @validate(schema=OrderForm, form="add")
    @restrict('POST')
    def create(self):
        '''Метод непосредственного создания заявки в БД'''
        h.requirerights('creator')
        order = model.Order()
        # Создание заявки
        order.status = meta.Session.query(model.Status).get(1); # Заявка свободна!
        order.cust_id = session['division'] # Заявка исходит от подразделения текущего пользователя
        for key, value in self.form_result.items():
            if key != 'inventories':       # Всё прочее, кроме инвентарников
                setattr(order, key, value) # тащим из формы прямо в базу
        meta.Session.add(order)
        # Добавляем отношения заявка <-> инвентарники
        for inv in self.form_result['inventories']:
            item = meta.Session.query(model.Inventory).get(inv);
            # <TODO text="Убрать добавление инвентарников в базу после введения проверок!">
            if not item:
                item = model.Inventory()
                item.id = inv
                meta.Session.add(item)
            # </TODO>
            order.inventories.append(item)
        # Создаём первую запись в журнале - "заявка создана"
        act = model.Action()
        act.div_id = session['division']
        perf = meta.Session.query(model.Person).get(session["id"])
        act.performers.append(perf)
        if session.has_key("operator_id") and session["id"] != session["operator_id"]:
            act.status = meta.Session.query(model.Status).get(12) # Сообщаем, если создаёт оператор (и добавляем его)
            act.performers.append(meta.Session.query(model.Person).get(session["operator_id"]))
        else:
            act.status = meta.Session.query(model.Status).get(11) # Или если просто сам пользователь
        act.order_id = order.id
        meta.Session.add(act)
        # Обновляем создателей заявки
        order.customers.append(perf);
        # Готово, в базу!
        meta.Session.commit()
        h.flashmsg (u"Заявка № " + h.strong(order.id) + " была добавлена.")
        redirect_to(h.url_for(controller='order', action='view', id=order.id))

    def edit(self, id):
        order = h.checkorder(id)
        # Теперь - проверка прав доступа (админ либо ответственный подразделения, создавшего заявку)
        h.requirelogin()
        if not ((session.has_key('admin') and session['admin']) or (session.has_key('division') and session.has_key('creator') and session['creator'] and order.customer.id==session['division'])):
            abort(403)
        work = meta.Session.query(model.Work).order_by(model.Work.id).all()
        c.work = []
        for i in work:
            c.work.append([i.id, i.title])
        category = meta.Session.query(model.Category)\
            .filter(model.Category.upcat_id==order.upper_category.id)\
            .order_by(model.Category.id).all()
        c.category = []
        for i in category:
            c.category.append([i.id, i.title])
        upcategory = meta.Session.query(model.UpperCategory).filter_by(deleted=False).order_by(model.UpperCategory.id).all()
        c.upcategory = [[None, u" -- выберите надкатегорию -- "]]
        for i in upcategory:
            c.upcategory.append([i.id, i.title])
        c.curwork = [order.work]
        c.curcat = [order.category]
        c.upcat = [order.upper_category]
        values = {
            'title': order.title,
            'work_id': order.work_id,
            'cat_id': order.cat_id,
            'upcat_id': order.upcat_id,
            'workload': order.workload
        }
        c.invs = [item for item in order.inventories]
        return htmlfill.render(render("/orders/edit.html"), values)

    @validate(schema=OrderForm, form="edit")
    @restrict('POST')
    def save(self, id):
        order = h.checkorder(id)
        # Теперь - проверка прав доступа (админ либо ответственный подразделения, создавшего заявку)
        if not (h.have_role('admin') or h.have_role('operator') or (session.has_key('division') and session.has_key('creator') and session['creator'] and order.customer.id==session['division'])):
            abort(401)
        for key, value in self.form_result.items():
            if getattr(order, key) != value and key != 'inventories':
                setattr(order, key, value)
        # Изменяем отношения заявка <-> инвентарники
        for item in order.inventories: # Удаляем уже неактуальные отношения (удалённые при редактировании инвентарники)
            if item.id not in self.form_result['inventories']:
                order.inventories.remove(item)
        for inv in self.form_result['inventories']: # Добавляем новые отношения
            item = meta.Session.query(model.Inventory).get(inv);
            if not item:
                # <TODO text="Убрать добавление инвентарников в базу после введения проверок!">
                item = model.Inventory()
                item.id = inv
                meta.Session.add(item)
                # </TODO>
            if item not in order.inventories:
                order.inventories.append(item)
        meta.Session.commit()
        h.flashmsg (u"Заявка была изменена")
        redirect_to(h.url_for(controller='order', action='view', id=order.id))

    def delete(self, id):
        h.requirerights("admin")
        order = h.checkorder(id)
        #meta.Session.delete(order)
        order.deleted = True;
        meta.Session.commit()
        h.flashmsg (u"Заявки № " + h.strong(order.id) + " больше нет.")
        redirect_to(h.url_for(controller='order', action='list', id=None))

    def takerequest (self, id=None):
        c.order = h.checkorder(id)
        # Теперь - проверка прав доступа
        if not (h.have_role('appointer') and c.order.status_id==1):
            abort(401)
        c.division = meta.Session.query(model.Division).get(int(session['division']))
        performers = meta.Session.query(model.Person).filter_by(deleted=False)\
            .filter_by(div_id=session['division']).filter_by(performer=True).order_by(model.Person.surname).all()
        c.performers = []
        for user in performers:
            c.performers.append([user.id, h.name(user)])
        return render ("/orders/take.html")

    @validate(schema=TakeForm, form="takerequest")
    @restrict("POST")
    def take (self, id=None):
        order = h.checkorder(id)
        # Теперь - проверка прав доступа (ответственный подразделения, могущего выполнять заявки)
        if not (h.have_role('appointer') and order.status_id==1):
            abort(403)
        elif h.have_role('guest'): abort(401)
        act = model.Action()
        act.order_id = order.id
        act.status = meta.Session.query(model.Status).get(2)
        act.div_id = session['division']
        #act.performer = self.form_result['performer']
        for pid in self.form_result['performers']:
            perf = meta.Session.query(model.Person).get(pid)
            act.performers.append(perf)
        order.status = meta.Session.query(model.Status).get(2)
        order.perf_id = session['division']
        order.workload = self.form_result['workload']
        meta.Session.add(act)
        # Обновляем исполнителей заявки
        order.performers = act.performers;
        # Готово!
        meta.Session.commit()
        h.flashmsg (u"Вы взяли заявку № " + h.strong(order.id) + u" для выполнения себе. Исполнители: %s"%(u", ".join([h.name(x) for x in act.performers])))
        redirect_to(h.url_for(controller='order', action='view', id=order.id))

    @validate(schema=GoTo, form="list")
    def goto (self):
        redirect_to(h.url_for(controller='order', action='view', id=self.form_result['id']))

    def getinfo (self, id=None):
        if id is None:
            return ''
        c.order = meta.Session.query(model.Order).get(int(id))
        if c.order is None:
            return ''
        return render ("/orders/info.html") 
    
    @jsonify
    def getcatsforupcat (self, id=None):
        try:
            id = int(id)
        except TypeError:
            abort(400)
        categories = meta.Session.query(model.Category).filter(or_(model.Category.upcat_id==id, model.Category.upcat_id==None)).all()
        result = [dict(id=x.id, text=x.title) for x in categories]
        return result

    def revoke (self, id=None):
        """Отзыв заявки её создателем (например, решили проблему сами или «ложная тревога»)."""
        order = h.checkorder(id)
        # Заявка должна быть свободна!
        if order.status.id != 1:
            abort(403)
        # Проверка прав доступа (админ либо ответственный подразделения, создавшего заявку)
        if not (h.have_role('admin') or (session.has_key('division') and session.has_key('creator') and session['creator'] and order.cust_id==session['division'])):
            abort(401)
        # Заявка готова, но никто её не сделал
        order.status = meta.Session.query(model.Status).get(15)
        order.performers = []
        order.performer = None
        # Добавление записи в журнал действий над заявкой
        act = model.Action()
        act.order_id = order.id
        act.status = meta.Session.query(model.Status).get(15)
        act.division = meta.Session.query(model.Division).get(session['division'])
        act.performers.append(meta.Session.query(model.Person).get(session['id']))
        if session.has_key("operator_id") and session["id"] != session["operator_id"]:
            act.performers.append(meta.Session.query(model.Person).get(session["operator_id"]))
        meta.Session.add(act)
        # Готово
        meta.Session.commit()
        h.flashmsg (u"Заявка № " + h.strong(order.id) + u" отозвана.")
        redirect_to(h.url_for(controller='order', action='view', id=order.id))

