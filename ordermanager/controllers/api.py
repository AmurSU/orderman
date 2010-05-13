import logging

from pylons import request, response, session, tmpl_context as c
from pylons.controllers.util import abort, redirect_to

from ordermanager.lib.base import BaseController, render
import ordermanager.lib.helpers as h

import calendar
import ordermanager.model as model
import ordermanager.model.meta as meta

log = logging.getLogger(__name__)

from sqlalchemy.orm import eagerload

class ApiController(BaseController):

    def index(self):
        # Return a rendered template
        #return render('/api.mako')
        # or, return a response
        return 'Hello World'
        
    def orderstat (self, ctype="text/html"):
        response.content_type = 'text/plain'
        result = ""
        orders = meta.Session.query(model.Order).filter_by(deleted=False).order_by(model.Order.created).options(eagerload('actions'))
        for order in orders:
            applied = order.actions.filter(model.Action.status_id==2).order_by(model.Action.created).options(eagerload('performers')).first()
            markdone = order.actions.filter(model.Action.status_id==3).order_by(model.sql.desc(model.Action.created)).options(eagerload('performers')).first()
            #applied = meta.Session.query(model.Action).filter_by(order_id=order.id).\
            #    filter(model.Action.status_id==2).order_by(model.Action.created).first()
            #markdone = meta.Session.query(model.Action).filter_by(order_id=order.id).\
            #    filter(model.Action.status_id==3).order_by(model.sql.desc(model.Action.created)).options(eagerload('performers')).first()
            #for act in order.actions:
            #    if act.status_id == 2:
            #        applied = act
            #        break
            #    else:
            #        applied = None
            #for act in reversed(order.actions):
            #    if act.status_id == 3:
            #        markdone = act
            #        break
            #    else:
            #        markdone = None                    
            result += unicode(order.id) +" "+ unicode(calendar.timegm(order.created.timetuple())) + " "
            for act in [applied, markdone]:
                try:
                    result += unicode(calendar.timegm(act.created.timetuple())) + " "
                except AttributeError:            
                    result += "None "
            if markdone is not None:
                result += "\"" + u", ".join([h.name(person) for person in markdone.performers]) + "\"" + "\n"
            elif applied is not None:
                result += "\"" + u", ".join([h.name(person) for person in applied.performers]) + "\"" + "\n"
            else:
                result += "\"None\"\n"
        return result 
            
