# 🌍 OAP WORLD

**One World. One Front Door. Many Systems Inside.**

A civic operating system built on a postcode-based living network with intelligence, memory, and contribution-based economy.

---

## 📍 Spatial Structure

```
📍 Spot → 🧭 Area → 🏛 Zone → 🌍 World
```

- **Spot**: Base unit - street level, postcode cluster, local community space
- **Area**: Mid layer - borough/district level coordination
- **Zone**: City layer - regional governance
- **World**: Global ecosystem - all zones connected

---

## 🚀 Quick Start

### Prerequisites
- Python 3.9+
- PostgreSQL 14+
- pip

### Installation

```bash
cd backend

# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Set up database
createdb oap_world

# Run migrations (after first run)
flask db init
flask db migrate -m "Initial schema"
flask db upgrade

# Start server
python app/__init__.py
```

Server runs at: `http://localhost:5000`

---

## 📡 Core System Modules

| System | Endpoint | Description |
|--------|----------|-------------|
| 📍 Spots | `/api/v1/spots` | Base unit locations |
| 🧭 Areas | `/api/v1/areas` | Mid-layer collections |
| 🏛 Zones | `/api/v1/zones` | City-level coordination |
| 👤 Users | `/api/v1/users` | Identity & human state |
| 💎 SIKA | `/api/v1/sika` | Value system & economy |
| 🧠 HRM | `/api/v1/hrm` | Intelligence & memory |
| 📡 Pulse | `/api/v1/pulse` | Live activity feed |
| 💬 Signal | `/api/v1/signal` | News & information |
| 🔗 Link | `/api/v1/link` | Communication system |
| 🎮 Arena | `/api/v1/arena` | Competition & games |
| 🎪 Movement | `/api/v1/movement` | Real-world activities |
| 🛡 Guardian | `/api/v1/guardian` | Safety & moderation |
| 🌿 Nature | `/api/v1/nature` | Environmental data |
| 💚 Wellbeing | `/api/v1/wellbeing` | Health & wellness |

---

## 💎 SIKA Economy Flow

```
Action → HRM Validation → Trust Update → SIKA Reward → Reputation Growth
```

**Sources of SIKA:**
- 🎮 Arena participation
- 🎪 Movement activity
- 💬 Signal contributions
- 🔗 Link engagement
- 📍 Spot activity

---

## 🧠 System Intelligence Flow

```
User Action
    ↓
Spot Processing
    ↓
HRM Validation
    ↓
SIKA Update
    ↓
Pulse Update
    ↓
World Sync
```

---

## 📁 Project Structure

```
oap-world/
├── database/
│   └── schema.sql          # Complete PostgreSQL schema
├── backend/
│   ├── app/
│   │   ├── __init__.py     # Flask application factory
│   │   ├── models/         # Database models
│   │   ├── routes/         # API route blueprints
│   │   └── services/       # Business logic
│   ├── config/
│   │   ├── __init__.py
│   │   ├── config.py       # Configuration classes
│   │   └── database.py     # Database setup
│   └── requirements.txt
└── README.md
```

---

## ⚡ Human State Layer

| State | Options | Description |
|-------|---------|-------------|
| Energy | high, medium, low | Live engagement level |
| Mood | calm, focused, motivated, tired, happy | Emotional state |
| Stealth | visible, quiet, hidden | Presence control |

---

## 🌿 Nature & Wellbeing

**Nature Layer:**
- Weather conditions
- Environmental alerts
- Wildlife sightings
- Green spaces

**Wellbeing Layer:**
- Mental health tracking
- Exercise minutes
- Nutrition score
- Sleep hours
- Mindfulness practice

---

## 🔄 Cross-Spot System

Spots connect to Areas → Areas connect to Zones → Zones connect globally

SIKA can transfer between spots under trust rules.

---

## 📜 Database Schema

Complete schema in `database/schema.sql` includes:
- 25+ tables covering all systems
- Proper foreign key relationships
- Indexes for performance
- Default configuration values
- Hierarchy overview view

---

## 🚀 Next Steps

1. **Mobile UI**: Build React Native frontend
2. **Real-time**: Add WebSocket support for Pulse
3. **Analytics**: Implement HRM pattern recognition
4. **Governance**: Build Treasury module
5. **Deployment**: Docker + Kubernetes setup

---

## 🌍 Final Principle

> One World = OAP World  
> One Door = Entry System  
> Many Spots = Living Locations  
> One Pulse = Live Awareness  
> One HRM = Intelligence Memory  
> One SIKA = Value System

---

**Built with ❤️ for community empowerment**
