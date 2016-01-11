==========
 Examples
==========


It also works with existing Sphinx highlighting:

.. code-block:: html

    <html>
      <body>Hello World</body>
    </html>

.. code-block:: python

    def hello():
        """Greet."""
        return "Hello World"


Code Documentation
==================

An example Python function.

.. py:function:: format_exception(etype, value, tb[, limit=None])

   Format the exception with a traceback.

   :param etype: exception type
   :param value: exception value
   :param tb: traceback object
   :param limit: maximum number of stack frames to show
   :type limit: integer or None
   :rtype: list of strings
