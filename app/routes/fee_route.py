from flask import Blueprint


class FeeRoutes:
    def __init__(self):
        self.blueprint = Blueprint('fee', __name__, url_prefix='/fees')

    def register(self):
        from app.controllers.fee_controller import FeeController
        
        fee_controller = FeeController()
        
        # Route to display fees management page
        self.blueprint.route('/management', methods=['GET'])(fee_controller.fees_management)
        
        # Route to update fee status
        self.blueprint.route('/update', methods=['POST'])(fee_controller.update_fee_status)
        
        return self.blueprint
