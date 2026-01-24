{% if style is not defined or style == 'tab' %}
.. tab-set::

   .. tab-item:: Result

      {% for line in content %}{{ line }}
      {% endfor %}

   .. tab-item:: reStructuredText

      .. code:: rst

         {% for line in content %}{{ line }}
         {% endfor %}
{% elif style == 'grid'  %}
.. grid:: 2
   :gutter: 1

   .. grid-item::

      .. code:: rst

         {% for line in content.split('\n') -%}
         {{ line }}
         {% endfor %}

   .. grid-item::

      {% for line in content.split('\n') -%}
      {{ line }}
      {% endfor %}

{% endif %}

