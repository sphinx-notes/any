from textwrap import dedent

dog = {
    'schema': {
        'attrs': {
            'breed': 'str, ref',
            'colors': 'words of str, ref',
        },
    },
    'templates': {
        'obj': dedent("""
                :Breed: {{ breed }}
                :Colors: {{ colors }}"""),
        'ref': '🐕{{ title }}',
    },
}
