# Runtime composition wrapper. The proven legacy gate remains byte-for-byte in gates_legacy.py.
from gates_legacy import *

from spot_family import register_spot_family
from royal_oap import register_royal_oap
from oap_intelligence import register_oap_intelligence
from youth_real_education import register_youth_real_education

if 'spot_family' not in app.blueprints:
    register_spot_family(app, db, uid)
if 'royal_oap' not in app.blueprints:
    register_royal_oap(app, db, uid)
if 'oap_intelligence' not in app.blueprints:
    register_oap_intelligence(app, db, uid)
if 'youth_real_education' not in app.blueprints:
    register_youth_real_education(app, db, uid)
