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
from oap_ride_admin import register_oap_ride_admin
from movement_hub import register_movement_hub
from oap_language import register_oap_language
from oap_checkpoints import register_checkpoints
from provider_contracts import register_provider_contracts
from provider_adapters import register_provider_adapters
from location_bridge import register_location_bridge
from event_bridge import register_event_bridge
from regulated_rails import register_regulated_rails
from oap_observability import register_observability
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
if 'oap_ride_admin' not in app.blueprints:
    register_oap_ride_admin(app, db, uid)
if 'oap_movement_hub' not in app.blueprints:
    register_movement_hub(app, db, uid)
if 'oap_language' not in app.blueprints:
    register_oap_language(app, db, uid)
if 'oap_checkpoints' not in app.blueprints:
    register_checkpoints(app, db, uid)
if 'oap_provider_contracts' not in app.blueprints:
    register_provider_contracts(app)
if 'oap_provider_adapters' not in app.blueprints:
    register_provider_adapters(app)
if 'oap_location_bridge' not in app.blueprints:
    register_location_bridge(app)
if 'oap_event_bridge' not in app.blueprints:
    register_event_bridge(app, db, uid)
if 'oap_regulated_rails' not in app.blueprints:
    register_regulated_rails(app)
if 'oap_observability' not in app.blueprints:
    register_observability(app, db, uid)
if 'oap_finalization' not in app.blueprints:
    register_finalization(app, db, uid)
