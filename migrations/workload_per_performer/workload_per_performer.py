# Launch in the paster shell

import ordermanager.model as model
import ordermanager.model.meta as meta

orders = meta.Session.query(model.Order).all()
for order in orders:
    action = meta.Session.query(model.Action).filter(model.Action.order_id==order.id).\
        filter(model.Action.status_id==3).order_by(model.sql.desc(model.Action.created)).first()
    for op in order.order_performers:
        op.workload = order.workload
        if action and op.person in action.performers:
            op.current = True
    order.workload = sum(map(lambda x: x.workload, order.order_performers))

meta.Session.commit()
