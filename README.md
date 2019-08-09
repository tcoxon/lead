# ![image](http://i.imgur.com/xKu5vCx.png) Lead - online leaderboard backend

Lead is an online leaderboard backend that presents a REST API for easy access
from your games.

You don't need to run it on a server in order to use it! If you expect not to
get much traffic, you can use the instance on
[lead.bytten.net](http://lead.bytten.net/v1/) -- just send me an email at
[bytten.games@gmail.com](mailto:bytten.games@gmail.com).

If lead seems overkill, maybe you'll be interested in using
[dreamlo](http://dreamlo.com). It looked pretty nice to me, but lacked some big
features I wanted.

## Features

* One instance of lead can serve any number of leaderboards for any number of
games you want it to.
* Simple REST API for listing scores with filtering and sorting on arbitrary
fields. Submitting new scores is just as simple.
* Add arbitrary fields to your score entries. Want to send the player's blood
type along with their score and sort the results by it? Sure, why not!

## Dependencies

* Python 2.7+
* Modules: web.py, psycopg2 -- these can be installed with `pip install -r requirements.txt`
* [Postgres](http://www.postgresql.org/download/)

## Installation

### Set up the database

It's recommended to create a separate user for the leaderboard database. On
Ubuntu you can do this with:

```
$ sudo -u postgres createuser lead
(answer no to all the questions it asks)

$ sudo -u postgres psql

postgres=# \password lead
(set the password for the new user and confirm it)
```

Create a new database for lead:

```
$ sudo -u postgres psql

postgres=# CREATE DATABASE lead;
```

Create the tables that lead uses:

```
$ psql -f db_schema.psql lead
```

### Configure lead

Lead reads its configuration from a file 'config.json' located in the same
directory as the script.

1. Copy and rename config.example.json to config.json. 
2. Edit this JSON file to set your database password.
3. Decide whether to show the usage / API reference page (example:
[http://lead.bytten.net/v1/](http://lead.bytten.net/v1/)). If you don't want to show
this, set the `misc.show_usage` value to `false`.
4. If you are showing the usage page, change the `misc.admin_email` property
to contain your email address. If you would prefer not to display contact
details on your usage page, just set it to `null` (not quoted) and it will not
be sent to the browser.

### Serving

There are two ways to start serving pages. For local development, it is most
convenient to run the lead.py script directly:

```bash
python lead.py 5001
```

That will start serving the API on
[http://localhost:5001](http://localhost:5001).

For a public-facing apache2 server, you can safely run it as a CGI script using
the `ScriptAliasMatch` directive in your config file in
/etc/apache2/sites-enabled/. For example to run it on a subdomain called 'lead':

```
<VirtualHost *:80>
    ServerName lead.YOURDOMAIN.com
    DocumentRoot /var/www/
    ScriptAliasMatch ^(/.*)$ /path/to/lead.py$1
</VirtualHost>
```

Make sure the directory containing lead.py is not public, as that contains your
config.json containing your password! The `ScriptAliasMatch` directive is there
to execute lead.py without making the directory public.

It's all built on top of web.py, so if you like you can follow the instructions
[here](http://webpy.org/install) instead. Just make sure what you do doesn't
make config.json publicly readable!

## Adding games

Before being able to use the API in your game, you'll need to generate keys for
it.

There's currently no script to automate this, but the steps are as follows:

1. Decide on an appid. This is an identifier for your game that will appear
in the URL of REST queries relating to that game. I recommend using the name
of your game, plus a number. The number's there so you can make
backwards-incompatible changes to the leaderboards in new versions of your game
without corrupting and breaking the leaderboards in old versions by adding a
new appid with a different number. For example, for my game, I used 'lenna1'.

2. Generate a writeKey and an adminKey for the game. From the directory
containing lead.py:

```
$ python
Python 2.7.5+ (default, Feb 27 2014, 19:37:08) 
[GCC 4.8.1] on linux2
Type "help", "copyright", "credits" or "license" for more information.
>>> from leadutil import *
>>> randstr(), randstr()
('piqxf62aQIjmR97eaXC5obg2DfmL8wWY', 'HUFfqm5CBoJd71QS8zCTfuRPP3275XvA')
>>> exit()
```

Copy those values somewhere safe. There are recommendations for how to
look after them on [the usage page](http://lead.bytten.net/v1/).

3. Add the game to the database:

```
$ psql lead

lead=# INSERT INTO app (appid, writeKey, adminKey, contact)
lead-#     VALUES ('<your-appid>', '<writeKey>', '<adminKey>', '<contact-info>');
```

The 'contact' field is there in case you want to add other people's games.
Keeping that info alongside the game's ID will make it easy to find out who
you need to contact if the traffic gets too much for your server.

## Usage

For general usage and API documentation, see the root page served by your
instance of lead, or see [here](http://lead.bytten.net/v1/).

Other general pointers:

* Make sure your games' players agree to a suitable privacy policy.

## Contributions

I'm happy to take pull requests. Here are some things I think would have high
value:

* Bug fixes (no known bugs at the moment though)
* Unit tests
* Support for other databases (e.g. Maria/MySQL)
* Install scripts
* A script for adding new games
* Reference frontend (e.g. a web page that loads scores for a leaderboard via
AJAX and displays them in a HTML table)
* Example games

But I will consider any BSD-3-licensed patches you want to throw my way as long
as they doesn't involve XML ;)

Bug reports and complaints are good too!

## FAQ

### How do I use a REST API?

REST is simple. You just send GET / POST requests via HTTP with the parameters
the query/command expects.

I recommend checking out Mashape's awesome open source library,
[unirest](http://unirest.io/) which simplifies this.
