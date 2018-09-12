from django import template
import markdown
from django.utils.safestring import mark_safe

register = template.Library()

@register.filter
def markdownify(text):
    # safe_mode governs how the function handles raw HTML
    return markdown.markdown(text, safe_mode='escape')

@register.simple_tag
def markdownifyshowcase(text, folder_name):
    text = markdown.markdown(text, safe_mode='escape')
    text = text.replace('src="', 'src="/static/results/%s/' % folder_name) # static image use
    return mark_safe(text)