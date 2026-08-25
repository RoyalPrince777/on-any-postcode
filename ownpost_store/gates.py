# Runtime composition wrapper. The proven legacy gate remains byte-for-byte in gates_legacy.py.
from gates_legacy import *

from spot_family import register_spot_family
from royal_oap import register_royal_oap
from oap_intelligence import register_oap_intelligence
from youth_real_education import register_youth_real_education
from youth_club import register_youth_club
from bank_intelligence import register_bank_intelligence
from background_258 import register_background_258
from oap_ride import register_oap_ride
from movement_hub import register_movement_hub
from oap_language import register_oap_language
from oap_finalization import register_finalization

if 'spot_family' not in app.blueprints:
    register_spot_family(app, db, uid)
if 'royal_oap' not in app.blueprints:
    register_royal_oap(app, db, uid)
if 'oap_intelligence' not in app.blueprints:
    register_oap_intelligence(app, db, uid)
if 'youth_real_education' not in app.blueprints:
    register_youth_real_education(app, db, uid)
if 'oap_youth_club' not in app.blueprints:
    register_youth_club(app, db, uid)
if 'bank_intelligence' not in app.blueprints:
    register_bank_intelligence(app, db, uid)
if 'background_258' not in app.blueprints:
    register_background_258(app, db, uid)
if 'oap_ride' not in app.blueprints:
    register_oap_ride(app, db, uid)
if 'oap_movement_hub' not in app.blueprints:
    register_movement_hub(app, db, uid)
if 'oap_language' not in app.blueprints:
    register_oap_language(app, db, uid)
if 'oap_finalization' not in app.blueprints:
    register_finalization(app, db, uid)
