from app.controllers.base_controller import BaseController
from app.models.message import Messagemodel

class MessageController(BaseController):
    def conversations(self):
        user_id = self.session.get('user_id')
       
        teachers = Messagemodel.get_all_teacher()
        
        

        return self.render('messages/message.html',teachers = teachers)

    def conversation(self, conversation_id):
        return self.render('messages/message.html')
