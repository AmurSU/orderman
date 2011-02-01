# Launch in the paster shell

import ordermanager.model as model
import ordermanager.model.meta as meta

meta.metadata.create_all(bind=meta.engine)

