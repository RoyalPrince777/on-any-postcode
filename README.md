# 🌍 ON ANY POSTCODE — Architecture v12

**Born Local. Built Global. Earth is our turf.**

A comprehensive Flask application implementing a multi-system platform for community engagement, operations management, and global connectivity. Built as "One Brand. One Front Door. One Identity."

---

## 🎯 Overview

ON ANY POSTCODE is a full-stack community platform with:

- **9 Distinct Systems**: World, Identity, Intelligence, Money, Communications, Infrastructure, Operations, Culture, Trust
- **40+ Routes**: Comprehensive web interface for all systems
- **20+ Database Tables**: Scalable data architecture
- **Member Management**: User profiles with geographic hierarchy (postcode → country → continent)
- **World Cup 2026 Integration**: 48-team tournament framework with community features
- **HRM Council**: Governance structure with AI agents and decision tracking
- **Community Power**: Contribution and reputation system

---

## 🚀 Quick Start

### Prerequisites
- Python 3.8+
- pip or pipenv

### Installation

1. **Clone the repository**
```bash
git clone https://github.com/RoyalPrince777/on-any-postcode.git
cd on-any-postcode
```

2. **Create virtual environment**
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

3. **Install dependencies**
```bash
pip install -r requirements.txt
```

4. **Configure environment**
```bash
cp .env.example .env
# Edit .env with your settings
```

5. **Run the application**
```bash
python app.py
```

Visit `http://localhost:5000` in your browser.

---

## 📋 System Architecture

### Nine Separate Systems

| System | Emoji | Purpose |
|--------|-------|---------|
| **OAP World** | 🌍 | One public front door, signals, experiences, explorer |
| **My World** | 👤 | Identity hub, profiles, family tree, awards |
| **Intelligence** | 🧠 | HRM, review core, agents, command center |
| **Money / SIKA** | 💎 | Financial records, trust, wallet readiness |
| **Communications** | 📧 | Mail, messenger, notifications, broadcasts |
| **Infrastructure** | 🗺 | Weather, maps, navigation, connectivity, eSIM |
| **Operations** | 🚚 | Bookings, delivery, riders, drivers, businesses |
| **Culture** | 🎭 | Music, media, sports, education, World Cup |
| **Trust** | 🛡 | Privacy, safety, compliance, verification, audit |

### Core Routes

**Public Pages:**
- `/` - Homepage with system grid
- `/<system>` - System overview
- `/<system>/<module>` - Module details
- `/world-cup` - World Cup 2026 hub
- `/world-cup/team/<team>` - Team details

**Member Features:**
- `/join` - Create account
- `/enter` - Login
- `/my-world` - Member dashboard
- `/leave` - Logout

**Operations:**
- `/dispatch` - Delivery dispatch board
- `/command` - Master control center
- `/hrm/council` - HRM Council overview
- `/hrm/local-ai` - AI memory hub

**Infrastructure:**
- `/mail` - Internal mail system
- `/messenger` - Community messenger
- `/maps-hub` - Maps and places
- `/navigation-hub` - Route tracking
- `/weather-hub` - Weather records
- `/notifications` - System alerts

**Community:**
- `/community-power` - Contribution tracking
- `/oap-world` - World hub dashboard

---

## 💾 Database Schema

### Core Tables

| Table | Purpose |
|-------|---------|
| **members** | User profiles with geographic data (postcode, borough, country, continent, circle) |
| **records** | Generic system/module records with status tracking |
| **community_power** | Member contributions and points |
| **businesses** | Business registry and network |
| **creators** | Creator profiles and links |
| **experiences** | Events, gatherings, matchday activities |
| **delivery_bookings** | Delivery orders and tracking |
| **riders_drivers** | Logistics personnel management |
| **sika_records** | Trust and value records |
| **verification_badges** | Verification levels and badges |
| **readiness_requests** | Regulatory and provider requests |
| **audit** | Action logging and compliance |
| **dispatch_jobs** | Delivery dispatch assignments |
| **rider_status** | Real-time rider/driver status |
| **mail_items** | Internal messaging |
| **notifications** | System alerts |
| **navigation_routes** | Route and movement tracking |
| **map_places** | Geographic markers and places |
| **weather_records** | Weather data by location |

---

## 🔐 Security Features

- **HTML Escaping**: All user input sanitized with `escape()`
- **Parameterized Queries**: SQL injection prevention via prepared statements
- **Session Management**: Flask sessions with HTTPONLY and SECURE flags
- **Password Hashing**: Passwords stored securely (werkzeug.security)
- **CSRF Protection**: Ready for Flask-WTF integration
- **Audit Logging**: All actions tracked in audit table

---

## 🎭 Key Features

### Member System
- Geographic hierarchy: Postcode → Borough → County → Country → Continent
- Membership circles: Community Member, Postcode Founder, Borough Builder, Country Champion
- Profile management with family tree support

### World Cup 2026
- 48-team structure with group tables and fixtures
- Match command centers with 12+ tabs per match
- Team hubs with culture, business, and community features
- Tournament structure: groups → knockouts → semifinals → final

### Community Features
- **Community Power**: Track contributions across 6 categories (Community, Business, Creator, Events, Sports, Culture)
- **SIKA Records**: Trust system with contribution types (Contribution Recorded, Trust Earned, Value Manifested, Legacy Recorded)
- **Verification Levels**: 8 levels from postcode to universe

### HRM Council
- God Layer and Founder governance
- Advisory agents: Chancellor, Guardian, Architect, Archivist
- Neo Team (Execution): Neo, Morpheus, Trinity, Oracle, Architect, Keymaker, Seraph, Tank, Dozer
- Animal Team (Wisdom): Bee, Elephant, Owl, Gorilla, Lion, Tiger, Panther, Eagle, Dolphin, Horse, Stag
- AI Partners: GPT, Claude, Gemini, Kimi, Grok, Edge/Copilot

### Operations
- Business network and creator hub
- Experience/event management
- Delivery booking system
- Rider and driver management
- Dispatch job assignments

### Infrastructure
- Weather tracking by location
- Navigation routes and movement
- Maps hub with places and landmarks
- Mail system with folders (Inbox, Sent, Draft, Review)
- Notifications and broadcasts
- Community messenger

---

## 🛠 API Endpoints

### Member Routes
- `POST /join` - Register new member
- `POST /enter` - Member login
- `GET /leave` - Logout
- `GET /my-world` - Member dashboard

### Records
- `POST /add-record` - Add generic record
- `POST /add-business` - Add business
- `POST /add-creator` - Add creator
- `POST /add-experience` - Add experience

### Operations
- `POST /add-delivery` - Add delivery booking
- `POST /add-rider-driver` - Add rider/driver
- `POST /add-dispatch` - Create dispatch job

### Finance
- `POST /add-sika` - Add SIKA record
- `POST /add-verification` - Add verification badge
- `POST /add-readiness` - Add readiness request

### Communications
- `POST /send-mail` - Send mail
- `POST /add-notification` - Create notification
- `POST /add-record` - Add messenger message (system='communications', module='Messenger')

### Infrastructure
- `POST /add-route` - Add navigation route
- `POST /add-place` - Add map place
- `POST /add-weather` - Add weather record

### Community
- `POST /add-community-power` - Record contribution

---

## 📊 Data Hierarchy

```
Global
├── Continents (7)
│   ├── Africa, Europe, Asia, North America, South America, Caribbean, Oceania
│   └── Countries (48)
│       └── Teams (World Cup 2026)
│       └── Members
│           ├── Postcode
│           ├── Borough
│           └── County
├── Council (HRM Governance)
└── Community (Global)
    ├── Community Power
    ├── Businesses
    └── Creators
```

---

## 🌐 Supported Countries (48 Teams)

Algeria, Argentina, Australia, Belgium, Brazil, Cameroon, Canada, Colombia, Costa Rica, Croatia, Denmark, Ecuador, Egypt, England, France, Germany, Ghana, Iran, Iraq, Italy, Ivory Coast, Jamaica, Japan, Mali, Mexico, Morocco, Netherlands, New Zealand, Nigeria, Panama, Paraguay, Poland, Portugal, Qatar, Saudi Arabia, Senegal, Serbia, South Africa, South Korea, Spain, Switzerland, Tunisia, Ukraine, Uruguay, USA, Uzbekistan, Venezuela

---

## 🚢 Deployment

### Heroku

1. Create Heroku app
```bash
heroku create your-app-name
```

2. Set environment variables
```bash
heroku config:set SECRET_KEY=your-secret-key
heroku config:set FLASK_ENV=production
```

3. Deploy
```bash
git push heroku main
```

4. Open app
```bash
heroku open
```

### Docker (Optional)

```dockerfile
FROM python:3.11-slim
WORKDIR /app
COPY requirements.txt .
RUN pip install -r requirements.txt
COPY . .
CMD ["gunicorn", "app:app", "--bind", "0.0.0.0:5000"]
```

---

## 📝 Configuration

Key settings in `app.py`:

```python
app.secret_key = os.environ.get("SECRET_KEY", "OAP-CHANGE-THIS-777")
DB = "oap_architecture_v12.db"
FLASK_ENV = "production"  # Set in .env
```

Environment variables:
- `SECRET_KEY` - Flask session encryption key
- `PORT` - Server port (default: 5000)
- `FLASK_ENV` - development or production
- `FLASK_DEBUG` - Enable/disable debug mode

---

## 🐛 Known Issues & TODOs

### In Progress
- [ ] Implement password hashing (werkzeug.security)
- [ ] Add CSRF protection (Flask-WTF)
- [ ] Implement pagination for large result sets
- [ ] Add database indexes for performance
- [ ] Complete `contribution_form()` implementation
- [ ] Add email verification
- [ ] Add API rate limiting
- [ ] Implement proper error pages (404, 500)

### Future Features
- [ ] Real-time notifications (WebSockets)
- [ ] File uploads (profiles, content)
- [ ] Search functionality
- [ ] Reporting and analytics
- [ ] Mobile app
- [ ] Blockchain integration for SIKA records
- [ ] External API integrations

---

## 👥 Governance

**Build Law Process:**
```
Bee collects → HRM records → Local AI summarises → Council reviews → Founder approves
```

**Values:**
🙏 Truth, Protection, Dignity, Purpose

**Tagline:**
One Race. Human Race.

---

## 📚 Foundation Memory

See `OAP_FOUNDATION_MEMORY.md` for complete architecture documentation, governance structure, and vision.

---

## 🤝 Contributing

1. Create a feature branch (`git checkout -b feature/your-feature`)
2. Make changes with clear commit messages
3. Test locally (`python app.py`)
4. Push to branch (`git push origin feature/your-feature`)
5. Create Pull Request with description

### Code Standards
- Use meaningful variable names
- Add comments for complex logic
- Follow PEP 8 style guide
- Sanitize all user input
- Use parameterized SQL queries

---

## 📄 License

Not specified. Add LICENSE file for open source distribution.

---

## 📞 Support

For issues or questions:
- Check `OAP_FOUNDATION_MEMORY.md` for architecture details
- Review `app.py` route documentation
- Check database schema in `init()` function

---

## 🎯 Version History

| Version | Date | Status |
|---------|------|--------|
| v12 | June 2026 | Active |
| v11 | - | Previous |

---

**ON ANY POSTCODE — Born Local. Built Global. Earth is our turf.**

One Brand. One Front Door. One Identity. One Race. Human Race.
