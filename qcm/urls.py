from django.conf.urls import patterns, include, url
from django.conf.urls.static import static
from django.conf import settings
from django.contrib import admin
admin.autodiscover()

urlpatterns = patterns('',
    # Examples:
    # url(r'^$', 'qcm.views.home', name='home'),
    # url(r'^blog/', include('blog.urls')),
	url(r'^$', 'prof.views.home'),
	url(r'^eleve', 'prof.views.ehome'),
    url(r'^admin/', include(admin.site.urls)),
    url(r'^qcmaker','prof.views.qcmaker'),
    url(r'^qcmanage','prof.views.qcmanage'),
    url(r'^makexo','prof.views.makexo'),
    url(r'^banque','prof.views.banque'),
    url(r'^copie','prof.views.voircopie'),
    url(r'^ecopie','prof.views.evoircopie'),
    url(r'^image/(?P<id_cc>\d+)/(?P<page>\d+)','prof.views.image'),
    url(r'^svg/(?P<id_svg>\d+)/(?P<prefix>\d+)/','prof.views.svg'),
    url(r'^login', 'django_cas.views.login'), 
    url(r'^logout', 'django_cas.views.logout'), 
)


urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
