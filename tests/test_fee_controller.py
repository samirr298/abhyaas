import unittest
from unittest.mock import patch, MagicMock
from flask import Flask, Blueprint, session, get_flashed_messages
from app.controllers.fee_controller import FeeController

# Helper: build a tiny Flask app to fake browser requests
def make_test_app():
    app = Flask(__name__)
    app.secret_key = "test-secret-key"

    # Define the dummy routes that url_for() will try to redirect to
    bp = Blueprint("auth", __name__)
    bp.route("/fees", endpoint="fees_management")(lambda: "fees")
    bp.route("/profile", endpoint="profile")(lambda: "profile")
    bp.route("/login", endpoint="login")(lambda: "login") # FIXED: Added login route for the decorator!
    app.register_blueprint(bp)
    return app

class TestFeeController(unittest.TestCase):
    def setUp(self):
        self.app = make_test_app()
        self.controller = FeeController()

    # =====================================================================
    #  TESTING FEES MANAGEMENT (ADMIN VIEW)
    # =====================================================================
    @patch("app.controllers.fee_controller.Users")
    @patch.object(FeeController, "render")
    def test_fees_management_calculates_balances(self, mock_render, mock_users):
        """Proves the controller correctly does math on student fees."""
        mock_render.return_value = "fees_page"
        
        # Fake a student coming from the database
        mock_users.get_all_students.return_value = [{'id': 1, 'name': 'John Doe'}]
        # Fake their invoice (They owe 5000, but only paid 2000)
        mock_users.get_fees_by_student_id.return_value = [
            {'amount': 5000, 'paid_amount': 2000, 'status': 'unpaid', 'due_date': '2026-12-01'}
        ]

        with self.app.test_request_context(method="GET"):
            # FIXED: Properly mock the session so the decorators let us through
            session['user_id'] = 1 
            session['role'] = 'admin'

            result = self.controller.fees_management()

            # The controller should have successfully returned the page
            self.assertEqual(result, "fees_page")
            
            # Check what data it sent to the HTML file
            rendered_students = mock_render.call_args[1]['students']
            john = rendered_students[0]
            
            # THE MATH TEST: Did it correctly see they are unpaid?
            self.assertEqual(john['fee_amount'], 5000)
            self.assertEqual(john['fee_paid_amount'], 2000)
            self.assertEqual(john['fee_status'], 'unpaid')


    # =====================================================================
    #  TESTING RECORDING PAYMENTS (ADMIN ACTION)
    # =====================================================================
    @patch("app.controllers.fee_controller.Users")
    def test_record_payment_success(self, mock_users):
        """Proves that submitting a payment updates the database and flashes success."""
        # Make the fake database return True, meaning payment was saved!
        mock_users.record_payment_on_fee.return_value = True

        # Simulate filling out the HTML form to pay NPR 1000 on fee ID #5
        form_data = {
            "action": "record_payment",
            "fee_id": "5",
            "payment_amount": "1000",
            "student_id": "99"
        }

        with self.app.test_request_context(method="POST", data=form_data):
            session['user_id'] = 1 
            session['role'] = 'admin'
            
            response = self.controller.update_fee_status()
            
            # Check if it told the database to update Fee #5 with 1000
            mock_users.record_payment_on_fee.assert_called_once_with("5", 1000.0)
            
            # Check if it flashed the correct success message
            flashes = get_flashed_messages(with_categories=True)
            self.assertIn(("success", "Collection entry recorded successfully."), flashes)
            self.assertEqual(response.status_code, 302) # Redirects back to page


    # =====================================================================
    #  TESTING BULK INVOICES (ADMIN ACTION)
    # =====================================================================
    @patch("app.controllers.fee_controller.Users")
    def test_bulk_set_fee(self, mock_users):
        """Proves the admin can bulk-assign a new fee to all students."""
        # Provide two fake students
        mock_users.get_all_students.return_value = [{'id': 1}, {'id': 2}]
        mock_users.get_fees_by_student_id.return_value = []
        mock_users.add_student_due.return_value = True

        form_data = {
            "action": "bulk_set_fee",
            "target_group": "all",
            "fee_title": "Library Fee",
            "fee_amount": "500"
        }

        with self.app.test_request_context(method="POST", data=form_data):
            session['user_id'] = 1 
            session['role'] = 'admin'
            
            self.controller.update_fee_status()

            # Prove it looped through and charged BOTH students NPR 500
            self.assertEqual(mock_users.add_student_due.call_count, 2)
            
            flashes = get_flashed_messages(with_categories=True)
            self.assertIn(("success", "Successfully allocated 'Library Fee' to 2 student accounts."), flashes)


    # =====================================================================
    #  TESTING STUDENT DASHBOARD VIEW (STUDENT ROLE)
    # =====================================================================
    @patch("app.controllers.fee_controller.Users")
    @patch.object(FeeController, "render")
    def test_student_fees_calculates_total_balance(self, mock_render, mock_users):
        """Proves a student can see their own fees and the balance is correct."""
        mock_render.return_value = "student_fees_page"
        
        # Student owes 2 separate fees: 5000 (paid 5000) and 3000 (paid 1000)
        mock_users.get_fees_by_student_id.return_value = [
            {'id': 1, 'amount': 5000, 'paid_amount': 5000},
            {'id': 2, 'amount': 3000, 'paid_amount': 1000}
        ]
        mock_users.get_transactions_by_student_id.return_value = []

        with self.app.test_request_context(method="GET"):
            session['role'] = 'student'
            session['user_id'] = 99

            self.controller.student_fees()

            # Catch the variables sent to the student dashboard
            rendered_kwargs = mock_render.call_args[1]
            
            # The total billed should be 8000. Total paid should be 6000. Balance is 2000.
            self.assertEqual(rendered_kwargs['fee_amount'], 8000.0)
            self.assertEqual(rendered_kwargs['fee_paid_amount'], 6000.0)
            self.assertEqual(rendered_kwargs['balance'], 2000.0)
            self.assertEqual(rendered_kwargs['fee_status'], 'UNPAID')

if __name__ == "__main__":
    unittest.main()