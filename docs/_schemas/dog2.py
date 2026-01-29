from textwrap import dedent

dog = {
    'schema': {
        'attrs': {
            'breed': 'str, ref',
            'color': 'words of str',
        },
    },
    'templates': {
        'obj': dedent("""
            :Breed: :any:dog.breed:`{{ breed }}`
            :Colors: {% for c in color %}:any:dog.color:`{{ c }}` {% endfor %}"""),
        'ref': '🐕{{ title }}',
    },
}
