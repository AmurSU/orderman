# -*- coding: utf-8 -*-
"""Setup the OrderManager application"""
import logging

from ordermanager.config.environment import load_environment
from ordermanager.model import meta
import ordermanager.model as model

from hashlib import md5

log = logging.getLogger(__name__)

def setup_app(command, conf, vars):
    """Place any commands to setup ordermanager here"""
    load_environment(conf.global_conf, conf.local_conf)

    # Create the tables if they don't already exist
    log.info(u"Удаление и создание таблиц...")
    meta.metadata.drop_all(bind=meta.engine)
    meta.metadata.create_all(bind=meta.engine)

    # Create initial configuration
    div = meta.Session.query(model.Division).get(1)
    if not div:
        log.info(u"Создание администрирующего подразделения...")
        div = model.Division()
        div.id = 1
        div.title = u'Администраторская'
        meta.Session.add(div)
        meta.Session.commit()

    admin = meta.Session.query(model.Person).get(1)
    creating = not bool(admin)
    if creating:
        log.info(u"Добавление пользователя-администратора...")
        admin = model.Person()
        admin.id = 1
        admin.name = u'Администратор'
        admin.surname = u'Администратор'
        admin.patronymic = u'Администратор'
    else:
        log.info(u"Исправление пользователя-администратора...")
    admin.login = u'admin'
    admin.password = md5(u"Random!").hexdigest()
    admin.div_id = 1
    admin.admin = True
    admin.chief = True
    admin.responsible = True
    if creating:
        meta.Session.add(admin)
    meta.Session.commit()
    log.info(u"Логин администратора: %s ; пароль: %s ;" % (admin.login, u"Random!") )

    log.info(u"Создание типов (надкатегорий)...")
    upcats = [
        [1, u"IT",        u"it"],
        [2, u"Электрика", u"electrics"]
    ]
    for u in upcats:
        uc = model.UpperCategory()
        uc.id, uc.title, uc.url_text = u
        meta.Session.add(uc)
    meta.Session.commit()

    log.info(u"Создание категорий работ...")
    categories = [
        # id,           title,                    url_text,   upper_category
        [1,  u"Не знаю - ничего не работает!",  u"unknown",         None],
        [2,  u"Операционная система",           u"os",              1   ],
        [3,  u"Офисные программы",              u"officesoft",      1   ],
        [4,  u"Антивирус",                      u"antivirus",       1   ],
        [5,  u"Вирусы",                         u"virus",           1   ],
        [6,  u"Другое программное обеспечение", u"othersoft",       1   ],
        [7,  u"Системный блок",                 u"systemunit",      1   ],
        [8,  u"Монитор",                        u"monitor",         1   ],
        [9,  u"Клавиатура и мышь",              u"inputdevices",    1   ],
        [10, u"Принтер/сканер и др. периферия", u"peripherals",     1   ],
        [11, u"Ксерокс (копир)",                u"copier",          1   ],
        [12, u"Картридж",                       u"cartridge",       1   ],
        [13, u"Веб-сайт АмГУ",                  u"website",         1   ],
        [14, u"Сеть, Почта, Интернет",          u"networking",      1   ],
        [15, u"Телефон",                        u"phone",           1   ],
        [16, u"Другое",                         u"other",           None],
        [17, u"Диспетчер заявок",               u"ordermanager",    1   ],
        [18, u"Проводка (также щиты, розетки)", u"wiring",          2   ],
        [19, u"Лампы, освещение",               u"lamps",           2   ],
        [20, u"Электрооборудование",            u"electricsystems", 2   ]
    ]
    for category in categories:
        cat = model.Category()
        cat.id, cat.title, cat.url_text, cat.upcat_id = category
        meta.Session.add(cat)
    meta.Session.commit()

    log.info(u"Создание видов работ...")
    works = [
        [u"Неисправность",                  u"repair"    ],
        [u"Настройка",                      u"customize" ],
        [u"Установка",                      u"install"   ],
        [u"Приобретение (нужна служебка)",  u"purchase"  ],
        [u"Дефектовать",                    u"defect"    ],
        [u"Информация",                     u"inform"    ],
        [u"Другая работа",                  u"other"     ]
    ]
    for i,item in enumerate(works):
        work = model.Work()
        work.id = i+1
        work.title, work.url_text = item
        meta.Session.add(work)
    meta.Session.commit()

    log.info(u"Создание статусов...")
    slist = [
         [1, u"Заявка свободна", 1],
         [2, u"Принято", 2],
         [3, u"Заявлено о выполнении", 3],
         [4, u"Выполнено", 4],
         [5, u"Отказано", 1],
         [6, u"Подана претензия", 6],
         [7, u"Передано другому исполнителю", 2],
         [8, u"Ожидание заказчика", 8],
         [9, u"Ожидание отдела закупок", 9],
         [10,u"Ожидание ремонта по гарантии", 10],
         [11,u"Заявка создана", 1],
         [12,u"Заявка создана оператором", 1]
    ]
    for item in slist:
        status = model.Status()
        status.id = item[0]
        status.title = item[1]
        status.redirects = item[2]
        meta.Session.add(status)
    meta.Session.commit()

    log.info(u"Успешно установлено.")
