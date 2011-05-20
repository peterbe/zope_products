CREATE TABLE users (
"uid"			SERIAL PRIMARY KEY,
"email"			VARCHAR(200) NOT NULL UNIQUE,
"passkey"		VARCHAR(200) NOT NULL UNIQUE,
"temporary_passkey"	VARCHAR(200) NOT NULL,
"name"			VARCHAR(200) NOT NULL DEFAULT '',
"html_emails"		BOOLEAN NOT NULL DEFAULT false,
"unsubscribe_passkey"	VARCHAR(200) NOT NULL DEFAULT '',
"inactive_date"		TIMESTAMP NOT NULL DEFAULT 'infinity',
"last_login_time"	TIMESTAMP NOT NULL DEFAULT 'infinity',
"add_date"		TIMESTAMP NOT NULL DEFAULT NOW(),
"modify_date"		TIMESTAMP NOT NULL DEFAULT NOW()
);

CREATE TABLE user_details (
"duid"                  SERIAL PRIMARY KEY,
"uid"			INT REFERENCES users NOT NULL,
"first_name"            VARCHAR(100) NOT NULL DEFAULT '',
"last_name"             VARCHAR(100) NOT NULL DEFAULT '',
"country"               VARCHAR(100) NOT NULL DEFAULT '',
"website"               VARCHAR(100) NOT NULL DEFAULT '',
"sex"                   VARCHAR(10) NOT NULL DEFAULT '',
"birthday"		INT NULL,
"birthmonth"		INT NULL,
"birthyear"		INT NULL,
"modify_date"		TIMESTAMP NOT NULL DEFAULT NOW()
);

CREATE TABLE user_interest_keywords (
"ukid"                  SERIAL PRIMARY KEY,
"uid"			INT REFERENCES users NOT NULL,
"keyword" 		VARCHAR(200) NOT NULL DEFAULT '',
"positive" 		BOOLEAN NOT NULL DEFAULT true
);


CREATE TABLE reminders (
"rid"			SERIAL PRIMARY KEY,
"uid"			INT REFERENCES users NOT NULL,
"name"                  VARCHAR(200) NOT NULL,
"email"		        VARCHAR(200) NOT NULL,
"birthday"		INT NULL,
"birthmonth"		INT NULL,
"birthyear"		INT NULL,
"next_date"		TIMESTAMP NOT NULL,
"periodicity"		VARCHAR(20) NOT NULL,
"snooze"		INT NOT NULL DEFAULT 0,
"paused_date"		TIMESTAMP NOT NULL DEFAULT 'infinity',
"add_date"		TIMESTAMP NOT NULL DEFAULT NOW(),
"modify_date"		TIMESTAMP NOT NULL DEFAULT NOW()
);

CREATE TABLE sent_reminders (
"srid"			SERIAL PRIMARY KEY,
"rid"			INT REFERENCES reminders NOT NULL,
"snoozed"  	        INT NOT NULL DEFAULT 0,
"add_date"		TIMESTAMP NOT NULL DEFAULT NOW()
);

CREATE TABLE sent_invitations (
"siid"			SERIAL PRIMARY KEY,
"uid"			INT REFERENCES users NOT NULL,
"email"  	        VARCHAR(100) NOT NULL,
"name"  	        VARCHAR(100) NOT NULL,
"html_email"		BOOLEAN NOT NULL DEFAULT false,
"periodicity"  	        VARCHAR(20) NOT NULL,
"clicked_link" 	        BOOLEAN NOT NULL DEFAULT false,
"send_date"		TIMESTAMP NOT NULL DEFAULT '-infinity',
"add_date"		TIMESTAMP NOT NULL DEFAULT NOW()
);

