-- CREATE DATABASE IS NOT EXISTS cadetcoin;
-- USE cadetcoin;

-- CREATE TABLE IS NOT EXISTS cadetgroups(
--   ID INT AUTO_INCREMENT PRIMARY KEY,
--   groupname VARCHAR(100) NOT NULL,
--   grouptype VARCHAR(50) NOT NULL
-- );

-- CREATE TABLE IS NOT EXISTS users (
--   ID INT AUTO_INCREMENT PRIMARY KEY,
--   username VARCHAR(50) NOT NULL,
--   password_hash VARCHAR(100) NOT NULL,
--   fullname VARCHAR(100) NOT NULL,
--   role ENUM('cadet', 'admin') NOT NULL DEFAULT 'cadet',
--   groupID INT,
--   coins INT NOT NULL DEFAULT 0,
--   created TIMESTAMP DEFAULT CURRENT,
--   FOREIGN KEY (groupID) REFERENCES cadetgroups(ID)
-- );

-- CREATE TABLE IS NOT EXISTS activities(
--   ID INT AUTO_INCREMENT PRIMARY KEY,
--   name VARCHAR(100) NOT NULL
--   description TEXT,
--   coinVal INT NOT NULL,
--   req_ver BOOLEAN NOT NULL DEFAULT TRUE
-- );

-- CREATE TABLE IS NOT EXISTS workouts(
--   ID INT AUTO_INCREMENT PRIMARY KEY,
--   userID INT NOT NULL,
--   activityID INT NOT NULL,
--   notes TEXT,
--   perform_val VARCHAR(100),
--   coinsEarned INT NOT NULL DEFAULT 0,
--   verSTATUS ENUM('pending', 'verified', 'rejected') NOT NULL DEFAULT 'pending',
--   verifed INT,
--   created TIMESTAMP DEFAULT CURRENT,
--   FOREIGN KEY (userID) REFERENCES users(ID),
--   FOREIGN KEY (activityID) REFERENCES activities(ID),
--   FOREIGN KEY (verified) REFERENCES users(ID)
-- );

-- CREATE TABLE IS NOT EXISTS rewards(
--   ID INT AUTO_INCREMENT PRIMARY KEY,
--   reward VARCHAR(100) NOT NULL,
--   description TEXT,
--   costOfCoin INTO NOT NULL,
--   active BOOLEAN NOT NULL DEFAULT TRUE
-- );

-- CREATE TABLE IS NOT EXISTS redemptions(
--   id INT AUTO_INCREMENT PRIMARY KEY,
--   userID INT NOT NULL,
--   rewardID INT NOT NULL,
--   spentCoins INT NOT NULL,
--   redemSTATUS ENUM ('pending', 'approved', 'denied') NOT NULL DEFAULT 'pending',
--   created TIMESTAMP DEFAULT CURRENT
--   FOREIGN KEY (userID) REFERENCES users(ID),
--   FOREIGN KEY (rewardID) REFERENCES rewards(ID)
-- );

-- CREATE TABLE IS NOT EXISTS coinTrans(
--   ID INT AUTO_INCREMENT PRIMARY KEY,
--   userID INT NOT NULL,
--   amount INT NOT NULL,
--   transType ENUM('earned', 'spent', 'adminAdded', 'adminRemoved', 'transfer') NOT NULL,
--   description VARCHAR (300),
--   created TIMESTAMP DEFAULT CURRENT,
--   FOREIGN KEY (userID) REFERENCES users(ID)
-- );

-- INSERT INTO cadetGroups (groupName, groupType)
-- VALUES ('cadet.demo', 'temp_hash', 'Cadet Demo', 'cadet', 1, 0),
-- ('admin.demo', 'temp_hash', 'Admin Demo', 'admin', 1, 0);

-- INSERT INTO activities (name, description, coin_value, requires_verification)
-- VALUES
-- ('Recorded Run', 'Cadet completed a logged run', 10, TRUE),
-- ('Company Workout', 'Cadet attended a company workout', 15, TRUE),
-- ('Improved AFT Score', 'Cadet improved AFT performance', 25, TRUE),
-- ('Maxed AFT', 'Cadet maxed the AFT', 30, TRUE),
-- ('Ran Marathon', 'Cadet completed a marathon', 30, TRUE),
-- ('Reached 1000 lb Club', 'Cadet reached 1000 lb total', 30, TRUE),
-- ('Dunked on the Supe + Ratio', 'Morale-based bonus activity', 1000, TRUE);

-- INSERT INTO rewards (reward_name, description, coin_cost)
-- VALUES
-- ('Company Store Discount', 'Discount at company store', 50),
-- ('Peer Challenge Entry', 'Entry into peer fitness challenge', 25),
-- ('PMI Incentive', 'PMI-related reward', 100),
-- ('Privilege Reward', 'Approved privilege reward', 150);

CREATE DATABASE IF NOT EXISTS cadetcoin;
USE cadetcoin;

CREATE TABLE IF NOT EXISTS users (
    id INT AUTO_INCREMENT PRIMARY KEY,
    name VARCHAR(100) NOT NULL,
    coins INT NOT NULL DEFAULT 0
);

CREATE TABLE IF NOT EXISTS activities (
    id INT AUTO_INCREMENT PRIMARY KEY,
    name VARCHAR(100) NOT NULL,
    coin_value INT NOT NULL
);

CREATE TABLE IF NOT EXISTS workouts (
    id INT AUTO_INCREMENT PRIMARY KEY,
    user_id INT NOT NULL,
    activity_id INT NOT NULL,
    notes TEXT,
    coins_earned INT NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users(id),
    FOREIGN KEY (activity_id) REFERENCES activities(id)
);

INSERT INTO users (name, coins)
VALUES ('Cadet', 0);

INSERT INTO activities (name, coin_value)
VALUES
('Recorded Run', 10),
('Company Workout', 15),
('Improved AFT Score', 25),
('Maxed AFT', 30),
('Ran marathon', 30),
('Reach 1000 lb Club', 30),
('Dunked on the Supe + Ratio', 1000);