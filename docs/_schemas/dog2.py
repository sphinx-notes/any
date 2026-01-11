from textwrap import dedent

dog = {
    'schema': {
        'attrs': {
            'breed': 'str, ref',
            'color': 'words of str, ref',
        },
    },
    'templates': {
        'obj': dedent("""
            :Breed: :obj:dog.breed:`{{ breed }}`
            :Colors: {% for c in color %}:obj:dog.color:`{{ c }}` {% endfor %}"""),
        'ref': '🐕{{ title }}',
    },
}
