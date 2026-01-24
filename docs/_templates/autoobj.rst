{% set domain = _sphinx.registry.domains[name[0]] %}
{% set dir = domain.directives[name[1]] %}
{% set roles = domain.roles %}
{% set schema = domain.schemas[name[1]] %}
{% set dispname = name[1] %}

Directive for documenting ``{{ dispname }}`` object:

.. role:: py(code)
   :language: Python

.. rst:directive:: .. {{ dispname }}:: {% if schema.name %}name ({{ schema.name }}){% endif %}

   {% for attr, field in schema.attrs.items() %}
   .. rst:directive:option:: {{ attr }}
      :type: {{ field }}
   {% endfor %}

   {% if schema.content %}content ({{ schema.content }}){% endif %}

Cross-reference roles for referencing a ``{{ dispname }}`` object:

{% if schema.name.ref %}
.. rst:role:: {{ dispname }}
   
   Referencing a {{ dispname }} object by name.
{% endif %}

{% for attr, field in schema.attrs.items() %}
{% if field.ref %}
.. rst:role:: {{ dispname }}.{{ attr }}
   
   Referencing a {{ dispname }} object by attribute "{{ attr}}".
{% endif %}
{% endfor %}
