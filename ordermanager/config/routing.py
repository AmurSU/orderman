# -*- coding: utf-8 -*-
"""Routes configuration

The more specific and detailed routes should be defined first so they
may take precedent over the more generic routes. For more information
refer to the routes manual at http://routes.groovie.org/docs/
"""
from pylons import config
from routes import Mapper

def make_map(config):
    """Create, configure and return the routes Mapper"""
    map = Mapper(directory=config['pylons.paths']['controllers'],
                 always_scan=config['debug'], explicit=True)
    map.explicit = True
    map.minimization = False
    
    # The ErrorController route (handles 404/500 error pages); it should
    # likely stay at the top, ensuring it can always be resolved
    map.connect('/error/{action}', controller='error')
    map.connect('/error/{action}/{id}', controller='error')


    # SOME NAMED ROUTES
    # Списки  
    map.connect ("startpage", "/", controller="main", action="index")
    map.connect ("orderlist", "/orders", controller="order", action="list")
    map.connect ("userlist", "/users", controller="usercontrol", action="list")
    map.connect ("divisionlist", "/divisions", controller="division", action="list")

    # Заявки
    map.connect ("order", "/order/{id}", controller="order", action="view", requirements = {'id': '\d+'})
    map.connect ("order", "/order/{id}/{action}", controller="order", requirements = {'id': '\d+'})

    # Пользователи
    map.connect ("user", '/user/{id}', controller="usercontrol", action="view", requirements = {'id': '\d+'})
    map.connect (None, '/user/{action}', controller="usercontrol")
    map.connect (None, '/user/{id}/allorders', controller="usercontrol", action="view", showallorders=True, requirements = {'id': '\d+'})
    map.connect (None, '/user/{id}/{action}', controller="usercontrol", requirements = {'id': '\d+'})
    # И их список
    #map.redirect("/users/", '/users', _redirect_code='301 Moved Permanently')
    #map.redirect("/user/list", '/users', _redirect_code='301 Moved Permanently')
    map.connect (None, '/user/{login}', controller="usercontrol", action="view", requirements = {'login': '\W+'})

    # Список заявок
    #map.redirect("/orders/", '/orders', _redirect_code='301 Moved Permanently')
    #map.redirect("/order/list", '/orders', _redirect_code='301 Moved Permanently')
    map.connect (None, "/orders/page{page}",
        controller="order", action="list",
        requirements = {'page': '\d+'}
    )
    map.connect (None, "/orders/{upcat}",
        controller="order", action="list",
        requirements = {'upcat': '\w+'}                                
    )
    map.connect (None, "/orders/{upcat}/page{page}",
        controller="order", action="list",
        requirements = {'page': '\d+', 'upcat': '\w+'}                                
    )
    map.connect (None, "/orders/category={cat};work={work};status={status}",
        controller="order", action="list",
        requirements = {'cat': '\w+', 'work': '\w+', 'status': '\d+'},
        upcat = None, cat = 'any', work = 'any', status=None                                 
    )
    map.connect (None, "/orders/category={cat};work={work};status={status}/page{page}",
        controller="order", action="list",
        requirements = {'page': '\d+', 'cat': '\w+', 'work': '\w+', 'status': '\d+'},
        upcat = None, cat = 'any', work = 'any', status=None                              
    )
    map.connect (None, "/orders/{upcat}/category={cat};work={work};status={status}",
        controller="order", action="list",
        requirements = {'upcat': '\w+', 'cat': '\w+', 'work': '\w+', 'status': '\d+'},
        upcat = 'any', cat = 'any', work = 'any', status=None                               
    )
    map.connect (None, "/orders/{upcat}/category={cat};work={work};status={status}/page{page}",
        controller="order", action="list",
        requirements = {'page': '\d+', 'upcat': '\w+', 'cat': '\w+', 'work': '\w+', 'status': '\d+'},
        upcat = 'any', cat = 'any', work = 'any', status=None                                
    )

    # Подразделения
    map.connect ("/division/{id}/insertusers", controller="division", action="insertusers", requirements = {'id': '\d+'})
    #map.redirect("/division", '/division/list', _redirect_code='301 Moved Permanently')
    #map.redirect("/division/", '/division/list', _redirect_code='301 Moved Permanently')

    #map.redirect("/main", '/', _redirect_code='301 Moved Permanently')
    #map.redirect("/main/", '/', _redirect_code='301 Moved Permanently')
    #map.redirect("/main/index", '/', _redirect_code='301 Moved Permanently')
    #map.redirect("/main/index/", '/', _redirect_code='301 Moved Permanently')
    #map.redirect("/{controller}/", "/{controller}")
    #map.redirect("/{controller}/index", "/{controller}")
    
    map.connect ("/{controller}", action="index")
    
    # Ну и общее для всех
    map.connect (None, '/{controller}/{id}', action="view", requirements = {'id': '\d+'})
    map.connect (None, '/{controller}/{id}', action="view", requirements = {'id': '\d+'})
    map.connect (None, '/{controller}/{id}/{action}', requirements = {'id': '\d+'})

    map.connect (None, '/{controller}s', action="list")
    map.connect (None, '/{controller}/{action}')
    map.connect (None, '/{controller}/{action}/{id}')
    
    return map
