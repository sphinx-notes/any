=============
Configuration
=============

The extension provides the following configuration:

.. any:confval:: any_domain_name
   :type: str
   :default: 'any'

   Name of the domain.

.. any:confval:: any_domain_dump
   :type: bool
   :default: 'True'

   Whether dump domain data to ``DOCTREE_DIR/{any_domain_name}-objects.json``
   (default be ``_build/doctrees/any-objects.json``).

   .. versionadded:: 3.0a8

.. any:confval:: any_schemas
   :type: List[sphinxnotes.any.Schema]
   :default: []

   List of :ref:`schema <schema>` instances. For the way of writing schema definition, please refer to :ref:`writing-schema`.
