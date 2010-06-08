# -*- coding: utf-8 -*-
"""Routes configuration

The more specific and detailed routes should be defined first so they
may take precedent over the more generic routes. For more information
refer to the routes manual at http://routes.groovie.org/docs/
"""
from pylons import config
from routes import Mapper

def make_map():
    """Create, configure and return the routes Mapper"""
    map = Mapper(directory=config['pylons.paths']['controllers'],
                 always_scan=config['debug'], explicit=False)
    map.minimization = False
    
    # The ErrorController route (handles 404/500 error pages); it should
    # likely stay at the top, ensuring it can always be resolved
    map.connect('/error/{action}', controller='error')
    map.connect('/error/{action}/{id}', controller='error')

    # CUSTOM ROUTES HERE
    map.connect ("/", controller="main", action="index")
    map.redirect("/main", '/', _redirect_code='301 Moved Permanently')
    map.redirect("/main/", '/', _redirect_code='301 Moved Permanently')
    map.redirect("/main/index", '/', _redirect_code='301 Moved Permanently')
    map.redirect("/main/index/", '/', _redirect_code='301 Moved Permanently')
    map.connect ("/{controller}", action="index")
    
    # Пользователи
    map.connect ('/user/{id}', controller="usercontrol", action="view", requirements = {'id': '\d+'})
    map.connect ('/user/{id}/allorders', controller="usercontrol", action="view", showallorders=True, requirements = {'id': '\d+'})
    map.connect ('/user/{id}/{action}', controller="usercontrol", requirements = {'id': '\d+'})
    # И их список
    map.connect ('/users', controller="usercontrol", action="list")
    map.connect ('/users/{show}', controller="usercontrol", action="list")
    map.connect ('/user/{action}', controller="usercontrol")
    map.redirect("/users/", '/users', _redirect_code='301 Moved Permanently')
    map.redirect("/user/list", '/users', _redirect_code='301 Moved Permanently')
    map.connect ('/user/{login}', controller="usercontrol", action="view", requirements = {'login': '\W+'})

    # Список заявок
    map.redirect("/orders/", '/orders', _redirect_code='301 Moved Permanently')
    map.redirect("/order/list", '/orders', _redirect_code='301 Moved Permanently')
    map.connect ("/orders/page{page}",
        controller="order", action="list",
        requirements = {'page': '\d+'}
    )
    map.connect ("/orders/{upcat}",
        controller="order", action="list",
        requirements = {'upcat': '\w+'}                                
    )
    map.connect ("/orders/{upcat}/page{page}",
        controller="order", action="list",
        requirements = {'page': '\d+', 'upcat': '\w+'}                                
    )
    map.connect ("/orders/category={cat};work={work};status={status}",
        controller="order", action="list",
        requirements = {'cat': '\w+', 'work': '\w+', 'status': '\d+'},
        cat = 'any', work = 'any', status=None                                 
    )
    map.connect ("/orders/category={cat};work={work};status={status}/page{page}",
        controller="order", action="list",
        requirements = {'page': '\d+', 'cat': '\w+', 'work': '\w+', 'status': '\d+'},
        cat = 'any', work = 'any', status=None                              
    )
    map.connect ("/orders/{upcat}/category={cat};work={work};status={status}",
        controller="order", action="list",
        requirements = {'upcat': '\w+', 'cat': '\w+', 'work': '\w+', 'status': '\d+'},
        upcat = 'any', cat = 'any', work = 'any', status=None                               
    )
    map.connect ("/orders/{upcat}/category={cat};work={work};status={status}/page{page}",
        controller="order", action="list",
        requirements = {'page': '\d+', 'upcat': '\w+', 'cat': '\w+', 'work': '\w+', 'status': '\d+'},
        upcat = 'any', cat = 'any', work = 'any', status=None                                
    )
    map.connect("/orders/filter", controller="order", action="filter")
    map.connect("/orders/filter/{upcat}", controller="order", action="filter")
        
    # Подразделения
    map.connect ("/division/{id}/insertusers", controller="division", action="insertusers", requirements = {'id': '\d+'})
    #map.redirect("/division", '/division/list', _redirect_code='301 Moved Permanently')
    #map.redirect("/division/", '/division/list', _redirect_code='301 Moved Permanently')
    
    # Ну и общее для всех
    map.connect ('/{controller}/{id}', action="view", requirements = {'id': '\d+'})
    map.connect ('/{controller}/{id}', action="view", requirements = {'id': '\d+'})
    map.connect ('/{controller}/{id}/{action}', requirements = {'id': '\d+'})
    #map.redirect("/{controller}/", "/{controller}")
    #map.redirect("/{controller}/index", "/{controller}")
    map.connect ('/{controller}s', action="list")
    map.connect ('/{controller}/{action}')
    map.connect ('/{controller}/{action}/{id}')
    
    return map
