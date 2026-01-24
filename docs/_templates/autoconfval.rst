{% set opt = _sphinx.config.values[name] %}

.. role:: py(code)
   :language: Python

{% set types = [] %}
{% for t in opt.valid_types %}
   {# "<class 'str'>" → "str" #}
   {% set t = t | string %}
   {% do types.append(t[8:-2]) %}
{% endfor %}

.. confval:: {{ name }}
   :type: {{ types | roles('py') | join(',') }}
   :default: :py:`{{ opt.default | pprint }}`

   {% for line in opt.description.split('\n') -%}
   {{ line }}
   {% endfor %}
