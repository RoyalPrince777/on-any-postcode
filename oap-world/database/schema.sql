-- OAP World Database Schema
-- Starting from The Spot and expanding to the full hierarchy

-- ============================================
-- 📍 SPOT (Base Unit) - Where life happens
-- ============================================
CREATE TABLE spots (
    id SERIAL PRIMARY KEY,
    name VARCHAR(255) NOT NULL,
    postcode_prefix VARCHAR(10) NOT NULL,  -- e.g., "SW1A"
    street_level_address TEXT,
    latitude DECIMAL(10, 8),
    longitude DECIMAL(11, 8),
    area_id INTEGER,  -- Links to Area
    status VARCHAR(50) DEFAULT 'active',  -- active, inactive, archived
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Local SIKA pool for each Spot
CREATE TABLE spot_sika_pools (
    id SERIAL PRIMARY KEY,
    spot_id INTEGER REFERENCES spots(id) ON DELETE CASCADE,
    total_pool DECIMAL(20, 8) DEFAULT 0,
    distributed_today DECIMAL(20, 8) DEFAULT 0,
    last_distribution_date DATE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- ============================================
-- 🧭 AREA (Mid Layer) - Collection of Spots
-- ============================================
CREATE TABLE areas (
    id SERIAL PRIMARY KEY,
    name VARCHAR(255) NOT NULL,
    borough_level VARCHAR(255),
    district_level VARCHAR(255),
    zone_id INTEGER,  -- Links to Zone
    center_latitude DECIMAL(10, 8),
    center_longitude DECIMAL(11, 8),
    status VARCHAR(50) DEFAULT 'active',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Link Spots to Areas
ALTER TABLE spots ADD CONSTRAINT fk_spot_area 
    FOREIGN KEY (area_id) REFERENCES areas(id);

-- ============================================
-- 🏛 ZONE (City Layer) - Collection of Areas
-- ============================================
CREATE TABLE zones (
    id SERIAL PRIMARY KEY,
    name VARCHAR(255) NOT NULL,
    city_level VARCHAR(255),
    region_level VARCHAR(255),
    country_code VARCHAR(2) DEFAULT 'GB',
    center_latitude DECIMAL(10, 8),
    center_longitude DECIMAL(11, 8),
    status VARCHAR(50) DEFAULT 'active',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Link Areas to Zones
ALTER TABLE areas ADD CONSTRAINT fk_area_zone 
    FOREIGN KEY (zone_id) REFERENCES zones(id);

-- ============================================
-- 👤 USERS & IDENTITY
-- ============================================
CREATE TABLE users (
    id SERIAL PRIMARY KEY,
    username VARCHAR(100) UNIQUE NOT NULL,
    email VARCHAR(255) UNIQUE NOT NULL,
    password_hash VARCHAR(255) NOT NULL,
    
    -- Human State Layer
    energy_level VARCHAR(20) DEFAULT 'medium',  -- high, medium, low
    mood_state VARCHAR(50) DEFAULT 'calm',  -- calm, focused, motivated, tired, happy
    stealth_mode BOOLEAN DEFAULT FALSE,  -- Visibility state
    
    -- Home Spot
    home_spot_id INTEGER REFERENCES spots(id),
    
    -- Trust & Reputation
    trust_score DECIMAL(5, 4) DEFAULT 0.5000,  -- 0.0000 to 1.0000
    reputation_points INTEGER DEFAULT 0,
    
    -- Account Status
    is_verified BOOLEAN DEFAULT FALSE,
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- User activity in different Spots
CREATE TABLE user_spot_activity (
    id SERIAL PRIMARY KEY,
    user_id INTEGER REFERENCES users(id) ON DELETE CASCADE,
    spot_id INTEGER REFERENCES spots(id) ON DELETE CASCADE,
    first_visit DATE,
    last_visit TIMESTAMP,
    visit_count INTEGER DEFAULT 0,
    contribution_score DECIMAL(10, 4) DEFAULT 0,
    UNIQUE(user_id, spot_id)
);

-- ============================================
-- 💎 SIKA (Value System) - Internal Economy
-- ============================================
CREATE TABLE sika_accounts (
    id SERIAL PRIMARY KEY,
    user_id INTEGER REFERENCES users(id) ON DELETE CASCADE,
    spot_id INTEGER REFERENCES spots(id) ON DELETE CASCADE,
    balance DECIMAL(20, 8) DEFAULT 0,
    earned_total DECIMAL(20, 8) DEFAULT 0,
    spent_total DECIMAL(20, 8) DEFAULT 0,
    last_earned_at TIMESTAMP,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(user_id, spot_id)
);

-- SIKA Transactions
CREATE TABLE sika_transactions (
    id SERIAL PRIMARY KEY,
    from_user_id INTEGER REFERENCES users(id),
    to_user_id INTEGER REFERENCES users(id),
    spot_id INTEGER REFERENCES spots(id),
    amount DECIMAL(20, 8) NOT NULL,
    transaction_type VARCHAR(50) NOT NULL,  -- arena_reward, movement_reward, signal_contribution, link_engagement, spot_activity
    description TEXT,
    hrm_validated BOOLEAN DEFAULT FALSE,
    trust_impact DECIMAL(5, 4) DEFAULT 0,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- SIKA Distribution Rules (Cross-Spot transfers)
CREATE TABLE sika_transfer_rules (
    id SERIAL PRIMARY KEY,
    from_spot_id INTEGER REFERENCES spots(id),
    to_spot_id INTEGER REFERENCES spots(id),
    max_transfer_amount DECIMAL(20, 8),
    trust_threshold DECIMAL(5, 4) DEFAULT 0.7000,
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- ============================================
-- 🧠 HRM (Intelligence System) - Memory & Learning
-- ============================================
CREATE TABLE hrm_memory (
    id SERIAL PRIMARY KEY,
    user_id INTEGER REFERENCES users(id) ON DELETE CASCADE,
    memory_type VARCHAR(50) NOT NULL,  -- behavior, pattern, progress, trust
    memory_key VARCHAR(255) NOT NULL,
    memory_value JSONB,  -- Flexible storage for complex data
    confidence_score DECIMAL(5, 4),
    last_updated TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    expires_at TIMESTAMP,
    UNIQUE(user_id, memory_key)
);

-- Behavior Tracking
CREATE TABLE hrm_behavior_logs (
    id SERIAL PRIMARY KEY,
    user_id INTEGER REFERENCES users(id) ON DELETE CASCADE,
    spot_id INTEGER REFERENCES spots(id),
    action_type VARCHAR(100) NOT NULL,
    action_data JSONB,
    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    processed_by_hrm BOOLEAN DEFAULT FALSE
);

-- Pattern Recognition Results
CREATE TABLE hrm_patterns (
    id SERIAL PRIMARY KEY,
    user_id INTEGER REFERENCES users(id) ON DELETE CASCADE,
    pattern_type VARCHAR(100) NOT NULL,  -- daily_routine, weekly_activity, social_interaction
    pattern_data JSONB,
    confidence DECIMAL(5, 4),
    detected_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    is_active BOOLEAN DEFAULT TRUE
);

-- Trust Evaluation History
CREATE TABLE hrm_trust_evaluations (
    id SERIAL PRIMARY KEY,
    user_id INTEGER REFERENCES users(id) ON DELETE CASCADE,
    evaluator_type VARCHAR(50) NOT NULL,  -- system, community, peer
    previous_trust_score DECIMAL(5, 4),
    new_trust_score DECIMAL(5, 4),
    evaluation_reason TEXT,
    evaluated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- ============================================
-- 📡 PULSE (Feed System) - Live Activity Stream
-- ============================================
CREATE TABLE pulse_events (
    id SERIAL PRIMARY KEY,
    spot_id INTEGER REFERENCES spots(id) ON DELETE CASCADE,
    user_id INTEGER REFERENCES users(id),
    event_type VARCHAR(100) NOT NULL,  -- update, activity, achievement, announcement
    event_data JSONB,
    energy_level INTEGER DEFAULT 50,  -- 0-100 scale
    visibility VARCHAR(20) DEFAULT 'public',  -- public, community, private
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Pulse Subscriptions (Users follow Spots/Areas)
CREATE TABLE pulse_subscriptions (
    id SERIAL PRIMARY KEY,
    user_id INTEGER REFERENCES users(id) ON DELETE CASCADE,
    spot_id INTEGER REFERENCES spots(id) ON DELETE CASCADE,
    area_id INTEGER REFERENCES areas(id) ON DELETE CASCADE,
    notification_enabled BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(user_id, spot_id, area_id)
);

-- ============================================
-- 💬 SIGNAL (News System) - Information Layer
-- ============================================
CREATE TABLE signal_posts (
    id SERIAL PRIMARY KEY,
    spot_id INTEGER REFERENCES spots(id) ON DELETE CASCADE,
    area_id INTEGER REFERENCES areas(id) ON DELETE CASCADE,
    zone_id INTEGER REFERENCES zones(id) ON DELETE CASCADE,
    author_id INTEGER REFERENCES users(id),
    post_type VARCHAR(50) NOT NULL,  -- announcement, news, update, broadcast
    title VARCHAR(500) NOT NULL,
    content TEXT NOT NULL,
    priority VARCHAR(20) DEFAULT 'normal',  -- low, normal, high, urgent
    is_pinned BOOLEAN DEFAULT FALSE,
    views_count INTEGER DEFAULT 0,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- ============================================
-- 🔗 LINK (Communication System)
-- ============================================
CREATE TABLE link_messages (
    id SERIAL PRIMARY KEY,
    sender_id INTEGER REFERENCES users(id) ON DELETE CASCADE,
    recipient_id INTEGER REFERENCES users(id) ON DELETE CASCADE,
    spot_id INTEGER REFERENCES spots(id),
    message_type VARCHAR(50) DEFAULT 'direct',  -- direct, group, broadcast
    content TEXT NOT NULL,
    is_read BOOLEAN DEFAULT FALSE,
    read_at TIMESTAMP,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Social Connections
CREATE TABLE link_connections (
    id SERIAL PRIMARY KEY,
    user_id INTEGER REFERENCES users(id) ON DELETE CASCADE,
    connected_user_id INTEGER REFERENCES users(id) ON DELETE CASCADE,
    connection_type VARCHAR(50) DEFAULT 'friend',  -- friend, follower, collaborator
    trust_level DECIMAL(5, 4) DEFAULT 0.5000,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(user_id, connected_user_id)
);

-- ============================================
-- 🎮 ARENA (Competition System)
-- ============================================
CREATE TABLE arena_games (
    id SERIAL PRIMARY KEY,
    spot_id INTEGER REFERENCES spots(id) ON DELETE CASCADE,
    game_name VARCHAR(255) NOT NULL,
    game_type VARCHAR(50) NOT NULL,  -- 1v1, team, tournament, ranked
    status VARCHAR(50) DEFAULT 'pending',  -- pending, active, completed, cancelled
    max_participants INTEGER,
    current_participants INTEGER DEFAULT 0,
    sika_prize_pool DECIMAL(20, 8) DEFAULT 0,
    started_at TIMESTAMP,
    completed_at TIMESTAMP,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Arena Participants
CREATE TABLE arena_participants (
    id SERIAL PRIMARY KEY,
    game_id INTEGER REFERENCES arena_games(id) ON DELETE CASCADE,
    user_id INTEGER REFERENCES users(id) ON DELETE CASCADE,
    team_id INTEGER,
    rank_position INTEGER,
    score DECIMAL(10, 2),
    sika_earned DECIMAL(20, 8) DEFAULT 0,
    joined_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Arena Leaderboards (per Spot)
CREATE TABLE arena_leaderboards (
    id SERIAL PRIMARY KEY,
    spot_id INTEGER REFERENCES spots(id) ON DELETE CASCADE,
    user_id INTEGER REFERENCES users(id) ON DELETE CASCADE,
    game_type VARCHAR(50),
    total_wins INTEGER DEFAULT 0,
    total_losses INTEGER DEFAULT 0,
    win_rate DECIMAL(5, 4),
    ranking_points INTEGER DEFAULT 0,
    season VARCHAR(50) DEFAULT 'current',
    last_updated TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(spot_id, user_id, game_type, season)
);

-- ============================================
-- 🎪 MOVEMENT (Action System) - Real-world Participation
-- ============================================
CREATE TABLE movement_activities (
    id SERIAL PRIMARY KEY,
    spot_id INTEGER REFERENCES spots(id) ON DELETE CASCADE,
    activity_type VARCHAR(100) NOT NULL,  -- community_power_day, local_mission, cultural_activity, public_event
    title VARCHAR(500) NOT NULL,
    description TEXT,
    location_name VARCHAR(255),
    latitude DECIMAL(10, 8),
    longitude DECIMAL(11, 8),
    start_time TIMESTAMP NOT NULL,
    end_time TIMESTAMP,
    max_participants INTEGER,
    current_participants INTEGER DEFAULT 0,
    sika_reward DECIMAL(20, 8) DEFAULT 0,
    status VARCHAR(50) DEFAULT 'scheduled',  -- scheduled, active, completed, cancelled
    created_by INTEGER REFERENCES users(id),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Movement Participation
CREATE TABLE movement_participation (
    id SERIAL PRIMARY KEY,
    activity_id INTEGER REFERENCES movement_activities(id) ON DELETE CASCADE,
    user_id INTEGER REFERENCES users(id) ON DELETE CASCADE,
    participation_status VARCHAR(50) DEFAULT 'registered',  -- registered, attended, cancelled
    check_in_time TIMESTAMP,
    check_out_time TIMESTAMP,
    sika_awarded DECIMAL(20, 8) DEFAULT 0,
    feedback_rating INTEGER,  -- 1-5 scale
    feedback_comment TEXT,
    participated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(activity_id, user_id)
);

-- ============================================
-- 🛡 GUARDIAN (Safety System)
-- ============================================
CREATE TABLE guardian_reports (
    id SERIAL PRIMARY KEY,
    reporter_id INTEGER REFERENCES users(id),
    reported_user_id INTEGER REFERENCES users(id),
    reported_content_type VARCHAR(50),  -- message, post, activity, user
    reported_content_id INTEGER,
    report_reason VARCHAR(255) NOT NULL,
    severity_level VARCHAR(20) DEFAULT 'medium',  -- low, medium, high, critical
    status VARCHAR(50) DEFAULT 'pending',  -- pending, reviewing, resolved, dismissed
    moderator_id INTEGER REFERENCES users(id),
    resolution_notes TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    resolved_at TIMESTAMP
);

-- Risk Detection Logs
CREATE TABLE guardian_risk_logs (
    id SERIAL PRIMARY KEY,
    user_id INTEGER REFERENCES users(id),
    spot_id INTEGER REFERENCES spots(id),
    risk_type VARCHAR(100) NOT NULL,
    risk_score DECIMAL(5, 4),
    risk_data JSONB,
    action_taken VARCHAR(255),
    detected_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- ============================================
-- 🌿 NATURE & WELLBEING SYSTEM
-- ============================================
-- Nature Layer
CREATE TABLE nature_data (
    id SERIAL PRIMARY KEY,
    spot_id INTEGER REFERENCES spots(id) ON DELETE CASCADE,
    weather_condition VARCHAR(100),
    temperature_celsius DECIMAL(5, 2),
    air_quality_index INTEGER,
    environmental_alerts JSONB,
    wildlife_sightings JSONB,
    green_space_nearby BOOLEAN DEFAULT TRUE,
    last_updated TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Wellbeing Layer
CREATE TABLE user_wellbeing (
    id SERIAL PRIMARY KEY,
    user_id INTEGER REFERENCES users(id) ON DELETE CASCADE,
    mental_health_score INTEGER,  -- 1-100
    exercise_minutes_today INTEGER DEFAULT 0,
    nutrition_score INTEGER,  -- 1-100
    sleep_hours_last_night DECIMAL(4, 2),
    mindfulness_minutes_today INTEGER DEFAULT 0,
    recorded_date DATE DEFAULT CURRENT_DATE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(user_id, recorded_date)
);

-- ============================================
-- 📜 CHRONICLE (Event History) - Audit Trail
-- ============================================
CREATE TABLE chronicle_events (
    id SERIAL PRIMARY KEY,
    event_category VARCHAR(100) NOT NULL,  -- user_action, system_event, economic_transaction, governance_decision
    event_source VARCHAR(100) NOT NULL,  -- spot, area, zone, world, hrm, sika
    event_data JSONB NOT NULL,
    spot_id INTEGER REFERENCES spots(id),
    user_id INTEGER REFERENCES users(id),
    immutable_hash VARCHAR(255),  -- For integrity verification
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- ============================================
-- ⚙️ SYSTEM CONFIGURATION
-- ============================================
CREATE TABLE system_config (
    id SERIAL PRIMARY KEY,
    config_key VARCHAR(255) UNIQUE NOT NULL,
    config_value JSONB NOT NULL,
    description TEXT,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Default SIKA distribution rates
INSERT INTO system_config (config_key, config_value, description) VALUES
('sika_rates', '{
    "arena_participation": 10.0,
    "movement_activity": 15.0,
    "signal_contribution": 5.0,
    "link_engagement": 2.0,
    "spot_activity": 3.0
}', 'SIKA reward rates for different activities'),
('trust_thresholds', '{
    "minimum_for_transfer": 0.6000,
    "high_trust": 0.8000,
    "verified_user": 0.7000
}', 'Trust score thresholds for various actions');

-- ============================================
-- INDEXES FOR PERFORMANCE
-- ============================================
CREATE INDEX idx_spots_area ON spots(area_id);
CREATE INDEX idx_areas_zone ON areas(zone_id);
CREATE INDEX idx_users_home_spot ON users(home_spot_id);
CREATE INDEX idx_sika_accounts_user ON sika_accounts(user_id);
CREATE INDEX idx_sika_transactions_spot ON sika_transactions(spot_id);
CREATE INDEX idx_hrm_memory_user ON hrm_memory(user_id);
CREATE INDEX idx_pulse_events_spot ON pulse_events(spot_id);
CREATE INDEX idx_pulse_events_created ON pulse_events(created_at DESC);
CREATE INDEX idx_signal_posts_spot ON signal_posts(spot_id);
CREATE INDEX idx_movement_activities_spot ON movement_activities(spot_id);
CREATE INDEX idx_chronicle_events_created ON chronicle_events(created_at DESC);

-- ============================================
-- 🌍 HIERARCHY SUMMARY VIEW
-- ============================================
CREATE VIEW hierarchy_overview AS
SELECT 
    z.id as zone_id,
    z.name as zone_name,
    COUNT(DISTINCT a.id) as area_count,
    COUNT(DISTINCT s.id) as spot_count,
    COUNT(DISTINCT u.id) as user_count
FROM zones z
LEFT JOIN areas a ON a.zone_id = z.id
LEFT JOIN spots s ON s.area_id = a.id
LEFT JOIN users u ON u.home_spot_id = s.id
GROUP BY z.id, z.name;
