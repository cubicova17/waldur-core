%define __conf_dir %{_sysconfdir}/waldur
%define __conf_file %{__conf_dir}/core.ini
%define __data_dir %{_datadir}/waldur
%define __log_dir %{_localstatedir}/log/waldur
%define __user waldur
%define __work_dir %{_sharedstatedir}/waldur

%define __celery_conf_file %{__conf_dir}/celery.conf
%define __celery_service_name waldur-celery
%define __celery_systemd_unit_file %{_unitdir}/%{__celery_service_name}.service
%define __celerybeat_service_name waldur-celerybeat
%define __celerybeat_systemd_unit_file %{_unitdir}/%{__celerybeat_service_name}.service

%define __logrotate_dir %{_sysconfdir}/logrotate.d
%define __logrotate_conf_file %{__logrotate_dir}/waldur

%define __uwsgi_service_name waldur-uwsgi
%define __uwsgi_conf_file %{__conf_dir}/uwsgi.ini
%define __uwsgi_systemd_unit_file %{_unitdir}/%{__uwsgi_service_name}.service

Name: waldur-core
Summary: Waldur Core
Version: 0.161.4
Release: 1.el7
License: MIT

# python-django-cors-headers is packaging-specific dependency; it is not required in upstream code
# mailcap is required for /etc/mime.types of static files served by uwsgi
Requires: logrotate
Requires: mailcap
Requires: python-celery = 4.1.0
Requires: python-country >= 1.20, python-country < 2.0
Requires: python-croniter >= 0.3.4, python-croniter < 0.3.6
Requires: python-cryptography
Requires: python-django >= 1.11, python-django < 2.0
Requires: python-django-admin-tools = 0.8.0
Requires: python-django-cors-headers = 2.1.0
Requires: python-django-defender >= 0.5.3
Requires: python-django-filter = 1.0.2
Requires: python-django-fluent-dashboard = 0.6.1
Requires: python-django-fsm = 2.3.0
Requires: python-django-jsoneditor >= 0.0.7
Requires: python-django-model-utils = 3.0.0
Requires: python-django-redis-cache >= 1.6.5
Requires: python-django-rest-framework >= 3.6.3, python-django-rest-framework < 3.7.0
Requires: python-django-rest-swagger = 2.1.2
Requires: python-django-reversion = 2.0.8
Requires: python-django-taggit >= 0.20.2
Requires: python-elasticsearch = 5.4.0
Requires: python-hiredis >= 0.2.0
Requires: python-iptools >= 0.6.1
Requires: python-pillow >= 2.0.0
Requires: python-prettytable >= 0.7.1, python-prettytable < 0.8
Requires: python-psycopg2 >= 2.5.4
Requires: python-redis = 2.10.6
Requires: python-requests >= 2.6.0
Requires: python-sqlparse >= 0.1.11
Requires: python-tlslite = 0.4.8
Requires: python-urllib3 >= 1.10.1
Requires: python-vat >= 1.3.1, python-vat < 2.0
Requires: PyYAML
Requires: uwsgi-plugin-python

Source0: %{name}-%{version}.tar.gz

BuildArch: noarch
BuildRoot: %{_tmppath}/%{name}-%{version}-%{release}-buildroot

# gettext package is needed to run 'django-admin compilemessages'
# python-django* packages are needed to generate static files
# python-setuptools package is needed to run 'python setup.py <cmd>'
# systemd package provides _unitdir RPM macro
BuildRequires: gettext
BuildRequires: python-django >= 1.11, python-django < 2.0
BuildRequires: python-django-filter = 1.0.2
BuildRequires: python-django-fluent-dashboard
BuildRequires: python-django-jsoneditor >= 0.0.7
BuildRequires: python-django-rest-framework >= 3.6.3, python-django-rest-framework < 3.7.0
BuildRequires: python-django-rest-swagger = 2.1.2
BuildRequires: python-setuptools
BuildRequires: systemd

%description
Waldur Core is an open-source RESTful server for multi-tenant resource
management. It provides an easy way for sharing access to external systems.
It is used as a platform for creating private and public clouds.

Additional information can be found at http://docs.waldur.com.

%prep
%setup -q -n %{name}-%{version}

%build
cp packaging/settings.py waldur_core/server/settings.py
django-admin compilemessages
%{__python} setup.py build

%install
rm -rf %{buildroot}
%{__python} setup.py install -O1 --root=%{buildroot}

mkdir -p %{buildroot}%{_unitdir}
cp packaging%{__celery_systemd_unit_file} %{buildroot}%{__celery_systemd_unit_file}
cp packaging%{__celerybeat_systemd_unit_file} %{buildroot}%{__celerybeat_systemd_unit_file}
cp packaging%{__uwsgi_systemd_unit_file} %{buildroot}%{__uwsgi_systemd_unit_file}

mkdir -p %{buildroot}%{__conf_dir}
cp packaging%{__celery_conf_file} %{buildroot}%{__celery_conf_file}
cp packaging%{__conf_file} %{buildroot}%{__conf_file}
cp packaging%{__uwsgi_conf_file} %{buildroot}%{__uwsgi_conf_file}

mkdir -p %{buildroot}%{__data_dir}/static
cat > tmp_settings.py << EOF
# Minimal settings required for 'collectstatic' command
INSTALLED_APPS = (
    'admin_tools',
    'admin_tools.dashboard',
    'admin_tools.menu',
    'admin_tools.theming',
    'fluent_dashboard',  # should go before 'django.contrib.admin'
    'django.contrib.contenttypes',
    'django.contrib.admin',
    'django.contrib.staticfiles',
    'jsoneditor',
    'waldur_core.landing',
    'rest_framework',
    'rest_framework_swagger',
    'django_filters',
)
SECRET_KEY = 'tmp'
STATIC_ROOT = '%{buildroot}%{__data_dir}/static'
STATIC_URL = '/static/'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': ['waldur_core/templates'],
        'OPTIONS': {
            'context_processors': (
                'django.template.context_processors.debug',
                'django.template.context_processors.request',  # required by django-admin-tools >= 0.7.0
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
                'django.template.context_processors.i18n',
                'django.template.context_processors.media',
                'django.template.context_processors.static',
                'django.template.context_processors.tz',
            ),
            'loaders': (
                'django.template.loaders.filesystem.Loader',
                'django.template.loaders.app_directories.Loader',
                'admin_tools.template_loaders.Loader',  # required by django-admin-tools >= 0.7.0
            ),
        },
    },
]
EOF
PYTHONPATH="${PYTHONPATH}:src" %{__python} manage.py collectstatic --noinput --settings=tmp_settings

mkdir -p %{buildroot}%{__log_dir}

mkdir -p %{buildroot}%{__logrotate_dir}
cp packaging%{__logrotate_conf_file} %{buildroot}%{__logrotate_conf_file}

mkdir -p %{buildroot}%{__work_dir}/media

%clean
rm -rf %{buildroot}

%files
%defattr(-,root,root,-)
%{python_sitelib}/*
%{_bindir}/*
%{_unitdir}/*
%{__data_dir}
%{__logrotate_dir}/*
%attr(0750,%{__user},%{__user}) %{__log_dir}
%attr(0750,%{__user},%{__user}) %{__work_dir}
%config(noreplace) %{__celery_conf_file}
%config(noreplace) %{__conf_file}
%config(noreplace) %{__uwsgi_conf_file}

%pre
# User must exist in the system before package installation, otherwise setting file permissions will fail
if ! id %{__user} 2> /dev/null > /dev/null; then
    echo "[%{name}] Adding new system user %{__user}..."
    useradd --home %{__work_dir} --shell /bin/sh --system --user-group %{__user}
fi

%post
%systemd_post %{__celery_service_name}.service
%systemd_post %{__celerybeat_service_name}.service
%systemd_post %{__uwsgi_service_name}.service

if [ "$1" = 1 ]; then
    # This package is being installed for the first time
    echo "[%{name}] Generating secret key..."
    sed -i "s,{{ secret_key }},$(head -c32 /dev/urandom | base64)," %{__conf_file}
fi

cat <<EOF
------------------------------------------------------------------------
Waldur Core installed successfully.

Next steps:

1. Configure database server connection in %{__conf_file}.
   Database server (PostgreSQL) must be running already.

2. Configure task queue backend connection in %{__conf_file}.
   Key-value store (Redis) must be running already.

3. Review and modify other settings in %{__conf_file}.

4. Create database (if not yet done):

     CREATE DATABASE waldur ENCODING 'UTF8';
     CREATE USER waldur WITH PASSWORD 'waldur';

5. Migrate the database:

     su - %{__user} -c "waldur migrate --noinput"

   Note: you will need to run this again on next Waldur Core update.

6. Start Waldur Core services:

     systemctl start %{__celery_service_name}
     systemctl start %{__celerybeat_service_name}
     systemctl start %{__uwsgi_service_name}

7. Create first superuser (if needed and not yet done):

     su - %{__user} -c "waldur createsuperuser"

All done.
------------------------------------------------------------------------
EOF

%preun
%systemd_preun %{__celery_service_name}.service
%systemd_preun %{__celerybeat_service_name}.service
%systemd_preun %{__uwsgi_service_name}.service

%postun
%systemd_postun_with_restart %{__celery_service_name}.service
%systemd_postun_with_restart %{__celerybeat_service_name}.service
%systemd_postun_with_restart %{__uwsgi_service_name}.service

%changelog
* Wed Jul 4 2018 Jenkins <jenkins@opennodecloud.com> - 0.161.4-1.el7
- New upstream release

* Sun Jun 24 2018 Jenkins <jenkins@opennodecloud.com> - 0.161.3-1.el7
- New upstream release

* Tue Jun 19 2018 Jenkins <jenkins@opennodecloud.com> - 0.161.2-1.el7
- New upstream release

* Mon Jun 18 2018 Jenkins <jenkins@opennodecloud.com> - 0.161.1-1.el7
- New upstream release

* Mon Jun 11 2018 Jenkins <jenkins@opennodecloud.com> - 0.161.0-1.el7
- New upstream release

* Fri Jun 1 2018 Jenkins <jenkins@opennodecloud.com> - 0.160.3-1.el7
- New upstream release

* Mon May 28 2018 Jenkins <jenkins@opennodecloud.com> - 0.160.2-1.el7
- New upstream release

* Sat May 26 2018 Jenkins <jenkins@opennodecloud.com> - 0.160.1-1.el7
- New upstream release

* Tue May 22 2018 Jenkins <jenkins@opennodecloud.com> - 0.160.0-1.el7
- New upstream release

* Thu May 17 2018 Jenkins <jenkins@opennodecloud.com> - 0.159.2-1.el7
- New upstream release

* Wed May 16 2018 Jenkins <jenkins@opennodecloud.com> - 0.159.1-1.el7
- New upstream release

* Thu May 10 2018 Jenkins <jenkins@opennodecloud.com> - 0.159.0-1.el7
- New upstream release

* Mon May 7 2018 Jenkins <jenkins@opennodecloud.com> - 0.158.0-1.el7
- New upstream release

* Tue Apr 17 2018 Jenkins <jenkins@opennodecloud.com> - 0.157.5-1.el7
- New upstream release

* Mon Apr 16 2018 Jenkins <jenkins@opennodecloud.com> - 0.157.4-1.el7
- New upstream release

* Sun Apr 8 2018 Jenkins <jenkins@opennodecloud.com> - 0.157.3-1.el7
- New upstream release

* Wed Apr 4 2018 Jenkins <jenkins@opennodecloud.com> - 0.157.2-1.el7
- New upstream release

* Wed Mar 28 2018 Jenkins <jenkins@opennodecloud.com> - 0.157.1-1.el7
- New upstream release

* Sat Mar 24 2018 Jenkins <jenkins@opennodecloud.com> - 0.157.0-1.el7
- New upstream release

* Thu Mar 1 2018 Jenkins <jenkins@opennodecloud.com> - 0.156.2-1.el7
- New upstream release

* Mon Feb 26 2018 Jenkins <jenkins@opennodecloud.com> - 0.156.1-1.el7
- New upstream release

* Mon Feb 19 2018 Jenkins <jenkins@opennodecloud.com> - 0.156.0-1.el7
- New upstream release

* Wed Feb 14 2018 Jenkins <jenkins@opennodecloud.com> - 0.155.3-1.el7
- New upstream release

* Tue Feb 13 2018 Jenkins <jenkins@opennodecloud.com> - 0.155.2-1.el7
- New upstream release

* Mon Feb 12 2018 Jenkins <jenkins@opennodecloud.com> - 0.155.1-1.el7
- New upstream release

* Sun Feb 11 2018 Jenkins <jenkins@opennodecloud.com> - 0.155.0-1.el7
- New upstream release

* Sat Feb 3 2018 Jenkins <jenkins@opennodecloud.com> - 0.154.0-1.el7
- New upstream release

* Sat Jan 20 2018 Jenkins <jenkins@opennodecloud.com> - 0.153.0-1.el7
- New upstream release

* Sat Jan 13 2018 Jenkins <jenkins@opennodecloud.com> - 0.152.0-1.el7
- New upstream release

* Wed Dec 27 2017 Jenkins <jenkins@opennodecloud.com> - 0.151.3-1.el7
- New upstream release

* Fri Dec 22 2017 Jenkins <jenkins@opennodecloud.com> - 0.151.2-1.el7
- New upstream release

* Tue Dec 19 2017 Jenkins <jenkins@opennodecloud.com> - 0.151.1-1.el7
- New upstream release

* Fri Dec 1 2017 Jenkins <jenkins@opennodecloud.com> - 0.151.0-1.el7
- New upstream release

* Mon Nov 27 2017 Jenkins <jenkins@opennodecloud.com> - 0.150.5-1.el7
- New upstream release

* Mon Nov 27 2017 Jenkins <jenkins@opennodecloud.com> - 0.150.4-1.el7
- New upstream release

* Fri Nov 24 2017 Jenkins <jenkins@opennodecloud.com> - 0.150.3-1.el7
- New upstream release

* Tue Nov 21 2017 Jenkins <jenkins@opennodecloud.com> - 0.150.2-1.el7
- New upstream release

* Wed Nov 15 2017 Jenkins <jenkins@opennodecloud.com> - 0.150.1-1.el7
- New upstream release

* Wed Nov 8 2017 Jenkins <jenkins@opennodecloud.com> - 0.150.0-1.el7
- New upstream release

* Wed Nov 1 2017 Jenkins <jenkins@opennodecloud.com> - 0.149.3-1.el7
- New upstream release

* Mon Oct 30 2017 Jenkins <jenkins@opennodecloud.com> - 0.149.2-1.el7
- New upstream release

* Sun Oct 29 2017 Jenkins <jenkins@opennodecloud.com> - 0.149.1-1.el7
- New upstream release

* Tue Oct 24 2017 Jenkins <jenkins@opennodecloud.com> - 0.149.0-1.el7
- New upstream release

* Mon Oct 16 2017 Jenkins <jenkins@opennodecloud.com> - 0.148.3-1.el7
- New upstream release

* Tue Oct 3 2017 Jenkins <jenkins@opennodecloud.com> - 0.148.2-1.el7
- New upstream release

* Sat Sep 30 2017 Jenkins <jenkins@opennodecloud.com> - 0.148.1-1.el7
- New upstream release

* Wed Sep 27 2017 Jenkins <jenkins@opennodecloud.com> - 0.148.0-1.el7
- New upstream release

* Wed Sep 27 2017 Jenkins <jenkins@opennodecloud.com> - 0.147.1-1.el7
- New upstream release

* Wed Sep 20 2017 Jenkins <jenkins@opennodecloud.com> - 0.147.0-1.el7
- New upstream release

* Tue Sep 19 2017 Jenkins <jenkins@opennodecloud.com> - 0.146.5-1.el7
- New upstream release

* Wed Sep 13 2017 Jenkins <jenkins@opennodecloud.com> - 0.146.4-1.el7
- New upstream release

* Wed Sep 13 2017 Jenkins <jenkins@opennodecloud.com> - 0.146.3-1.el7
- New upstream release

* Mon Sep 4 2017 Jenkins <jenkins@opennodecloud.com> - 0.146.2-1.el7
- New upstream release

* Fri Sep 1 2017 Jenkins <jenkins@opennodecloud.com> - 0.146.1-1.el7
- New upstream release

* Wed Aug 23 2017 Jenkins <jenkins@opennodecloud.com> - 0.146.0-1.el7
- New upstream release

* Wed Aug 16 2017 Jenkins <jenkins@opennodecloud.com> - 0.145.5-1.el7
- New upstream release

* Sat Aug 12 2017 Jenkins <jenkins@opennodecloud.com> - 0.145.4-1.el7
- New upstream release

* Fri Aug 11 2017 Jenkins <jenkins@opennodecloud.com> - 0.145.3-1.el7
- New upstream release

* Tue Aug 8 2017 Jenkins <jenkins@opennodecloud.com> - 0.145.2-1.el7
- New upstream release

* Sun Aug 6 2017 Jenkins <jenkins@opennodecloud.com> - 0.145.1-1.el7
- New upstream release

* Sun Aug 6 2017 Jenkins <jenkins@opennodecloud.com> - 0.145.0-1.el7
- New upstream release

* Tue Aug 1 2017 Jenkins <jenkins@opennodecloud.com> - 0.144.0-1.el7
- New upstream release

* Mon Jul 17 2017 Jenkins <jenkins@opennodecloud.com> - 0.143.3-1.el7
- New upstream release

* Thu Jul 13 2017 Jenkins <jenkins@opennodecloud.com> - 0.143.2-1.el7
- New upstream release

* Thu Jul 13 2017 Jenkins <jenkins@opennodecloud.com> - 0.143.1-1.el7
- New upstream release

* Wed Jul 12 2017 Jenkins <jenkins@opennodecloud.com> - 0.143.0-1.el7
- New upstream release

* Mon Jul 3 2017 Jenkins <jenkins@opennodecloud.com> - 0.142.2-1.el7
- New upstream release

* Fri Jun 30 2017 Jenkins <jenkins@opennodecloud.com> - 0.142.1-1.el7
- New upstream release

* Tue Jun 27 2017 Juri Hudolejev <juri@opennodecloud.com> - 0.142.0-1
- Rename package to Waldur Core
