from django import template
from django.conf import settings
from massmedia.models import VoxantVideo

register = template.Library()

def show_media(media):
    return media.get_template().render(template.Context({
        'media':media,
        'MEDIA_URL':settings.MEDIA_URL
    }))
    
def voxant(asset_id):
    return show_media(VoxantVideo.objects.get(asset_id=asset_id))
    
register.simple_tag(show_media)
register.simple_tag(voxant)