from django.utils.text import truncate_words
from django.contrib.admin.widgets import ForeignKeyRawIdWidget

class ForeignKeyRawIdImageWidget(ForeignKeyRawIdWidget):
    """
    A Widget for displaying ForeignKeys in the "raw_id" interface and a thumbnail
    rather than in a <select> box.
    """

    def label_for_value(self, value):
        key = self.rel.get_related_field().name
        obj = self.rel.to._default_manager.get(**{key: value})
        return '&nbsp;<strong>%s</strong>&nbsp;%s' % (truncate_words(obj, 14),obj.thumb())