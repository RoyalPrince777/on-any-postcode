# EARTH IS OUR TURF production gates

This directory contains the Unreal client/server source foundation for **EARTH IS OUR TURF**.

Truth boundary:
- Repository presence is not an Unreal build proof.
- The C++ project must be opened and compiled with Unreal Engine 5.8 before the Unreal gate can be Green.
- `EarthIsOurTurfServer.Target.cs` is the dedicated Unreal server target.
- `EIOTWorldBootstrap` fetches deterministic world cells from the first-party world server.
- `EIOTPedestrian` and `EIOTTrafficCar` contain runtime movement logic; animation/vehicle assets and Unreal runtime execution remain a separate proof gate.

Backend:
- `eiot_world_server.py` is the authoritative Python world-server process.
- `mission_control/mtown_persistence.py` stores durable world state in PostgreSQL with hashed reconnect tokens.
- Run `python scripts/init_eiot_world_persistence.py` against the selected production database before enabling save/reconnect.
- `mission_control/mtown_endless_world.py` generates deterministic cells at unbounded integer coordinates.
