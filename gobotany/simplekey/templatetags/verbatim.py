"""
jQuery templates use constructs like:

    {{if condition}} print something{{/if}}

This, of course, completely screws up Django templates,
because Django thinks {{ and }} mean something.

Wrap {% verbatim %} and {% endverbatim %} around those
blocks of jQuery templates and this will try its best
to output the contents with no changes.
"""

from django import template

register = template.Library()


class VerbatimNode(template.Node):

    def __init__(self, text):
        self.text = text
    
    def render(self, context):
        return self.text

# From https://gist.github.com/629508

@register.tag
def verbatim(parser, token):
    text = []
    while 1:
        token = parser.tokens.pop(0)
        if token.contents == 'endverbatim':
            break
        if token.token_type == template.TOKEN_VAR:
            text.append('{{')
        elif token.token_type == template.TOKEN_BLOCK:
            text.append('{%')
        text.append(token.contents)
        if token.token_type == template.TOKEN_VAR:
            text.append('}}')
        elif token.token_type == template.TOKEN_BLOCK:
            text.append('%}')
    return VerbatimNode(''.join(text))

# Our own variation.

@register.tag
def handlebars(parser, token):
    args = token.split_contents()
    if len(args) > 2:
        raise template.TemplateSyntaxError(
            "%r tag requires zero or one arguments" % args[0])
    if len(args) == 2:
        attr = ' data-template-name={}'.format(args[1])
    else:
        attr = ''
    text = ['<script type="text/x-handlebars"{}>'.format(attr)]
    while 1:
        token = parser.tokens.pop(0)
        if token.contents == 'endhandlebars':
            break
        if token.token_type == template.TOKEN_VAR:
            text.append('{{')
        elif token.token_type == template.TOKEN_BLOCK:
            text.append('{%')
        text.append(token.contents)
        if token.token_type == template.TOKEN_VAR:
            text.append('}}')
        elif token.token_type == template.TOKEN_BLOCK:
            text.append('%}')
    text.append('</script>')
    return VerbatimNode(''.join(text))
