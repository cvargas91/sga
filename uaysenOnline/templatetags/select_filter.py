from django.template import Library
from django.template.loader import get_template

register = Library()


@register.simple_tag
def admin_select_filter(cl, spec):
    tpl = get_template('admin/admin_list_select_filter.html')
    return tpl.render({
        'title': spec.title,
        'choices': list(spec.choices(cl)),
        'spec': spec,
    })
