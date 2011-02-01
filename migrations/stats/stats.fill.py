# Launch in the paster shell

import ordermanager.model as model
import ordermanager.model.meta as meta

statuses = meta.Session.query(model.Status).all()
for status in statuses:
    status.ordercount = 0

orders = meta.Session.query(model.Order).filter_by(deleted=False).all()
for order in orders:
    order.status.ordercount += 1

meta.Session.commit()

