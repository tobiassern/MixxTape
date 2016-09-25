## Synopsis

This is a project created for the Fullstack Nanodegree Item Catalog project.

Users can create playlists and add songs to their playlists. Which they can share with the world through facebook or twitter.

When creating songs users can add links to spotify, deezer, apple music and youtube in order for the ones visiting the song to use the streaming service that suits them best.

Songs are not owned by any user and thus can be added to any playlist when created.

If a user removes a song from their playlist the song will not be deleted as it can be used in other playlists

All users can contribute and edit a song another user has created in order to fix spellingerrors or adding / updating streaming links.

## Motivation

This project enhanced my skills in python in general but sql, sqllite, sqlalchemy, json api endpoints, oAuth and social logins specifically.

I also implemented for the fun of it a basic search function.

## Installation

This project is built using Vagrant
A file for vagrant is already included in the files

### Setting up vagrant
If you are new to vagrant you can see the docs here https://www.vagrantup.com/docs/getting-started/


If you are familiar with vagrant and created your own Google Ouath Credentials do this

## Running this project

1. Download this github project
2. Download the JSON file from your Google Oauth 2.0 Client's ID
3. Save the json file as client_secrets.json in the main folder (where main.py is)
4. Run vagrant up in the folder
5. The run vagrant ssh
6. Go to /vagrant/lib
7. Run $ python database_setup.py
8. Go to /vagrant
9. Run $ python main.py

The project can now be reached at localhost:5600

# License

The MIT License (MIT)