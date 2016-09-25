from sqlalchemy import Column, ForeignKey, Integer, String
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship
from sqlalchemy import create_engine

Base = declarative_base()


class User(Base):
    __tablename__ = 'user'

    id = Column(Integer, primary_key=True)
    name = Column(String(250), nullable=False)
    email = Column(String(250), nullable=False)
    picture = Column(String(250))


class Playlist(Base):
    __tablename__ = 'playlist'

    id = Column(Integer, primary_key=True)
    name = Column(String(250), nullable=False)
    description = Column(String(250), nullable=False)
    user_id = Column(Integer, ForeignKey('user.id'))
    user = relationship(User)

    @property
    def serialize(self):
        """Return object data in easily serializeable format"""
        return {
            'id': self.id,
            'name': self.name,
            'description': self.description,
        }


class Song(Base):
    __tablename__ = 'song'

    title = Column(String(80), nullable=False)
    id = Column(Integer, primary_key=True)
    artist = Column(String(250), nullable=False)
    spotify_url = Column(String(250))
    deezer_url = Column(String(250))
    apple_music_url = Column(String(250))
    youtube_url = Column(String(250))

    @property
    def serialize(self):
        """Return object data in easily serializeable format"""
        return {
            'id': self.id,
            'title': self.title,
            'artist': self.artist,
            'spotify_url': self.spotify_url,
            'deezer_url': self.deezer_url,
            'apple_music_url': self.apple_music_url,
            'youtube_url': self.youtube_url,
        }


class PlaylistSongs(Base):
    # Creates a connection "many to many" between a playlist and a song as a
    # song can be used in many different playlists
    __tablename__ = 'playlistsongs'
    id = Column(Integer, primary_key=True) # is built with playlist_id + song_id in order to create an unique id
    song_id = Column(Integer, ForeignKey('song.id'))
    playlist_id = Column(Integer, ForeignKey('playlist.id'))
    song = relationship(Song)
    playlist = relationship(Playlist)
    user_id = Column(Integer, ForeignKey('user.id'))
    user = relationship(User)

    @property
    def serialize(self):
        """Return object data in easily serializeable format"""
        return {
            'id': self.id,
            'song_id': self.song_id,
            'playlist_id': self.playlist_id,
        }

engine = create_engine('sqlite:///mixxtape.db')


Base.metadata.create_all(engine)
