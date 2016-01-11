==========
 Usage
==========

The aim of this SimpleRST is converting the manual python code, documentations to a restructured text farame.
It parses the code using python built-in module `ast` in order to extracts the classes and functions signature and documentation from code. Then puts them in a RST formated frame. You can use a custome regex to extract the specific
information from your ducumentaion, and put in RST doc. Which it depends on your documentaion format. Following is a
sample ducumentaion and relative regex with rst formatted doc:


.. code-block:: python

  def delUser(self, user_ids, comment, del_connections, del_audit_logs, admin_name):
  """
      delete users with ids in user_ids
      user_ids(list of int): List of user ids
      comment(str): comment when deleting users
      del_connection(bool): tells if we should delete user(s)
      del_audit_logs(bool): tells if we should delete user(s)

      admin_name(str): username of admin that deleted the users

  """

Relative regex:

.. code-block:: python

  regex = re.compile(r'^\s*([^:]*)\(([^)]*)\):(.*)$',re.DOTALL)
  # Extract the matchesd groups
  match_obj = regex.match(part)
      if match_obj:
        name, types, describe = match_obj.group(1, 2, 3)


Output in RST foramt

"""
.. code-block:: python
  
  """
  .. py:attribute:: delUser(['self', 'user_ids', 'comment', 'del_connections', 'del_audit_logs', 'admin_name', 'remote_address'])

     delete users with ids in user_ids

     :param user_ids:  List of user ids
     :type user_ids: list of int
     :param comment:  comment when deleting users
     :type comment: str
     :param del_connection:  tells if we should delete user(s) connection logs too
     :type del_connection: bool
     :param del_audit_logs:  tells if we should delete user(s) audit logs too

     :type del_audit_logs: bool
     :param admin_name:  username of admin that deleted the users
     :type admin_name: str
     :rtype: list of string
  """