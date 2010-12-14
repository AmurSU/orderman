# Launch in the paster shell

import ordermanager.model as model
import ordermanager.model.meta as meta

orders = meta.Session.query(model.Order).all()
for order in orders:
    actions = meta.Session.query(model.Action).filter(model.Action.order_id==order.id).\
        order_by(model.Action.created).all()
    for action in actions:
        if action.status_id == 11:
            order.customers = action.performers
        elif action.status_id == 12:
            order.customers = [action.performers[0]]
        elif action.status_id == 4:
            order.customers.append(action.performers[0])
        elif action.status.redirects == 1:
            order.performers = []
        elif action.status.redirects == 6:
            for perf in action.performers:
                if perf not in order.customers:
                    order.customers.append(perf)
        else: 
            order.performers = action.performers
            
meta.Session.commit()
         
