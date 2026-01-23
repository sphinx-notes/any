{% set opt = _sphinx.config.values[name] %}

.. role:: py(code)
   :language: Python

{% set types = [] %}
{% for t in opt.valid_types %}
   {# "<class 'str'>" → "str" #}
   {% set t = t | string %}
   {% do types.append(t[8:-2]) %}
{% endfor %}

:Type: {{ types | roles('py') | join(',') }}
:Default: :py:`{{ opt.default | pprint }}`

{{ opt.description }}
