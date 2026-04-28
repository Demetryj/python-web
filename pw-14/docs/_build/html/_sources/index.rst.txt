.. Rest API Contacts documentation master file, created by
   sphinx-quickstart on Tue Apr 28 17:12:06 2026.
   You can adapt this file completely to your liking, but it should at least
   contain the root `toctree` directive.



.. Add your content using ``reStructuredText`` syntax. See the
.. `reStructuredText <https://www.sphinx-doc.org/en/master/usage/restructuredtext/index.html>`_
.. documentation for details.

Rest API Contacts documentation
===============================

.. toctree::
   :maxdepth: 2
   :caption: Contents:

REST API main
===================
.. automodule:: main
  :members:
  :undoc-members:
  :show-inheritance:


REST API routes Auth
=========================
.. automodule:: src.routes.auth
  :members:
  :undoc-members:
  :show-inheritance:


REST API routes Users
==========================
.. automodule:: src.routes.users
  :members:
  :undoc-members:
  :show-inheritance:


REST API routes Contacts
=============================
.. automodule:: src.routes.contacts
  :members:
  :undoc-members:
  :show-inheritance:


REST API repository Auth
=========================
.. automodule:: src.repository.auth
  :members:
  :undoc-members:
  :show-inheritance:


REST API repository Users
==========================
.. automodule:: src.repository.users
  :members:
  :undoc-members:
  :show-inheritance:


REST API repository Contacts
=============================
.. automodule:: src.repository.contacts
  :members:
  :undoc-members:
  :show-inheritance:


REST API database
=================
.. automodule:: src.database.db
  :members:
  :undoc-members:
  :show-inheritance:
  :exclude-members: sessionmanager


REST API models
===============
.. automodule:: src.entity.models
  :members:
  :undoc-members:
  :show-inheritance:


REST API config Rate Limiters
=============================
.. automodule:: src.config.rate_limiters
  :members:
  :undoc-members:
  :show-inheritance:
  :exclude-members: redis_client, auth_base_limiter, auth_signup_limiter, auth_refresh_token_limiter, auth_confirm_email_limiter, auth_request_email_limiter, auth_reset_password_limiter, contacts_base_limiter, users_base_limiter, user_update_avatar_limiter


REST API schemas Auth
=========================
.. automodule:: src.schemas.auth
  :members:
  :undoc-members:
  :show-inheritance:
  :exclude-members: model_config


REST API schemas Users
==========================
.. automodule:: src.schemas.users
  :members:
  :undoc-members:
  :show-inheritance:
  :exclude-members: model_config


REST API schemas Contacts
=============================
.. automodule:: src.schemas.contacts
  :members:
  :undoc-members:
  :show-inheritance:
  :exclude-members: model_config


Indices and tables
==================

* :ref:`genindex`
* :ref:`modindex`
* :ref:`search`
