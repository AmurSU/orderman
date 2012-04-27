# -*- coding: utf-8 -*-
"""The application's model objects"""
import sqlalchemy as sql
from sqlalchemy import orm

from ordermanager.model import meta

import datetime
from sqlalchemy import schema, types

# инициализация модели
def init_model(engine):
    """Call me before using any of the tables or classes in the model"""
    meta.Session.configure(bind=engine)
    meta.Session.configure(expire_on_commit=True)
    meta.engine = engine

# Возвращает текущее время и дату
def now():
    return datetime.datetime.now()


##### ТАБЛИЦЫ #####

# Таблица заявок
orders_table = schema.Table ('orders', meta.metadata,
    # Искусственный ключ - уникальный номер заявки
    schema.Column('id', types.Integer,
        schema.Sequence('orders_seq_id', optional=True), primary_key=True),
    # Более подробная информация о заявке (название колонки не соответствует назначению по историческим причинам)
    schema.Column('title', types.UnicodeText(), default=""),
    # Кастомное место выполнения заявки
    schema.Column('place', types.Unicode(255), default=""),
    # Что нужно сделать? (починить, установить, купить)
    schema.Column('work_id', types.Integer, schema.ForeignKey("works.id")),
    # Категория, по которой проходит заявка (компьютеры, лампочки, интернет)
    schema.Column('cat_id', types.Integer, schema.ForeignKey("categories.id")),
    # Надкатегория, к которой относится заявка (IT, электрика)
    schema.Column('upcat_id', types.Integer, schema.ForeignKey("upcategories.id")),
    # От какого подразделения исходит заявка
    schema.Column('cust_id', types.Integer, schema.ForeignKey("divisions.id")),
    # Какое подразделение выполняет заявку
    schema.Column('perf_id', types.Integer), #, schema.ForeignKey("divisions.id")),
    # Сделана ли заявка
    schema.Column('status_id', types.Integer, schema.ForeignKey("statuses.id")),
    # Когда была сделана заявка
    schema.Column('doneAt', types.DateTime()),
    # Трудоёмкость заявки в человеко-часах
    schema.Column('workload', types.Numeric(precision=5, scale=1), default="1.0"),
    # До какого времени заявка должна быть сделана
    schema.Column('expires', types.DateTime()),
    # Служебные данные о записи
    schema.Column('deleted', types.Boolean, default=False),
    schema.Column('created', types.DateTime(), default=now),
    schema.Column('edited', types.TIMESTAMP())
)

# Таблица действий (производимых над заявками)
actions_table = schema.Table ('actions', meta.metadata,
    schema.Column('id', types.Integer,
        schema.Sequence('actions_seq_id', optional=True), primary_key=True),
    # Заявка, которой касается действие
    schema.Column('order_id', types.Integer, schema.ForeignKey("orders.id")),
    # Статус, придаваемы
    schema.Column('status_id', types.Integer, schema.ForeignKey("statuses.id")),
    # Какое подразделение производит действие
    schema.Column('div_id', types.Integer, schema.ForeignKey("divisions.id")),
    # Комментарий
    schema.Column('description', types.UnicodeText()),
    # До какого времени будет выполняться
    schema.Column('expires', types.DateTime()),
    # Служебные данные о записи
    schema.Column('created', types.DateTime(), default=now),
    schema.Column('edited', types.TIMESTAMP())
)

# Таблица подразделений
divisions_table = schema.Table ('divisions', meta.metadata,
    schema.Column('id', types.Integer,
        schema.Sequence('divisions_seq_id', optional=True), primary_key=True),
    # Название подразделения
    schema.Column('title', types.Unicode(255), nullable="false"),
    # Некоторое описание
    schema.Column('description', types.UnicodeText()),
    # Местонахождение подразделения
    schema.Column('address', types.Unicode(255)),
    # Реквизиты для связи
    schema.Column('email', types.Unicode(255)),
    schema.Column('phone', types.Unicode(32)),
    # Служебные данные о записи
    schema.Column('deleted', types.Boolean, default=False),
    schema.Column('created', types.DateTime(), default=now),
    schema.Column('edited', types.TIMESTAMP())
)

# Таблица исполнителей (и вообще людей)
people_table = schema.Table ('people', meta.metadata,
    schema.Column('id', types.Integer,
        schema.Sequence('people_seq_id', optional=True), primary_key=True),
    # Учётные данные
    schema.Column('login', types.Unicode(64), nullable="false"),
    schema.Column('password', types.String(32), nullable="false"),
    # Данные о персоне
    schema.Column('surname', types.Unicode(64)),
    schema.Column('name', types.Unicode(64)),
    schema.Column('patronymic', types.Unicode(64)),
    # Реквизиты для связи
    schema.Column('email', types.Unicode(255)),
    schema.Column('phone', types.Unicode(32)),
    # В каком подразделении состоит
    schema.Column('div_id', types.Integer, schema.ForeignKey("divisions.id")),
    # Права доступа
    schema.Column('creator', types.Boolean, default="true"), # Может создавать заявки
    schema.Column('performer', types.Boolean, default="false"), # Может выполнять заявки
    schema.Column('appointer', types.Boolean, default="false"), # Может брать заявки и назначать исполнителей
    schema.Column('responsible', types.Boolean, default="false"), # Ответственный (для отчёта и статистики)
    schema.Column('chief', types.Boolean, default="false"), # Начальник (для отчёта и статистики)
    schema.Column('operator', types.Boolean, default="false"), # Может создавать заявки от имени других
    schema.Column('admin', types.Boolean, default="false"), # Может администрировать всё
    # Здесь хранятся настройки
    schema.Column('preferences', types.PickleType()),
    # Служебные данные о записи
    schema.Column('deleted', types.Boolean, default=False),
    schema.Column('created', types.DateTime(), default=now),
    schema.Column('edited', types.TIMESTAMP())
)

# Таблица статусов заявок
statuses_table = schema.Table ('statuses', meta.metadata,
    schema.Column('id', types.Integer,
        schema.Sequence('statuses_seq_id', optional=True), primary_key=True),
    # Название
    schema.Column('title', types.Unicode(255), nullable="false"),
    schema.Column('url_text', types.Unicode(255), nullable="false"),
    # В какой статус переводит заявку
    schema.Column('redirects', types.Integer),
    # Количество заявок, находящихся сейчас в данном статусе
    schema.Column('ordercount', types.Integer, default=0),
    # Приоритет для сортировки статусов в выпадающем списке в GUI
    schema.Column('gui_priority', types.Integer),
    # Служебные данные о записи
    schema.Column('deleted', types.Boolean, default=False),
    schema.Column('created', types.DateTime(), default=now),
    schema.Column('edited', types.TIMESTAMP())
)

# Таблица категорий заявок
categories_table = schema.Table ('categories', meta.metadata,
    schema.Column('id', types.Integer,
        schema.Sequence('categories_seq_id', optional=True), primary_key=True),
    # Название
    schema.Column('title', types.Unicode(255), nullable="false"),
    schema.Column('upcat_id', types.Integer, schema.ForeignKey('upcategories.id')),
    schema.Column('url_text', types.Unicode(255), nullable="false"),
    # Служебные данные о записи
    schema.Column('deleted', types.Boolean, default=False),
    schema.Column('created', types.DateTime(), default=now),
    schema.Column('edited', types.TIMESTAMP())
)

# Таблица "верхних" категорий заявок (железо, электрика)
upcategories_table = schema.Table ('upcategories', meta.metadata,
    schema.Column('id', types.Integer, 
        schema.Sequence('categories_seq_id', optional=True), primary_key=True),
    # Название
    schema.Column('title', types.Unicode(255), nullable="false"),
    schema.Column('url_text', types.Unicode(255), nullable="false"),
    # Служебные данные о записи
    schema.Column('deleted', types.Boolean, default=False),
    schema.Column('created', types.DateTime(), default=now),
    schema.Column('edited', types.TIMESTAMP())
) 

# Таблица видов работ заявок
works_table = schema.Table ('works', meta.metadata,
    schema.Column('id', types.Integer,
        schema.Sequence('works_seq_id', optional=True), primary_key=True),
    # Название
    schema.Column('title', types.Unicode(255), nullable="false"),
    schema.Column('url_text', types.Unicode(255), nullable="false"),
    # Служебные данные о записи
    schema.Column('deleted', types.Boolean, default=False),
    schema.Column('created', types.DateTime(), default=now),
    schema.Column('edited', types.TIMESTAMP())
)

# Таблица автоназначений заявок
assigns_table = schema.Table ('assigns', meta.metadata,
    schema.Column('id', types.Integer,
        schema.Sequence('assigns_seq_id', optional=True), primary_key=True),
    # Какой категории
    schema.Column('cat_id', types.Integer, schema.ForeignKey("categories.id")),
    schema.Column('div_id', types.Integer, schema.ForeignKey("divisions.id")),
    # Пояснение
    schema.Column('description', types.Unicode(255)),
    # Служебные данные о записи
    schema.Column('created', types.DateTime(), default=now)
)

# Таблица инвентарных номеров
inventory_table = schema.Table ('inventory', meta.metadata,
    schema.Column('id', types.Integer,
        schema.Sequence('inventory_seq_id', optional=True), primary_key=True),
    # Какой категории
    schema.Column('type_id', types.Integer), #, schema.ForeignKey("categories.id")),
    schema.Column('title', types.Unicode(255)), # Наименование
    schema.Column('year', types.Integer), # Год приобретения
    schema.Column('cost', types.Integer), # Стоимость
    schema.Column('sw_id', types.Integer), #schema.ForeignKey("software.id")),
    schema.Column('hw_id', types.Integer), #schema.ForeignKey("hardware.id")),    
    schema.Column('description', types.Unicode(255)), # Примечание, пояснение
    # Служебные данные о записи
    schema.Column('deleted', types.Boolean, default=False),
    schema.Column('created', types.DateTime(), default=now)
)

# Вспомогательная таблица связи многие-ко-многим между таблицей действий и исполнителей
actperf_table = schema.Table('actionperformers', meta.metadata,
    schema.Column('action_id', types.Integer, schema.ForeignKey('actions.id'), primary_key=True),
    schema.Column('person_id', types.Integer, schema.ForeignKey('people.id'), primary_key=True),
)

# Вспомогательная таблица связи многие-ко-многим между таблицей заявок и инвентарных номеров
orderinvs_table = schema.Table('orderinventories', meta.metadata,
    schema.Column('order_id', types.Integer, schema.ForeignKey('orders.id'), primary_key=True),
    schema.Column('inv_id', types.Integer, schema.ForeignKey('inventory.id'), primary_key=True),
)

# Таблица, содержащая в себе текущих или конечных исполнителей заявки.
# Большей частью для денормализации БД и ускорения. Так же сделает многие вещи проще.
orderperf_table = schema.Table('orderperformers', meta.metadata,
    schema.Column('order_id', types.Integer, schema.ForeignKey('orders.id'), primary_key=True),
    schema.Column('person_id', types.Integer, schema.ForeignKey('people.id'), primary_key=True),
)

# Таблица, содержащая в себе людей-заказчиков заявки.
# Большей частью для денормализации БД и ускорения. Так же сделает многие вещи проще.
ordercust_table = schema.Table('ordercustomers', meta.metadata,
    schema.Column('order_id', types.Integer, schema.ForeignKey('orders.id'), primary_key=True),
    schema.Column('person_id', types.Integer, schema.ForeignKey('people.id'), primary_key=True),
)

##### КЛАССЫ #####

class Order(object):
    pass

class Action(object):
    pass

class Division(object):
    pass

class Person(object):
    pass

class Status(object):
    pass

class Category(object):
    pass

class UpperCategory(object):
    pass

class Work(object):
    pass

class Assign(object):
    pass

class Inventory(object):
    pass

##### СЛУЖЕБНЫЕ ВЕЩИ #####

# Расширение, отслеживающее изменение статуса заявки и обновляющее статистику
# Чтобы расширение работало, НЕ ИСПОЛЬЗУЙТЕ код вида order.status_id = 2
# Вместо этого используйте код вида order.status = meta.Session.query(model.Status).get(2)
class OrderChangeStatus(orm.interfaces.AttributeExtension): 
    def set(self, state, value, oldvalue, initiator): 
        value.ordercount += 1
        if oldvalue:
            oldvalue.ordercount -= 1
        return value 

##### СОЕДИНЕНИЕ МОДЕЛИ #####

orm.mapper(Order, orders_table,
    properties = {
        'actions':  orm.relation(Action, backref=orm.backref('order', lazy='dynamic'), cascade="all", lazy="dynamic", order_by=actions_table.c.created),
        'customer': orm.relation(Division, cascade=None, uselist=False, backref='createdorders', lazy=False,
            primaryjoin  = divisions_table.c.id==orders_table.c.cust_id,
            foreign_keys = [divisions_table.c.id]  
        ),
        'performer':orm.relation(Division, cascade=None, uselist=False, backref='performingorders',
            primaryjoin =  divisions_table.c.id==orders_table.c.perf_id,
            foreign_keys = [divisions_table.c.id]
        ),
        'status':   orm.relation(Status, cascade=None, uselist=False, lazy=False, backref="orders",
            extension=OrderChangeStatus()),
        'work':     orm.relation(Work, cascade=None, uselist=False, lazy=False),
        'category': orm.relation(Category, cascade=None, uselist=False, lazy=False),
        'upper_category':orm.relation(UpperCategory, cascade=None, lazy=False, backref=orm.backref("orders", cascade="all")),
        'inventories': orm.relation (Inventory, secondary=orderinvs_table, backref=orm.backref("orders", cascade=None), cascade=None),
        'customers': orm.relation (Person, secondary=ordercust_table, cascade=None,
            backref=orm.backref("created_orders", cascade=None)
        ),
        'performers': orm.relation (Person, secondary=orderperf_table, cascade=None,
            backref=orm.backref("performing_orders", cascade=None)
        ),
    }
)
orm.mapper(Action, actions_table, properties={
    'performers': orm.relation (Person, secondary=actperf_table, backref=orm.backref("actions", cascade=None), cascade="all"),
    'division'  : orm.relation (Division, cascade=None, uselist=False),
    'status'    : orm.relation (Status, cascade=None, uselist=False)
})
orm.mapper(Division, divisions_table, properties={
   'people' : orm.relation(Person, backref=orm.backref("division", uselist=False, cascade=None), cascade=None), 
   'orders' : orm.relation(Order, cascade="all"),
   'actions': orm.relation(Action, cascade="all")
})
orm.mapper(Person, people_table)

orm.mapper(Status, statuses_table, properties={
   'actions':orm.relation(Action)
})
orm.mapper(Category, categories_table, properties={
   'orders':orm.relation(Order, cascade=None),
   'upper_category':orm.relation(UpperCategory, cascade=None, backref=orm.backref("categories", cascade="all"))
})
orm.mapper(UpperCategory, upcategories_table)

orm.mapper(Work, works_table, properties={
   'orders':orm.relation(Order, cascade=None),
})
orm.mapper(Assign, assigns_table, properties={
    'division':orm.relation(Division, cascade=None, uselist=False, backref="assigned"),
    'category':orm.relation(Category, cascade=None, uselist=False, backref="assigned"),
})
orm.mapper(Inventory, inventory_table)

