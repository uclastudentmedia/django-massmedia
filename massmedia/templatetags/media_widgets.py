from django import template
from django.conf import settings

register = template.Library()

def show_media(media):
    return media.get_template().render(template.Context({
        'media':media,
        'MEDIA_URL':settings.MEDIA_URL
    }))
    
register.simple_tag(show_media)