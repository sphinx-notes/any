cat = {
    'schema': {
        'attrs': {
            'color': 'str, ref',
        },
    },
    'templates': {
        'header': '🐈 ``{{ name }}``',
        'content':"Hi there, human! I am {{ name }}. I've got {{ color }} fur.",
        'ref': '🐈 ``{{ name }}``',
    }
}

