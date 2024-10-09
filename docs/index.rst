.. This file is generated from sphinx-notes/cookiecutter.
   You need to consider modifying the TEMPLATE or modifying THIS FILE.

===============
sphinxnotes-any
===============

Role:

:rrr:`Hey!`


Directive:

.. ddd:: Hey!

   I am here.

.. autoclass:: jinja.context.NodeAdapter
   :members:

.. template:: git
   :extra: env app json:xxx.json

   {% for r in revisions %}
   :{{ r.date | strftime }}:
      {% if r.modification %}
      - 修改了 {{ r.modification | roles("doc") | join("、") }}
      {% endif %}
      {% if r.addition %}
      - 新增了 {{ r.addition | roles("doc") | join("、") }}
      {% endif %}
      {% if r.deletion %}
      - 删除了 {{ r.deletion | join("、") }}
      {% endif %}
   {% endfor %}
