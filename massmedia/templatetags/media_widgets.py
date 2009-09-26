from django import template
from django.conf import settings
from massmedia import settings as appsettings

if appsettings.USE_VOXANT:
    from massmedia.models import VoxantVideo

register = template.Library()

class MassMediaNode(template.Node):
    def __init__(self, *args):
        assert len(args)
        self.args = list(args)
    
    def render(self, context):
        media = context.get(self.args[0], self.args[0])
        if appsettings.USE_VOXANT and isinstance(media, basestring):
            media = VoxantVideo.objects.get(slug=media)
        return media.get_template().render(template.RequestContext(context['request'], {
            'media':media,
        }))
def show_media(parser, token):
    return MassMediaNode(*token.contents.split()[1:])
    
register.tag(show_media)
