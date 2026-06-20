- [x] Create fee tables in app/database.py (fees, fee_transactions)
- [x] Call Database.create_fee_tables() from app/__init__.py
- [x] Remove fee columns from users table definition in app/database.py

- [ ] Refactor app/models/user.py fee-related methods to use fees/fee_transactions only (and keep admin filter working)
- [ ] Fix any template / controller code expecting removed columns
- [ ] Run basic import/startup check (python -c)
