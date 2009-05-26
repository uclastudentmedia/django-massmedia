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
        self.args[0] = context.get(self.args[0],self.args[0])
        if appsettings.USE_VOXANT and isinstance(self.args[0], basestring):
            self.args[0] = VoxantVideo.objects.get(slug=self.args[0])
        return self.args[0].get_template().render(template.RequestContext(context['request'], {
        'media':self.args[0],
    }))
def show_media(parser, token):
    return MassMediaNode(*token.contents.split()[1:])
    
register.tag(show_media)
