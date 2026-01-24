cat = {
    'schema': {
        'name': 'str, ref, uniq',
        'attrs': {
            'color': 'str, ref',
        },
        'content': 'str'
    },
    'templates': {
        'obj':"Hi there, human! I've got **{{ color }}** fur.",
        'header': '🐈 {{ name }}',
        'ref': '``🐈 {{ name }}``',
    }
}

