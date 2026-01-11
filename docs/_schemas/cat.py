from textwrap import dedent

cat = {
    'schema': {
        'name': 'lines of str, ref',
        'attrs': {
            'id': 'str, required, uniq, ref',
            'color': 'str, ref',
            'picture': 'str',
        },
    },
    'templates': {
        'obj': dedent("""
                .. image:: {{ picture }}
                   :align: left

                :Cat ID: {{ id }}
                :Color: {{ color }}

                {{ content }}"""),
        'ref': '🐈{{ title }}',
    }
}
