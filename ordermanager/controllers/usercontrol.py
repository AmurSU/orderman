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
import sqlalchemy
from sqlalchemy import and_, or_, join

from hashlib import md5
import cPickle as pickle

log = logging.getLogger(__name__)

#####################################################################
# Валидация форм

# Этот валидатор проверяет логин на уникальность
class UniqueUsername(formencode.FancyValidator):
    def _to_python(self, value, state):
        value = unicode(value)
        login = meta.Session.query(model.Person.login).filter("LOWER(login) = LOWER(:value)").params(value=value).first()
        if login:
            raise formencode.Invalid(self.message('invalid', state), value, state)
        else:
            return value
       
#         users = meta.Session.query(model.Person).all()
#         usernames = [user.login for user in users]
#         if value in usernames:
#             raise formencode.Invalid(
#                 self.message('invalid', state),
#                 value, state)
#         return value

# Этот валидатор проверяет пароль на самого себя
class CorrectPass(formencode.FancyValidator):
    def _to_python(self, value, state):
        user = meta.Session.query(model.Person).get(int(request.urlvars['id']))
        if not h.have_role('admin') and md5(value.encode('utf-8')).hexdigest() != user.password:
            raise formencode.Invalid(
                self.message('invalid', state),
                value, state)
        return value

# Этот валидатор проверяет правильность учётных данных при авторизации.
class ValidateLogin (formencode.FancyValidator):
    def _to_python (self, values, state):
        user = meta.Session.query(model.Person).filter("LOWER(login) = LOWER(:value)").params(value=values.get('login')).first()
        # Если такого пользователя нет или хэши паролей не совпадают
        if (user is None) or (md5(values.get('password').encode('utf-8')).hexdigest() != user.password):
            values['password'] = "" # Установим пустой пароль, чтобы не выводить его обратно пользователю (т.к. небезопасно)
            raise formencode.Invalid(
                {"login": u"Комбинация логин/пароль неверна! Проверьте раскладку клавиатуры и регистр символов.",
                "password": u"Также проверьте правильность ввода логина и пароля."},
                values, state)
        values['login'] = user.login # Вообще везде в приложении регистр логина играет роль, поэтому исправим то, что ввёл пользователь
        return values

class LoginForm(formencode.Schema):
    allow_extra_fields = True
    filter_extra_fields = True
    login = formencode.validators.UnicodeString(
        strip = True,
        not_empty=True,
        max = 32,
        messages = {
            'empty':   u"Введите ваш логин для входа",
            'tooLong': u"Логин слишком длинный!"
        }
    )
    password = formencode.validators.UnicodeString(
        strip = True,
        not_empty=True,
        max = 32,
        messages = {
            'empty':   u"Введите ваш пароль для входа",
            'tooLong': u"Пароль слишком длинный!"
        }
    )
    chained_validators = [ValidateLogin()]

class NewUserForm(formencode.Schema):
    allow_extra_fields = True
    filter_extra_fields = True
    login = UniqueUsername(
        strip = True,
        not_empty=True,
        messages = {
            'empty': u"Введите логин",
            'invalid': u'Это имя пользователя уже занято. Выберите другое.'
        }
    )
    name = formencode.validators.UnicodeString(
        #not_empty=True,
        messages = {'empty': u"Введите имя"}
    )
    surname = formencode.validators.UnicodeString(
        #not_empty=True,
        messages = {'empty': u"Введите фамилию"}
    )
    patronymic = formencode.validators.UnicodeString(
        #not_empty=True,
        messages = {'empty': u"Введите отчество"}
    )
    div_id = formencode.validators.OneOf(
        [unicode(x.id) for x in meta.Session.query(model.Division).filter_by(deleted=False).all()],
        not_empty=False,
        messages = {
            'invalid': u"Введите пароль",
            'notIn': u"Значение должно быть одним из списка!"
        }
    )
    email = formencode.validators.Email()
    phone = formencode.validators.String()
    # Права доступа
    creator = formencode.validators.StringBoolean(if_missing=False)
    performer = formencode.validators.StringBoolean(if_missing=False)
    appointer = formencode.validators.StringBoolean(if_missing=False)
    responsible = formencode.validators.StringBoolean(if_missing=False)
    chief = formencode.validators.StringBoolean(if_missing=False)
    admin = formencode.validators.StringBoolean(if_missing=False)
    operator = formencode.validators.StringBoolean(if_missing=False)
    password = formencode.validators.UnicodeString(
        not_empty=True,
        max = 32,
        min = 4,
        messages = {'empty': u"Введите пароль (не может быть пустым!)"}
    )
    passcheck = formencode.validators.UnicodeString(
        not_empty=True,
        messages = {'empty': u"Введите подтверждение пароля"}
    )
    chained_validators = [formencode.validators.FieldsMatch(
        'password', 'passcheck'
    )]


class EditUserForm(formencode.Schema):
    allow_extra_fields = True
    filter_extra_fields = True
    name = formencode.validators.UnicodeString(
        not_empty=True,
        messages = {'empty': u"Введите имя"}
    )
    surname = formencode.validators.UnicodeString(
        not_empty=True,
        messages = {'empty': u"Введите фамилию"}
    )
    patronymic = formencode.validators.UnicodeString(
        not_empty=True,
        messages = {'empty': u"Введите отчество"}
    )
    div_id = formencode.validators.OneOf(
        [unicode(x.id) for x in meta.Session.query(model.Division).filter_by(deleted=False).all()],
        not_empty=False,
        if_missing=False,
        messages = {
            'invalid': u"Выберите подразделение",
            'notIn': u"Значение должно быть одним из списка!"
        }
    )
    email = formencode.validators.Email()
    phone = formencode.validators.UnicodeString()
    # Права доступа
    creator = formencode.validators.StringBoolean(if_missing=False)
    performer = formencode.validators.StringBoolean(if_missing=False)
    appointer = formencode.validators.StringBoolean(if_missing=False)
    responsible = formencode.validators.StringBoolean(if_missing=False)
    chief = formencode.validators.StringBoolean(if_missing=False)
    operator = formencode.validators.StringBoolean(if_missing=False)
    admin = formencode.validators.StringBoolean(if_missing=False)

class ChPassForm(formencode.Schema):
    allow_extra_fields = True
    filter_extra_fields = True
    oldpass = CorrectPass(
        if_missing = "",
        strip = True,
        not_empty = not h.have_role('admin'),
        messages = {
            'empty': u"Введите старый пароль. Без него нельзя установить новый!",
            'invalid': u'Неверный пароль.'
        }
    )
    newpass = formencode.validators.UnicodeString(
        strip = True,
        not_empty=True,
        messages = {'empty': u'Пароль не может быть пустым!'}
    )
    chkpass = formencode.validators.UnicodeString(
        strip = True,
        not_empty=True,
        messages = {'empty': u'Пароль не может быть пустым!'}
    )
    chained_validators = [formencode.validators.FieldsMatch(
        'newpass', 'chkpass'
    )]

class SwitchForm(formencode.Schema):
    allow_extra_fields = True
    filter_extra_fields = True
    user_id = formencode.validators.OneOf(
        [unicode(x.id) for x in meta.Session.query(model.Person).filter_by(deleted=False).filter_by(creator=True).all()],
        not_empty=False,
        if_missing=False,
        messages = {
            'invalid': u"Выберите пользователя",
            'notIn': u"Значение должно быть одним из списка!"
        }
    )
    
class PrefsForm(formencode.Schema):
    allow_extra_fields = True
    filter_extra_fields = True
    upcat = formencode.validators.OneOf(
        ["None"] + [unicode(x.url_text) for x in meta.Session.query(model.UpperCategory).filter_by(deleted=False).all()],
        if_missing=None,
        messages = {
            'invalid': u"Выберите тип",
            'notIn': u"Значение должно быть одним из списка!"
        }
    )
    ordersinpage = formencode.validators.Int(
        if_missing = 15,
        max = 50,
        min = 5,
        messages = {
            'invalid': u"Введите число.",
            'tooHigh': u"Введите число не большее %(max)i.",
            'tooLow': u"Введите число не меньшее %(min)i."
        }        
    )
    
#####################################################################
# Контроллер

class UsercontrolController(BaseController):

    def __before__ (self):
        h.refresh_account() 

    def index(self):
        return redirect_to(h.url_for(action="list"))

    def list(self, show=None):
        q = meta.Session.query(model.Person).filter_by(deleted=False).order_by(model.Person.login).order_by(model.Person.surname)
        if show is None:
            users = q
        elif show == "customers":
            users = q.filter_by(creator=True)
        elif show == "performers":
            users = q.filter_by(performer=True)
        elif show == "appointers":
            users = q.filter_by(appointer=True)
        elif show == "responsibles":
            users = q.filter_by(responsible=True)
        elif show == "chiefs":
            users = q.filter_by(chief=True)
        elif show == "administrators":
            users = q.filter_by(admin=True)
        elif show == "operators":
            users = q.filter_by(operator=True)
        else:
            users = q
        # Ищем?
        c.search = request.params.get('search', '')
        if len(c.search):
            search = "%"+unicode(c.search).lower()+"%"
            users = users.filter(sqlalchemy.or_(model.Person.login.ilike(search), model.Person.surname.ilike(search), model.Person.name.ilike(search), model.Person.patronymic.ilike(search)))
        # Разбивка на страницы
        c.paginator = h.paginate.Page(
            users,
            page=int(request.params.get('page', 1)),
            items_per_page = 15,
        )
        c.usercount = q.count()
        return render ("/users/list.html")

    def login(self):
        return render ("/users/login.html")

    @validate(schema=LoginForm, form="login")
    @restrict('POST')
    def dologin(self):
        session.clear()
        qloginer = meta.Session.query(model.Person)
        person = qloginer.filter_by(login=self.form_result['login']).first()
        # Загрузка информации о человеке и его правах доступа
        h.refresh_account(person.id)
        # Велкам!
        session['flash'] = u"Вы успешно вошли в систему"
        session.save()
        redirect_to(h.url_for(controller="main", action="index"))
            

    def logout(self):
        session.clear()
        session['flash'] = u"Вы вышли из системы"
        session.save()
        redirect_to(h.url_for(controller="main", action="index", id=None))

    def view(self, id=None, showallorders=False):
        c.person = h.checkuser(id)
        act = meta.Session.query(model.Action).filter(model.Action.performers.any(id=id))
        c.givememore = not showallorders
        # Выбираем заявки, созданные этим пользователем
        creatingacts = act.filter(model.Action.status_id.in_([11, 12])).all()
        createdorders = meta.Session.query(model.Order).filter(model.Order.id.in_([x.order_id for x in creatingacts])).order_by(model.Order.id)
        c.creatednum = createdorders.count()
        # Выбираем заявки, выполняемые этим пользователем
        performingacts = act.filter(model.sql.not_(model.Action.status_id.in_([1, 6, 11, 12]))).all()
        #performingacts = act.filter("status_id!=11 AND status_id!=12 AND status_id!=6 AND status_id!=1").all()
        performing = meta.Session.query(model.Order).filter(model.Order.id.in_([x.order_id for x in performingacts])).order_by(model.Order.id)
        c.performingnum = performing.count()
        # TODO: Выбираем заявки, выполненные этим пользователем
        if showallorders:
            c.createdorders = createdorders.all()
            c.performing = performing.all()
        else:
            c.createdorders = createdorders[:5]
            c.performing = performing[:5]
        return render("/users/view.html")

    def add(self):
        h.requirerights("admin")
        divisions = meta.Session.query(model.Division).filter_by(deleted=False).order_by(model.Division.title).all()
        c.divisions = [[None, u"-- выберите подразделение --"]]
        for i in divisions:
            c.divisions.append([i.id, i.title])
        return render ("/users/add.html")

    @validate(schema=NewUserForm, form="add")
    @restrict('POST')
    def create(self):
        h.requirerights("admin")
        user = model.Person()
        password = md5(self.form_result['password'].encode('utf-8')).hexdigest()
        for key, value in self.form_result.items():
            if key not in ["passcheck"]:
                setattr(user, key, value)
        user.password = password
        meta.Session.add(user)
        meta.Session.commit()
        h.flashmsg (u"Пользователь был добавлен.")
        redirect_to(h.url_for(controller='usercontrol', action='view', id=user.id))
        #meta.Session.expunge_all()


    def edit(self, id=None):
        user = h.checkuser(id)
        h.requirerights(user_is=id)
        qdivs = meta.Session.query(model.Division).filter_by(deleted=False)
        divisions = qdivs.all()
        c.divisions = [[None, u"-- нет --"]]
        for i in divisions:
            c.divisions.append([i.id, i.title])
        values = {
            'login': user.login,
            'name': user.name,
            'surname': user.surname,
            'patronymic': user.patronymic,
            'email': user.email,
            'phone': user.phone,
            'creator': user.creator,
            'performer': user.performer,
            'appointer': user.appointer,
            'responsible': user.responsible,
            'chief': user.chief,
            'admin': user.admin,
            'operator': user.operator,
            'div_id': user.div_id
        }
        c.curdiv = [user.div_id]
        return htmlfill.render(render("/users/edit.html"), values)

    @validate(schema=EditUserForm, form="edit")
    @restrict('POST')
    def save(self, id=None):
        user = h.checkuser(id)
        h.requirerights(user_is=id)
        if session.has_key('admin') and session['admin']:
            for key, value in self.form_result.items():
                if getattr(user, key) != value:
                    setattr(user, key, value)
        else:
            for key, value in self.form_result.items():
                if key in ['name', 'surname', 'patronymic', 'email', 'phone']:
                    if getattr(user, key) != value:
                        setattr(user, key, value)
        meta.Session.commit()
        h.flashmsg (u"Информация о пользователе была обновлена. ДА!")
        redirect_to(h.url_for(controller='usercontrol', action='view', id=user.id))
        #meta.Session.expunge(user.division)
        #meta.Session.expunge(user) # Принудительный сброс пользователя из сессии ORM в БД

    @validate(schema=ChPassForm, form="edit")
    @restrict('POST')
    def changepassword (self, id=None):
        user = h.checkuser(id)
        h.requirerights(user_is=id)
        user.password = md5(self.form_result['newpass'].encode('utf-8')).hexdigest()
        meta.Session.commit()
        h.flashmsg (u"Пароль был изменён")
        redirect_to(h.url_for(controller='usercontrol', action='list', id=None))

    def delete(self, id=None):
        h.requirerights("admin")
        user = h.checkuser(id)
        #meta.Session.delete(user)
        user.deleted = True
        meta.Session.commit()
        h.flashmsg (u"Пользователь был удалён")
        redirect_to(h.url_for(controller='usercontrol', action='list', id=None))

    def switch (self, id=None):
        h.requirerights("operator")
        userdivs =meta.Session.query(model.Person, model.Division).join(model.Division)\
            .filter(and_(model.Person.deleted==False, model.Person.creator==True))\
            .filter(or_(model.Person.chief==True, model.Person.responsible==True))\
            .order_by(model.Division.title).order_by(model.Person.surname).all()
        #users = meta.Session.query(model.Person)\
        #    .filter_by(deleted=False).filter_by(creator=True).order_by(model.Person.login).order_by(model.Person.surname).all()
        #users.sort(key=lambda x:(x.division.title, x.surname));
        #c.users = [[unicode(x.id), x.division.title + h.literal(" &mdash; ") + (h.name(x))] for x in users]
        c.users = [[unicode(x[0].id), x[1].title + h.literal(" &mdash; ") + (h.name(x[0]))] for x in userdivs]
        c.selected = id
        return render ("/users/switch.html")

    @validate(schema=SwitchForm, form="switch")
    @restrict('POST')
    def doswitch (self):
        h.requirerights("operator")
        h.refresh_account(self.form_result["user_id"], session.get("id")) 
        h.flashmsg (u"Теперь вы под другим пользователем. Нажмите 'вернуться' вверху, чтобы вернуться в свою учётную запись.")       
        redirect_to(h.url_for(controller="order", action="add", id=None))

    def switchback (self):
        if session.has_key("operator_id"):
            h.refresh_account(session.get("operator_id")) 
        redirect_to(h.url_for(controller="usercontrol", action="switch", id=None))
        
    def preferences (self):
        c.user = h.checkuser(session['id'])
        c.upcats = [[None, u" -- все -- "]] + [[x.url_text, x.title] for x in meta.Session.query(model.UpperCategory).filter_by(deleted=False).all()]
        return render ("/users/preferences.html")
    
    @validate(schema=PrefsForm, form="preferences")
    @restrict('POST')   
    def saveprefs (self):
        user = h.checkuser(session['id'])
        user.preferences = dict()
        for key,value in self.form_result.iteritems():
            if value == u"None":
                user.preferences[key] = None
            else:
                user.preferences[key] = value
        meta.Session.commit()
        h.flashmsg (u"Ваши настройки были бережно сохранены...")
        redirect_to(h.url_for(controller="main", action="index"))
