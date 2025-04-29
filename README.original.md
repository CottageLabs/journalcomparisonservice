# Journal Comparison Service

This is a Django 3.2.13 data management system using Postgres and Elasticsearch. 
Using a modified [Volt](https://themesberg.com/product/django/volt-admin-dashboard-template) template.

## Deployment

Docker is used for development, see `docker-compose.yml`.

For deploying on server, the folder `deploy` contains configuration
for nginx and uwsgi as a service. These should be symlinked.

1. Pull the latest code

    `git pull`
   and 
    `git submodule update --init --recursive` (this is for [Edges](https://github.com/CottageLabs/edges)) 
2. Activate virtualenv

    `source venv/bin/activate`
3. Install Python libraries if required

    `pip install -r requirements.txt`
4. Migrate
 
    `python manage.py migrate`
5. Generate static files

    `python manage.py collectstatic`
6. Give uwsgi a kick

    `sudo systemctl restart uwsgi.service`

You should never have to run `makemigrations` on any deployment server. Migrations 
should be done locally and committed.

There are a couple of management commands in order to populate data. These only
need to be run once, after initial deployment.

1. Create groups (these are the user groups)
 
    `python manage.py create_groups`
2. Create services and trade bodies (values for select dropdowns in forms)

    `python manage.py create_services_and_trade_bodies`

Both of the above commands need to be run in virtualenv.

If you are nervous you can stop uwsgi by doing
`sudo systemctl stop uwsgi.service` before step 1 and then 
`sudo systemctl start uwsgi.service` instead of step 6.
 
Note: it's a bit unclear if we need to run gulp build (as suggested 
[here](https://themesberg.com/docs/volt-bootstrap-5-dashboard/getting-started/quick-start/))
or if outputted files are being committed 


## Maintenance

In order to maintain and update the Elastic Search index you need
to run:

`python manage.py build_index`

In order to generate the zipped data for download there needs to be
a dedicated process:

`python manage.py scheduled_data_dump`


### Logging
Because the app is deployed using multiple processes/workers it is not possible to use file logging handlers. To
overcome this problem we will deploy three different local TCP logging servers, see 
[log_listener](https://github.com/CottageLabs/log_listener).

Django config will be configured to point to these three listeners depending on the  logging purposes.

1. `$ python3 log_listener.py -fn /home/cloo/log_listener/logs/pstf_app.log`: this will log all non-Django modules
except `data.audit_log`
2. `$ python3 log_listener.py -p 9021 -fn /home/cloo/log_listener/logs/pstf_django.log`: this will log all Django
modules
3.  `$ python3 log_listener.py -p 9022 -fn /home/cloo/log_listener/logs/pstf_audit.log`: this will log all logs from
`data.audit_log` class for audit purposes 


### Access to /admin

NGINX blocks all ips requesting `/admin` except localhost.

In order to access Django admin you need to SSH tunnel into the server

`$ ssh -L 8005:localhost:443 -N pstf-test `

and then you can access Django admin via:

`https://localhost:8005/admin/`

There will be a cert warning, http won't work.

### Configuring NGINX-Unit
Nginx-Unit runs by uploading config [documentation](https://unit.nginx.org/configuration/) to it via a Unix socket:

`$ sudo curl -X PUT --data-binary @/path/to/config.json --unix-socket /run/control.unit.sock http://localhost/config/applications/django`

This command will create/update config for the application "django".

`$ sudo curl -X GET --unix-socket /run/control.unit.sock http://localhost/control/applications/django/restart`

This command will restart the application only.

`$ sudo curl --unix-socket /run/control.unit.sock http://localhost/config`

This commmand will simply retrieve current config (all apps).