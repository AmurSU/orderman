# Launch in the paster shell

import ordermanager.model as model
import ordermanager.model.meta as meta
from datetime import datetime

revoke = model.Status()
revoke.id = 15
revoke.title = u"Заявка отозвана"
revoke.redirects = 15
revoke.created = datetime.now()
revoke.order_count = 0

meta.Session.add(revoke)
meta.Session.commit()

