"""Explicit initializer for EARTH IS OUR TURF durable PostgreSQL saves."""
from mission_control import mtown_persistence

if __name__=="__main__":
    mtown_persistence.ensure_schema()
    print("eiot_world_persistence_ready")
