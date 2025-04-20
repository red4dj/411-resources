DROP TABLE IF EXISTS songs;
CREATE TABLE songs (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    artist TEXT NOT NULL,
    title TEXT NOT NULL,
    year INTEGER NOT NULL CHECK(year >= 1900),
    genre TEXT NOT NULL,
    duration INTEGER NOT NULL CHECK(duration > 0),
    play_count INTEGER DEFAULT 0,
    UNIQUE(artist, title, year)
);

CREATE INDEX idx_songs_artist_title ON songs(artist, title);
CREATE INDEX idx_songs_year ON songs(year);
CREATE INDEX idx_songs_play_count ON songs(play_count);