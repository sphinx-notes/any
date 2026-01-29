=============
Configuration
=============

The extension provides the following configuration:

.. autoconfval:: any_domain_name

   The name of the domain.

.. autoconfval:: any_object_types

   A dictionary ``dict[str, objdef]`` of object type definitions.

   The ``str`` key is the object type;
   The ``objdef`` vaule is a ``dict``,
   please refer to :ref:`writing-objdef` for more details.

.. autoconfval:: any_domain_dump

   Whether dump domain data to :file:`$DOCTREE_DIR/$OBJ_DOMAIN_NAME-objects.json`.

   The ``$DOCTREE_DIR`` is usually :file:`_build/doctrees/`.
   The ``$OBJ_DOMAIN_NAME`` refers value of :confval:`any_domain_name`.
   (By default, the path is :file:`_build/doctrees/obj-objects.json`)'.
