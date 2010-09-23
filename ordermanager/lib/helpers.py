# -*- coding: utf-8 -*-
"""Helper functions

Consists of functions to typically be used within templates, but also
available to Controllers. This module is available to templates as 'h'.
"""
# Import helpers as desired, or define your own, ie:
#from webhelpers.html.tags import checkbox, password

from routes import url_for

from webhelpers.html.tags import *
from webhelpers.html.tools import *
from webhelpers.html import literal
import webhelpers.paginate as paginate

from formbuild.helpers import field
from formbuild import start_with_layout as form_start, end_with_layout as form_end
from formbuild.helpers import checkbox_group

import pylons

import datetime

import ordermanager.model as model
import ordermanager.model.meta as meta

import pytils
from pytils.numeral import get_plural

def now():
    return datetime.datetime.now()
    

# Формирует готовую HTML-ссылку
def link (controller=None, action=None, id=None, text="Ссылка", title="", class_="", id_=""):
    answer = literal('<a ')
    if class_:
        answer += literal('class="'+class_+'" ')
    if id_:
        answer += literal('id="'+id_+'" ')
    if title:
        answer += literal('title="') + title + literal('" ')
    if url_for(id=id) != url_for(controller=controller, action=action, id=id):
       answer += literal('href="') + url_for(controller=controller, action=action, id=id) + literal('"')
       answer +=  literal(">") + text +  literal("</a>")
    else:
       answer += literal('class="nolink">') + text + literal("</a>")
    return answer

def link2 (url=None, text="Ссылка", title="", class_="", id_=""):
    if url_for() != url_for(url):
       answer = literal('<a href="') + url + literal('"')
       if class_:
           answer += literal(' class="'+class_+'"')
       if id_:
           answer += literal(' id="'+id_+'"')
       if title:
           answer += literal(' title="') + title + literal('"')
       answer +=  literal(">") + text +  literal("</a>")
    else:
       answer = literal('<a class="nolink"')
       if title:
           answer += literal(' title="') + title + literal('"')
       answer +=  literal(">") + text +  literal("</a>")
    return answer

# Ссылка для главного меню
def mlink (controller=None, action=None, id=None, upcat=None, text="Ссылка", title=""):
    if url_for(action=None, id=id) != url_for(controller=controller, action=None, id=id):
       answer = literal('<a href="') + url_for(controller=controller, action=action, id=id, upcat=upcat, show=None, type=None) + literal('"')
       if title:
           answer += literal(' title="') + title + literal('"')
       answer +=  literal(">") + text +  literal("</a>")
    else:
       answer = literal('<a class="nolink"')
       if title:
           answer += literal(' title="') + title + literal('"')
       answer +=  literal(">") + text +  literal("</a>")
    return answer

def admincheck():
    requirerights("admin")
#    if not pylons.session.has_key('user'):
#        pylons.controllers.util.abort(401)
#    if not pylons.session['admin']:
#        pylons.controllers.util.abort(403)

def requirerights(rights="admin", user_is=None):
    if not pylons.session.has_key('user'):
        pylons.controllers.util.abort(401)
    if user_is is not None:
       if unicode(pylons.session.get('id')) != unicode(user_is) and not pylons.session['admin']:
           pylons.controllers.util.abort(403)
    elif not pylons.session.get(rights):
        pylons.controllers.util.abort(403)

def requirelogin(rights="admin", user_is=None):
    if not pylons.session.has_key('user'):
        pylons.controllers.util.abort(401)

def flashmsg(text):
    pylons.session['flash'] = text
    pylons.session.save()

def strong (text):
    '''Оборачивает текст в тег <strong>.\n\nПрименение: h.strong(текст)'''
    return literal("<strong>") + unicode(text) + literal("</strong>")

def tr (i=1):
    if i%2:
        text = "odd"
    else:
        text = "even"
    return literal("<tr class=\"") + unicode(text) + literal("\">")

def normname (surname, name, patronymic):
    """Эта функция объявлена устаревшей! Пожалуйста, по возможности используйте h.name()\n\nВозвращает строку вида: Фамилия И. О.\n\nПрименение: h.normname(фамилия, имя, отчество)"""
    return (surname or '') + ' ' + (name[0] or '') + '. ' + (patronymic[0] or '') + '.'

def name (user):
    """Возвращает строку вида: Фамилия И. О. Или логин.\n\nПрименение: h.name(персона)\n\nГде персона - объект класса model.Person"""
    if len(user.surname) and len(user.name) and len(user.patronymic):
        return user.surname + ' ' + user.name[0] + '. ' + user.patronymic[0] + '.'
    else:
        return user.login

def orderactlink (order):
    '''Возвращает HTML-ссылку на действие, которое пользователь может совершить с заявкой\n\nПрименение: h.orderactlink(заявка)\n\nГде заявка - объект класса model.Order'''
    if have_role('appointer') and order.status_id==1:
        return link_to(u'Взять себе', url_for(controller='order', action='takerequest', id=order.id, show=None))
    elif pylons.session.has_key('division') and order.cust_id == pylons.session['division'] and order.status_id==3:
        return link_to(u'Подтвердить выполнение', url_for(controller='action', action='approve', id=order.id, show=None))
    elif (
        have_role('appointer')
        and order.status_id not in [1,4,6]
        and pylons.session.has_key('division')
        and order.perf_id == pylons.session['division']
        ) or have_role('admin'):
        return link_to(u'Изменить статус', url_for(controller='action', action='choose', id=order.id, show=None))
    elif can_complain(order):
        return link_to(u'Пожаловаться', url_for(controller='action', action='complain', id=order.id, show=None))
    else:
        return ''

def humandatetime(ts=now):
    '''Возвращает строку с "человекопонятной" меткой времени в стиле "2009.11.18 в 9:49".\n\nПрименение: h.humandatetime(время)\n\nГде время - питоновская метка времени.'''
    return ts.strftime("%Y.%m.%d")+ u" в " + ts.strftime("%H:%M")

def refresh_account (id=None, operator=None):
    """Так как вся информация о посетителе хранится в сессии, то при в этой функции эта информация перезагружается, чтобы быть актуальной. И права доступа тоже. Стоит помещать в __before__ контроллеров."""
        # Main info
    if id is not None:
        person = meta.Session.query(model.Person).get(int(id))
    elif id is None and pylons.session.has_key('id'):
        person = meta.Session.query(model.Person).get(int(pylons.session['id']))
    else:
        person = None
    if person is None:
        if pylons.session.has_key('flash'):
            flash = pylons.session.get('flash')
            pylons.session.clear()
            pylons.session['flash'] = flash
        else:
            pylons.session.clear()
        pylons.session['guest'] = True
        pylons.session.save()
        return
    pylons.session['user'] = person.login
    pylons.session['name'] = name(person)
    pylons.session['id'] = person.id
    pylons.session['division'] = person.div_id
    # Раздача прав доступа
    pylons.session['creator'] = person.creator
    pylons.session['performer'] = person.performer
    pylons.session['admin'] = person.admin
    pylons.session['appointer'] = person.appointer
    pylons.session['responsible'] = person.responsible
    pylons.session['chief'] = person.chief
    pylons.session['operator'] = person.operator
    pylons.session['preferences'] = person.preferences
    if operator: pylons.session['operator_id'] = operator
    #else:        pylons.session['operator_id'] = False
    pylons.session.save()
    return

def have_role (role="creator"):
    """Есть ли такое право (роль) у пользователя."""
    if pylons.session.has_key(role) and pylons.session[role]:
        return True
    else:
        return False

def can_complain (order):
    """Проверяет, может ли жаловаться на заявку посетитель. Это должен быть человек из подразделения, создавшего заявку, должен обладать правом создавать заявки (или быть ответственным или начальником) и с момента создания заявки должен пройти день, а с момента её принятия - три дня. Заявка не должна уже быть выполнена!"""
    if (have_role('responsible') or have_role('chief') or have_role('creator')) and pylons.session.has_key('division') and order.cust_id == pylons.session['division'] and order.status_id!=4:
        if order.status_id == 1:
            if (now() - order.created).days >= 1: # 1
                return True
            else:
                return False
        elif order.status_id == 3:
            return True
        else:
            action = meta.Session.query(model.Action).filter_by(order_id=order.id).filter_by(status_id=2).first()
            if action is not None and (now() - action.created).days >= 3: # 3
                return True
            else:
                return False
    else:
        return False

def checkorder (id=None):
    if id is None:
        pylons.controllers.util.abort(404)
    order = meta.Session.query(model.Order).get(int(id))
    if order is None:
        pylons.controllers.util.abort(404)
    elif order.deleted:
        pylons.controllers.util.abort(410)
    return order

def checkuser (id=None):
    if id is None:
        pylons.controllers.util.abort(404)
    user = meta.Session.query(model.Person).get(int(id))
    if user is None:
        pylons.controllers.util.abort(404)
    elif user.deleted:
        pylons.controllers.util.abort(410)
    return user

def checkdiv (id=None):
    if id is None:
        pylons.controllers.util.abort(404)
    div = meta.Session.query(model.Division).get(int(id))
    if div is None:
        pylons.controllers.util.abort(404)
    elif div.deleted:
        pylons.controllers.util.abort(410)
    return div

def ago (time):
    '''Вычисляет разность времени между сейчас и переданным временем'''
    diff = now()-time;
    '''weeks, days = divmod(diff.days, 7)
    minutes, seconds = divmod(diff.seconds, 60)
    hours, minutes = divmod(minutes, 60)
    if weeks and days:
        return u"%s и %s назад" % (get_plural(weeks, u"неделя, недели, недель"), get_plural(days, u"день, дня, дней"))
    elif days and hours:
        return u"%s и %s назад" % (get_plural(days, u"день, дня, дней"), get_plural(hours, u"час, часа, часов"))   
    elif hours and minutes:
        return u"%s и %s назад" % (get_plural(hours, u"час, часа, часов"), get_plural(minutes, u"минуту, минуты, минут"))
    elif minutes and seconds:
        return u"%s и %s назад" % (get_plural(minutes, u"минуту, минуты, минут"), get_plural(seconds, u"секунду, секунды, секунд"))
    elif weeks:
        return u"%s назад" % get_plural(weeks, u"неделя, недели, недель")
    elif days:
        return u"%s назад" % get_plural(days, u"день, дня, дней")   
    elif hours:
        return u"%s назад" % get_plural(hours, u"час, часа, часов")  
    elif minutes:
        return u"%s назад" % get_plural(minutes, u"минуту, минуты, минут")
    elif seconds:
        return u"%s назад" % get_plural(seconds, u"секунду, секунды, секунд")
    else:
        return u"Только что"'''
    return pytils.dt.distance_of_time_in_words(now()-diff, accuracy=2)

