from flask import Blueprint
from app.auth import login_required
from app.controllers.announcement_controller import AnnouncementController
from app.controllers.rolecontroller import RoleController
class AnnouncementRoutes:
    def __init__(self):
        self.bp = Blueprint("announce", __name__)
        self.controller = AnnouncementController()
        self.rolecontroller = RoleController()
    
    def register(self):
        self.bp.route("/announcement", methods=["GET", "POST"])(
            login_required(self.controller.announcement)
        )
        self.bp.route("/announcement/create", methods=["GET", "POST"])(
            login_required(self.controller.announcement_create)
        )
        self.bp.route("/announcement/view/<int:announcement_id>", methods=["GET", "POST"])(
            login_required(self.controller.announcement_view)

        
        )
        self.bp.route("/announcement/delete/<int:announcement_id>", methods=["POST"])(
            self.controller.announcement_delete
        )
        self.bp.route("/announcement/annoucementcategory/<string:category>", methods=["GET", "POST"])(
            login_required(self.controller.annoucement_category)

        )
        return self.bp
